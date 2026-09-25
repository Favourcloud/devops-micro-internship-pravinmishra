#!/usr/bin/env bash
# Eze Favour — report structured Ansible check-mode events without parsing colorized logs.
set -euo pipefail
umask 077
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
review_python="${DMI_REVIEW_PYTHON:-python3}"
full_name='Eze Favour'
test "$#" -eq 4 && test "$1" = '--config' && test "$3" = '--output'
config_path="$2"
output_path="$4"
playbook_path="$("$review_python" -c 'import json,sys; print(json.load(open(sys.argv[1]))["playbook"])' "$config_path")"
inventory_path="$("$review_python" -c 'import json,sys; print(json.load(open(sys.argv[1]))["inventory"])' "$config_path")"
report_path="$output_path/report.json"
checks=(check_service_restarts_handlers check_firewall_changes check_user_sudo_changes check_package_file_removal)
changed_tasks=()

extract_changed_tasks() {
  "$review_python" - "$report_path" <<'PY'
import json,sys
r=json.load(open(sys.argv[1])); seen=set()
for tasks in list(r['categories'].values())+[r['unmatched_changes']]:
 for task in tasks:
  key=(task['source'],task['name'])
  if key not in seen:
   seen.add(key);print(task['name'].replace('\n',' '))
PY
}

check_tasks_matching_pattern() {
  # The callback classified module/actions, including resolved variables and handlers.
  # Match the exact category rather than guessing risk from free-text terminal output.
  "$review_python" - "$report_path" "$1" <<'PY'
import json,sys
r=json.load(open(sys.argv[1])); tasks=r['categories'][sys.argv[2]]
print(sys.argv[2]+': '+str(len(tasks)))
raise SystemExit(0 if tasks else 1)
PY
}
check_service_restarts_handlers() { check_tasks_matching_pattern service_restarts_handlers; }
check_firewall_changes() { check_tasks_matching_pattern firewall_changes; }
check_user_sudo_changes() { check_tasks_matching_pattern user_sudo_changes; }
check_package_file_removal() { check_tasks_matching_pattern package_file_removal; }

set +e
"$review_python" "$script_dir/review.py" --config "$config_path" --output "$output_path"
script_exit_code=$?
set -e
if test -f "$report_path"; then
  while IFS= read -r task; do changed_tasks+=("$task"); done < <(extract_changed_tasks)
  printf 'Learner: %s\nChanged tasks: %s\n' "$full_name" "${#changed_tasks[@]}"
  for check in "${checks[@]}"; do
    if "$check"; then printf 'Finding requires operator review.\n'; fi
  done
else
  script_exit_code=3
fi
printf 'Captured Exit Code: %s (0 LOW; 2 HOLD; 3 ERROR)\n' "$script_exit_code"
exit "$script_exit_code"
