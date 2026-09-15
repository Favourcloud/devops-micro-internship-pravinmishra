#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

student_name='Eze Favour'
checks=(check_destructive_actions check_open_ingress)
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
helper="$project_dir/lib/evidence.py"
mode='' fixture='' terraform_dir='' report='' authorized=false
workspace='' source_hash='unavailable' plan_exit='not run'
status=ERROR detail='Evidence gathering or validation failed; no approval.'
deletes=0 unsafe=0 public_http=0 unknown=0 changes=0 outputs=0 drift=0
result=3

fail() { printf '%s\n' 'FAIL: review could not complete; no safety approval.' >&2; exit 3; }
usage() {
  printf '%s\n' 'Usage: tf-drift-check.sh --fixture JSON --report NEW_PATH' \
    '   or: tf-drift-check.sh --live --terraform-dir TRUSTED_DIR --authorize-live-read-only --report NEW_PATH' >&2
  exit 3
}
while (($#)); do
  case "$1" in
    --fixture) [[ $# -ge 2 && -z "$mode" ]] || usage; mode=FIXTURE; fixture=$2; shift 2 ;;
    --live) [[ -z "$mode" ]] || usage; mode=LIVE; shift ;;
    --terraform-dir) [[ $# -ge 2 && -z "$terraform_dir" ]] || usage; terraform_dir=$2; shift 2 ;;
    --authorize-live-read-only) [[ "$authorized" == false ]] || usage; authorized=true; shift ;;
    --report) [[ $# -ge 2 && -z "$report" ]] || usage; report=$2; shift 2 ;;
    *) usage ;;
  esac
done
[[ -n "$mode" && -n "$report" ]] || usage
[[ "$mode" != FIXTURE || ( -z "$terraform_dir" && "$authorized" == false ) ]] || usage
[[ "$mode" != LIVE || ( -n "$terraform_dir" && "$authorized" == true ) ]] || usage
for tool in python3.13 dirname; do command -v "$tool" >/dev/null 2>&1 || fail; done
python_bin="$(command -v python3.13)"
workspace="$("$python_bin" "$helper" init "$report")" || fail
finish() {
  local prior=$?
  trap - EXIT HUP INT TERM
  if [[ $prior -ne 0 ]]; then status=ERROR; result=3; detail='Evidence gathering or validation failed; no approval.'; fi
  if ! "$python_bin" "$helper" publish "$workspace" "$report" "$mode" "$status" "$detail" "$source_hash" "$plan_exit" \
      "$deletes" "$unsafe" "$public_http" "$unknown" "$changes" "$outputs" "$drift"; then result=3; fi
  "$python_bin" "$helper" cleanup "$workspace" || result=3
  exit "$result"
}
trap finish EXIT
trap 'exit 3' HUP INT TERM
command -v jq >/dev/null 2>&1 || fail
jq_bin="$(command -v jq)"
[[ -x "$jq_bin" && -f "$jq_bin" ]] || fail
if [[ "$mode" == FIXTURE ]]; then
  "$python_bin" "$helper" copy "$fixture" "$workspace/plan.json" || fail
else
  # A trusted initialized project, provider binaries, environment, and explicit
  # human authorization are prerequisites. Plan can execute data-source code.
  [[ -d "$terraform_dir" ]] || fail
  [[ -z "${TF_CLI_ARGS:-}" && -z "${TF_CLI_ARGS_plan:-}" && -z "${TF_CLI_ARGS_show:-}" ]] || fail
  command -v terraform >/dev/null 2>&1 || fail
  terraform_bin="$(command -v terraform)"
  [[ -f "$terraform_bin" && -x "$terraform_bin" && "$terraform_bin" == /* ]] || fail
  unset TF_LOG TF_LOG_PATH TF_LOG_CORE TF_LOG_PROVIDER
  set +e
  (cd -- "$terraform_dir" && "$terraform_bin" plan -input=false -no-color -detailed-exitcode "-out=$workspace/plan.binary") \
    >"$workspace/plan.stdout.log" 2>"$workspace/plan.stderr.log"
  plan_exit=$?
  set -e
  case "$plan_exit" in 0|2) ;; *) fail ;; esac
  [[ -s "$workspace/plan.binary" && -f "$workspace/plan.binary" && ! -L "$workspace/plan.binary" ]] || fail
  (cd -- "$terraform_dir" && "$terraform_bin" show -json "$workspace/plan.binary") \
    >"$workspace/plan.json" 2>"$workspace/show.stderr.log" || fail
fi
source_hash="$("$python_bin" "$helper" prepare "$workspace/plan.json" "$workspace")" || fail
"$jq_bin" -e -f "$project_dir/lib/schema.jq" "$workspace/plan.json" >"$workspace/schema.log" 2>&1 || fail

check_destructive_actions() {
  deletes="$("$jq_bin" '[.resource_changes[]?, .resource_drift[]? | select(.change.actions | index("delete"))] | length' "$workspace/plan.json")" || fail
}
check_open_ingress() {
  "$jq_bin" -c -f "$project_dir/lib/ingress.jq" "$workspace/policy-input.json" >"$workspace/ingress.json" 2>"$workspace/ingress.log" || fail
  unsafe="$("$jq_bin" -er '.unsafe' "$workspace/ingress.json")" || fail
  public_http="$("$jq_bin" -er '.public_http' "$workspace/ingress.json")" || fail
  unknown="$("$jq_bin" -er '.unknown' "$workspace/ingress.json")" || fail
}
for check in "${checks[@]}"; do "$check"; done
changes="$("$jq_bin" '[.resource_changes[]? | select(.change.actions != ["no-op"])] | length' "$workspace/plan.json")" || fail
outputs="$("$jq_bin" '[.output_changes[]? | select(.actions != ["no-op"])] | length' "$workspace/plan.json")" || fail
drift="$("$jq_bin" '(.resource_drift // []) | length' "$workspace/plan.json")" || fail
uncertain="$("$jq_bin" '[
  (.resource_changes[]?, .resource_drift[]? | .change.after_unknown | .. | select(. == true)),
  (.output_changes[]? | .after_unknown | .. | select(. == true)),
  (.proposed_unknown? | .. | select(. == true)),
  (.planned_values.outputs[]? | select(has("value") | not)),
  (.deferred_changes[]?), (select(.complete == false)),
  (.checks[]? | select(.status != "pass"))] | length' "$workspace/plan.json")" || fail
unknown=$((unknown + uncertain))
if [[ "$mode" == LIVE ]]; then
  if [[ "$plan_exit" == 0 && $((changes + outputs + drift)) -ne 0 ]]; then fail; fi
  if [[ "$plan_exit" == 2 && $((changes + outputs + drift + unknown)) -eq 0 ]]; then fail; fi
fi
if (( deletes > 0 || unsafe > 0 )); then
  status=FAIL; result=2; detail='Destructive actions or unsafe public ingress detected; human review required.'
elif (( changes > 0 || outputs > 0 || drift > 0 || unknown > 0 || public_http > 0 )); then
  status=WARN; result=1; detail='Changes, intentional web ingress, or incomplete policy coverage require human review.'
else
  status=HEALTHY; result=0; detail='No pending changes or policy findings in the supported evidence scope.'
fi
exit 0
