def text: type == "string" and length > 0;
def obj: type == "object";
def flags: type == "boolean" or (type == "object" and all(.[]; flags)) or (type == "array" and all(.[]; flags));
def actions:
  . == ["no-op"] or . == ["create"] or . == ["read"] or . == ["update"] or
  . == ["delete"] or . == ["delete", "create"] or . == ["create", "delete"];
def change:
  obj and (.actions | actions) and has("before") and has("after") and
  (.after_unknown | flags) and
  (if .actions == ["no-op"] then .before == .after else true end) and
  (if .actions == ["delete"] then .after == null else has("after") end);
def resource_change:
  obj and (.address | text) and (.type | text) and (.provider_name | text) and
  (.mode == "managed" or .mode == "data") and (.change | change) and
  (.change | ((.before == null or (.before | obj)) and (.after == null or (.after | obj)))) and
  (if .change.actions == ["delete"] then (.change.before | obj)
   elif .change.actions == ["create"] or .change.actions == ["read"] then (.change.after | obj)
   else (.change.before | obj) and (.change.after | obj) end);
def resources:
  type == "array" and all(.[];
    obj and (.address | text) and (.type | text) and (.provider_name | text) and
    (.mode == "managed" or .mode == "data") and (.values | obj));
def plan_module:
  obj and ((has("resources") | not) or (.resources | resources)) and
  ((has("child_modules") | not) or (.child_modules | type == "array" and all(.[]; plan_module)));
def root($plan):
  obj and (.format_version == "1.0" or .format_version == "1.1" or .format_version == "1.2") and
  (.terraform_version | text) and (.planned_values | obj) and
  ((.planned_values | has("root_module") | not) or (.planned_values.root_module | plan_module)) and
  ((.planned_values | has("outputs") | not) or (.planned_values.outputs | obj and all(.[]; obj and (.sensitive | type == "boolean")))) and
  (all(["resource_changes", "resource_drift"][]; . as $key | $plan |
    (has($key) | not) or (.[$key] | type == "array" and all(.[]; resource_change)))) and
  ((has("output_changes") | not) or (.output_changes | obj and all(.[]; change))) and
  ((has("errored") | not) or .errored == false) and
  ((has("complete") | not) or (.complete | type == "boolean")) and
  ((has("applyable") | not) or (.applyable | type == "boolean")) and
  ((has("deferred_changes") | not) or (.deferred_changes | type == "array")) and
  ((has("checks") | not) or (.checks | type == "array" and all(.[]; obj and (.status == "pass" or .status == "fail" or .status == "unknown" or .status == "error")))) and
  ((has("proposed_unknown") | not) or (.proposed_unknown | obj));
. as $plan | root($plan)
