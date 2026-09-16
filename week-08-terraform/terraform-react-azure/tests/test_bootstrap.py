"""Shell orchestration tests with stubs: never an Ubuntu, Nginx or cloud deployment."""

from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r'''
source "$1"
TEST_ROOT=$2
APP_DIR=$TEST_ROOT/source
NODE_DIR=$TEST_ROOT/node
BUILD_HOME=$TEST_ROOT/home
WEB_ROOT=$TEST_ROOT/www
NGINX_CONFIG=$TEST_ROOT/nginx.conf
NGINX_ENABLED=$TEST_ROOT/nginx-enabled
READY_DIR=$TEST_ROOT/ready
READY_FILE=$READY_DIR/deployment-ready
WORK_DIR=$TEST_ROOT/work
mkdir -p "$APP_DIR/build/static/js" "$BUILD_HOME" "$WEB_ROOT" "$READY_DIR" "$WORK_DIR"
printf 'STUB HTML: not a React build\n' > "$APP_DIR/build/index.html"
printf 'STUB STATIC BYTES\n' > "$APP_DIR/build/static/js/main.js"
log() { printf '%s\n' "$*" >> "$TEST_ROOT/calls"; }
sleep() { :; }
chown() { :; }
timeout() { shift 2; "$@"; }
nginx() { log "nginx $*"; }
systemctl() { log "systemctl $*"; }
curl() {
  local output= url=
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o) output=$2; shift ;;
      http://*) url=$1 ;;
    esac
    shift
  done
  log "curl $url"
  if [[ "$url" == */static/* ]]; then
    cp "$APP_DIR/build/static/js/main.js" "$output"
  else
    cp "$APP_DIR/build/index.html" "$output"
  fi
}
'''
MAIN_STUBS = r'''
id() { if [[ "$1" == -u ]]; then printf '0\n'; else return 1; fi; }
uname() { printf 'x86_64\n'; }
install_packages() { log packages; }
install_node() { log node; }
prepare_source() { log source; }
build_app() { log build; }
'''


