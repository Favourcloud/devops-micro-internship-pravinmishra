#!/bin/bash
set -Eeuo pipefail
umask 022

readonly APP_COMMIT=f1b1aff14fe15c5bde092067c93a307fa3d97982
readonly APP_LOCK_SHA256=287a9d37c611438b6c4ed0979fbf45128bda5dc3ff5175683c74941ba0440257
readonly APP_REPOSITORY=https://github.com/pravinmishraaws/my-react-app.git
readonly NODE_VERSION=22.23.2
readonly NODE_SHA256=d60acfe00a2932254bb0ad20e01b0d74397a0875595de719654b214f4b03f307
readonly BUILD_USER=dmi-react-build
APP_DIR=/opt/dmi-react/source
NODE_DIR=/opt/dmi-react/node
BUILD_HOME=/var/lib/dmi-react-build
WEB_ROOT=/var/www/dmi-react
NGINX_CONFIG=/etc/nginx/sites-available/default
NGINX_ENABLED=/etc/nginx/sites-enabled/default
READY_DIR=/var/lib/dmi-react
READY_FILE=$READY_DIR/deployment-ready
WORK_DIR=
STAGE=preflight

fail() {
  local status=$1 line=$2
  rm -f -- "$READY_FILE" "$READY_FILE.tmp"
  printf 'React bootstrap failed: stage=%s line=%s exit=%s; no readiness claimed.\n' "$STAGE" "$line" "$status" >&2
  exit "$status"
}

cleanup() {
  if [[ -n "$WORK_DIR" && -d "$WORK_DIR" ]]; then
    rm -rf -- "$WORK_DIR"
  fi
}

retry() {
  local attempt status=1
  for attempt in 1 2 3; do
    if "$@"; then
      return 0
    else
      status=$?
    fi
    if [[ "$attempt" -lt 3 ]]; then sleep 10; fi
  done
  return "$status"
}

as_builder() {
  runuser -u "$BUILD_USER" -- env -i \
    HOME="$BUILD_HOME" PATH="$NODE_DIR/bin:/usr/bin:/bin" \
    GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null \
    GIT_TERMINAL_PROMPT=0 GIT_ALLOW_PROTOCOL=https \
    NPM_CONFIG_USERCONFIG="$BUILD_HOME/empty-user.npmrc" NPM_CONFIG_GLOBALCONFIG="$BUILD_HOME/empty-global.npmrc" \
    NPM_CONFIG_CACHE="$BUILD_HOME/npm-cache" \
    NPM_CONFIG_REGISTRY=https://registry.npmjs.org/ \
    NPM_CONFIG_UPDATE_NOTIFIER=false "$@"
}

install_packages() {
  export DEBIAN_FRONTEND=noninteractive
  retry timeout --kill-after=10s 300s apt-get -o Acquire::Retries=3 -o DPkg::Lock::Timeout=120 -o APT::Update::Error-Mode=any update
  retry timeout --kill-after=10s 600s apt-get -o Acquire::Retries=3 -o DPkg::Lock::Timeout=120 install -y --no-install-recommends ca-certificates curl git nginx xz-utils
}

install_node() {
  local archive="node-v${NODE_VERSION}-linux-x64.tar.xz" actual_version
  retry curl -q --proto '=https' --tlsv1.2 --fail --silent --show-error \
    --connect-timeout 15 --max-time 180 \
    "https://nodejs.org/dist/v${NODE_VERSION}/${archive}" -o "$WORK_DIR/$archive"
  printf '%s  %s\n' "$NODE_SHA256" "$WORK_DIR/$archive" | sha256sum --check --status
  install -d -m 0755 "$NODE_DIR"
  tar -xJf "$WORK_DIR/$archive" --strip-components=1 -C "$NODE_DIR"
  actual_version=$("$NODE_DIR/bin/node" --version)
  [[ "$actual_version" == "v$NODE_VERSION" ]] || return 1
}

prepare_source() {
  local remote commit
  if ! id "$BUILD_USER" >/dev/null 2>&1; then
    useradd --system --user-group --home-dir "$BUILD_HOME" --shell /usr/sbin/nologin "$BUILD_USER"
  fi
  install -d -m 0700 -o "$BUILD_USER" -g "$BUILD_USER" "$BUILD_HOME" "$APP_DIR"
  as_builder git -C "$APP_DIR" init --quiet
  if ! as_builder git -C "$APP_DIR" remote get-url origin >/dev/null 2>&1; then
    as_builder git -C "$APP_DIR" remote add origin "$APP_REPOSITORY"
  fi
  remote=$(as_builder git -C "$APP_DIR" remote get-url origin)
  [[ "$remote" == "$APP_REPOSITORY" ]] || return 1
  retry timeout --kill-after=10s 180s runuser -u "$BUILD_USER" -- env -i \
    HOME="$BUILD_HOME" PATH=/usr/bin:/bin GIT_CONFIG_NOSYSTEM=1 \
    GIT_CONFIG_GLOBAL=/dev/null GIT_TERMINAL_PROMPT=0 GIT_ALLOW_PROTOCOL=https \
    git -C "$APP_DIR" fetch --quiet --depth=1 origin "$APP_COMMIT"
  as_builder git -C "$APP_DIR" checkout --quiet --detach "$APP_COMMIT"
  commit=$(as_builder git -C "$APP_DIR" rev-parse HEAD)
  [[ "$commit" == "$APP_COMMIT" ]] || return 1
  printf '%s  %s\n' "$APP_LOCK_SHA256" "$APP_DIR/package-lock.json" | sha256sum --check --status
}

build_app() {
  local links changes
  cd "$APP_DIR"
  # Locked dependencies, no lifecycle hooks; the explicit production build is unprivileged.
  retry as_builder timeout --kill-after=10s 600s npm ci --ignore-scripts --no-audit --no-fund --fetch-timeout=60000 --fetch-retries=2
  as_builder timeout --kill-after=10s 600s npm run build
  [[ -s build/index.html && -d build/static ]] || return 1
  links=$(find build -type l -print -quit)
  [[ -z "$links" ]] || return 1
  changes=$(as_builder git status --porcelain --untracked-files=no)
  [[ -z "$changes" ]] || return 1
}

configure_nginx() {
  install -d -m 0755 "$WEB_ROOT"
  cp -R "$APP_DIR/build/." "$WEB_ROOT/"
  chown -R root:root "$WEB_ROOT"
  find "$WEB_ROOT" -type d -exec chmod 0755 {} +
  find "$WEB_ROOT" -type f -exec chmod 0644 {} +
  cat > "$NGINX_CONFIG" <<NGINX
server {
    listen 80 default_server;
    server_name _;
    root $WEB_ROOT;
    index index.html;
    server_tokens off;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /static/ {
        try_files \$uri =404;
    }
}
NGINX
  ln -sfn "$NGINX_CONFIG" "$NGINX_ENABLED"
  nginx -t
  timeout --kill-after=10s 60s systemctl enable nginx
  timeout --kill-after=10s 60s systemctl restart nginx
  systemctl is-active --quiet nginx
}

check_ready() {
  local route asset
  for route in / /assignment-spa-probe; do
    retry curl -q --noproxy '*' --fail --silent --show-error \
      --connect-timeout 3 --max-time 10 "http://127.0.0.1$route" -o "$WORK_DIR/response"
    cmp -s "$APP_DIR/build/index.html" "$WORK_DIR/response"
  done
  asset=$(find "$WEB_ROOT/static" -type f -name '*.js' -print -quit)
  [[ -n "$asset" && -s "$asset" ]] || return 1
  retry curl -q --noproxy '*' --fail --silent --show-error \
    --connect-timeout 3 --max-time 10 "http://127.0.0.1${asset#"$WEB_ROOT"}" -o "$WORK_DIR/response"
  cmp -s "$asset" "$WORK_DIR/response"
  printf 'status=ready\nupstream_commit=%s\nnode_version=%s\nlock_sha256=%s\nchecked_at=%s\n' \
    "$APP_COMMIT" "$NODE_VERSION" "$APP_LOCK_SHA256" "$(date -u +%FT%TZ)" > "$READY_FILE.tmp"
  chmod 0644 "$READY_FILE.tmp"
  mv -f "$READY_FILE.tmp" "$READY_FILE"
  printf 'React bootstrap ready; commit=%s; local HTTP and SPA checks passed.\n' "$APP_COMMIT"
}

main() {
  [[ "$(id -u)" == 0 ]] || return 1
  trap 'fail "$?" "$LINENO"' ERR
  trap cleanup EXIT
  install -d -m 0755 "$READY_DIR"
  rm -f -- "$READY_FILE" "$READY_FILE.tmp"
  [[ "$(uname -m)" == x86_64 ]] || return 1
  WORK_DIR=$(mktemp -d /tmp/dmi-react.XXXXXXXX)
  STAGE=packages
  install_packages
  STAGE=node
  install_node
  STAGE=source
  prepare_source
  STAGE=build
  build_app
  STAGE=nginx
  configure_nginx
  STAGE=readiness
  check_ready
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main
fi