class BootstrapTests(unittest.TestCase):
    def run_shell(self, body, *, main_stubs=False, code=0):
        with tempfile.TemporaryDirectory(prefix='dmi-a3-stub-') as temporary:
            command = HARNESS + (MAIN_STUBS if main_stubs else '') + '\n' + body
            result = subprocess.run(['/bin/bash', '--noprofile', '--norc', '-c', command, 'stub-test', str(ROOT / 'cloud-init.sh'), temporary],
                                    env={'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': temporary}, text=True, capture_output=True, timeout=20)
            path = Path(temporary)
            calls = (path / 'calls').read_text().splitlines() if (path / 'calls').exists() else []
            ready = (path / 'ready/deployment-ready').read_text() if (path / 'ready/deployment-ready').exists() else None
            config = (path / 'nginx.conf').read_text() if (path / 'nginx.conf').exists() else ''
            self.assertEqual(result.returncode, code, result.stdout + result.stderr)
            return calls, ready, config, result.stdout + result.stderr

    def test_success_orchestration_requires_all_health_checks(self):
        calls, ready, config, _ = self.run_shell('main', main_stubs=True)
        self.assertEqual(calls[:4], ['packages', 'node', 'source', 'build'])
        self.assertIn('nginx -t', calls)
        self.assertIn('systemctl is-active --quiet nginx', calls)
        self.assertEqual(len([c for c in calls if c.startswith('curl ')]), 3)
        self.assertIn('status=ready', ready)
        self.assertIn('upstream_commit=f1b1aff14fe15c5bde092067c93a307fa3d97982', ready)
        self.assertIn('try_files $uri $uri/ /index.html;', config)
        self.assertIn('try_files $uri =404;', config)

    def test_each_failed_stage_removes_marker_and_stops(self):
        stages = ['install_packages', 'install_node', 'prepare_source', 'build_app', 'configure_nginx', 'check_ready']
        for index, stage in enumerate(stages):
            with self.subTest(stage=stage):
                calls, ready, _, output = self.run_shell(f'printf stale > "$READY_FILE"\n{stage}() {{ log FAIL; return 42; }}\nmain', main_stubs=True, code=42)
                self.assertIsNone(ready)
                self.assertEqual(calls.count('FAIL'), 1)
                self.assertEqual(calls[-1], 'FAIL')
                self.assertIn('no readiness claimed', output)

    def test_architecture_failure_prevents_package_install(self):
        calls, ready, _, _ = self.run_shell('uname() { printf "aarch64\\n"; }; main', main_stubs=True, code=1)
        self.assertEqual(calls, [])
        self.assertIsNone(ready)

    def test_retry_success_is_bounded(self):
        calls, _, _, _ = self.run_shell('tries=0; flaky() { tries=$((tries+1)); log attempt; [[ "$tries" == 3 ]]; }; retry flaky')
        self.assertEqual(calls, ['attempt'] * 3)

    def test_retry_exhaustion_preserves_failure(self):
        calls, _, _, _ = self.run_shell('never() { log attempt; return 47; }; retry never', code=47)
        self.assertEqual(calls, ['attempt'] * 3)

    def test_package_failure_does_not_continue(self):
        calls, ready, _, _ = self.run_shell('apt-get() { log "$*"; return 43; }; install_packages', code=43)
        self.assertEqual(len(calls), 3)
        self.assertTrue(all('update' in c and 'install -y' not in c for c in calls))
        self.assertIsNone(ready)

    def test_checksum_failure_prevents_extraction(self):
        calls, ready, _, _ = self.run_shell('curl() { log download; }; sha256sum() { log checksum; return 44; }; tar() { log UNEXPECTED; }; install_node', code=44)
        self.assertEqual(calls, ['download', 'checksum'])
        self.assertIsNone(ready)

    def test_dependency_failure_prevents_build(self):
        calls, _, _, _ = self.run_shell('as_builder() { log "$*"; return 45; }; build_app', code=45)
        self.assertEqual(len(calls), 3)
        self.assertTrue(all('npm ci --ignore-scripts' in c for c in calls))
        self.assertFalse(any('npm run build' in c for c in calls))

    def test_build_failure_is_not_ready(self):
        calls, ready, _, _ = self.run_shell('as_builder() { log "$*"; if [[ "$*" == *"npm run build"* ]]; then return 46; fi; }; build_app', code=46)
        self.assertEqual(len(calls), 2)
        self.assertIsNone(ready)

    def test_missing_build_output_fails(self):
        _, ready, _, _ = self.run_shell('as_builder() { :; }; rm "$APP_DIR/build/index.html"; build_app', code=1)
        self.assertIsNone(ready)

    def test_symlinked_build_output_fails(self):
        _, ready, _, _ = self.run_shell('as_builder() { :; }; ln -s /etc/passwd "$APP_DIR/build/unsafe"; build_app', code=1)
        self.assertIsNone(ready)

    def test_upstream_source_mutation_fails(self):
        _, ready, _, _ = self.run_shell('as_builder() { if [[ "$1" == git ]]; then printf "modified source\\n"; fi; }; build_app', code=1)
        self.assertIsNone(ready)

    def test_source_integrity_command_failure_is_not_empty_success(self):
        _, ready, _, _ = self.run_shell('as_builder() { if [[ "$1" == git ]]; then return 51; fi; }; build_app', code=51)
        self.assertIsNone(ready)

    def test_build_output_inspection_failure_is_not_empty_success(self):
        _, ready, _, _ = self.run_shell('as_builder() { :; }; find() { return 52; }; build_app', code=52)
        self.assertIsNone(ready)

    def test_builder_environment_drops_inherited_configuration(self):
        self.run_shell('export AMBIENT_CREDENTIAL=fake; runuser() { shift 3; "$@"; }; as_builder /bin/sh -c \'test -z "$AMBIENT_CREDENTIAL" && test "$GIT_TERMINAL_PROMPT" = 0 && test "$NPM_CONFIG_USERCONFIG" != "$NPM_CONFIG_GLOBALCONFIG"\'')

    def test_nginx_validation_failure_prevents_activation(self):
        calls, ready, _, _ = self.run_shell('nginx() { log invalid-nginx; return 48; }; configure_nginx', code=48)
        self.assertEqual(calls, ['invalid-nginx'])
        self.assertIsNone(ready)

    def test_nginx_activation_failure_prevents_readiness(self):
        calls, ready, _, _ = self.run_shell('systemctl() { log "$*"; return 49; }; main', main_stubs=True, code=49)
        self.assertIsNone(ready)
        self.assertFalse(any(c.startswith('curl ') for c in calls))

    def test_http_failure_does_not_create_marker(self):
        calls, ready, _, _ = self.run_shell('curl() { log bad-http; return 50; }; main', main_stubs=True, code=50)
        self.assertEqual(calls.count('bad-http'), 3)
        self.assertIsNone(ready)

    def test_wrong_http_content_does_not_create_marker(self):
        _, ready, _, _ = self.run_shell('curl() { while [[ "$1" != -o ]]; do shift; done; printf wrong > "$2"; }; main', main_stubs=True, code=1)
        self.assertIsNone(ready)

    def test_wrong_static_asset_does_not_create_marker(self):
        body = r'''curl() {
          local output= url=
          while [[ $# -gt 0 ]]; do
            case "$1" in -o) output=$2; shift ;; http://*) url=$1 ;; esac
            shift
          done
          if [[ "$url" == */static/* ]]; then printf wrong > "$output";
          else cp "$APP_DIR/build/index.html" "$output"; fi
        }; main'''
        _, ready, _, _ = self.run_shell(body, main_stubs=True, code=1)
        self.assertIsNone(ready)

    def test_missing_static_asset_does_not_create_marker(self):
        _, ready, _, _ = self.run_shell('rm "$APP_DIR/build/static/js/main.js"; main', main_stubs=True, code=1)
        self.assertIsNone(ready)


if __name__ == '__main__':
    unittest.main()
