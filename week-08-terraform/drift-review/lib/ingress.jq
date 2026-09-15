def issue($kind): {unsafe: 0, public_http: 0, unknown: 0} | .[$kind] = 1;
def none: {unsafe: 0, public_http: 0, unknown: 0};
def integer: type == "number" and floor == .;
def strings: type == "array" and all(.[]; type == "string" and length > 0);
def optional_strings($key): (has($key) | not) or .[$key] == null or (.[$key] | strings);
def modules: ., (.child_modules[]? | modules);
def candidates:
  [(.plan.resource_changes[]?, .plan.resource_drift[]? |
       select(.change.after != null) | {type, provider_name, values: .change.after}),
   (.plan.planned_values.root_module? | select(. != null) | modules | .resources[]? | {type, provider_name, values})] | unique;
def rule($cidrs; $modern):
  . as $r |
  (if $modern then [(.cidr_ipv4 | select(. != null)), (.cidr_ipv6 | select(. != null))]
   else ((.cidr_blocks // []) + (.ipv6_cidr_blocks // [])) end) as $sources |
  (if $modern then
     [if .cidr_ipv4 != null then $cidrs["4:" + (.cidr_ipv4 | tostring)] // "unknown" else empty end,
      if .cidr_ipv6 != null then $cidrs["6:" + (.cidr_ipv6 | tostring)] // "unknown" else empty end]
   else
     [(.cidr_blocks[]? | $cidrs["4:" + tostring] // "unknown"),
      (.ipv6_cidr_blocks[]? | $cidrs["6:" + tostring] // "unknown")]
   end) as $classes |
  (if $modern then .ip_protocol else .protocol end | tostring) as $protocol |
  (if $modern then
     (.referenced_security_group_id != null and (.referenced_security_group_id | type == "string" and length > 0))
   else (.self == true or ((.security_groups // []) | length > 0) or
         (.source_security_group_id != null and (.source_security_group_id | type == "string" and length > 0))) end) as $restricted |
  (if $modern then .prefix_list_id != null else ((.prefix_list_ids // []) | length > 0) end) as $prefix |
  if ($modern and ([$r.cidr_ipv4, $r.cidr_ipv6, $r.referenced_security_group_id, $r.prefix_list_id] | map(select(. != null)) | length) != 1) or
     ($classes | any(. == "unknown")) or
     ($sources | any(type != "string")) or $prefix or
     (($sources | length) == 0 and ($restricted | not)) or
     (["tcp", "6", "udp", "17", "-1", "icmp", "1", "icmpv6", "58"] | index($protocol) | not)
  then issue("unknown")
  elif ($protocol != "-1" and
       ((.from_port | integer) and (.to_port | integer) and
        .from_port >= (if (["icmp", "1", "icmpv6", "58"] | index($protocol)) then -1 else 0 end) and
        .to_port <= (if (["icmp", "1", "icmpv6", "58"] | index($protocol)) then 255 else 65535 end) and
        .from_port <= .to_port | not))
  then issue("unknown")
  elif ($classes | any(. == "public")) then
    if ($protocol == "tcp" or $protocol == "6") and .from_port == .to_port and
       (.from_port == 80 or .from_port == 443)
    then issue("public_http") else issue("unsafe") end
  else none end;
def inspect($cidrs; $modern):
  if type != "object" then issue("unknown")
  elif (optional_strings("cidr_blocks") and optional_strings("ipv6_cidr_blocks") and
        optional_strings("security_groups") and optional_strings("prefix_list_ids") | not)
  then issue("unknown")
  elif (has("self") and .self != null and (.self | type != "boolean")) or
       (has("source_security_group_id") and .source_security_group_id != null and (.source_security_group_id | type != "string")) or
       (has("referenced_security_group_id") and .referenced_security_group_id != null and (.referenced_security_group_id | type != "string"))
  then issue("unknown")
  else rule($cidrs; $modern) end;
. as $input |
[candidates[] |
  if .provider_name != "registry.terraform.io/hashicorp/aws" then issue("unknown")
  elif .type == "aws_security_group" then
    if (.values.ingress | type) != "array" then issue("unknown")
    else .values.ingress[] | inspect($input.cidrs; false) end
  elif .type == "aws_security_group_rule" then
    if .values.type == "ingress" then .values | inspect($input.cidrs; false)
    elif .values.type == "egress" then none else issue("unknown") end
  elif .type == "aws_vpc_security_group_ingress_rule" then .values | inspect($input.cidrs; true)
  else issue("unknown") end] |
reduce .[] as $finding (none; .unsafe += $finding.unsafe | .public_http += $finding.public_http | .unknown += $finding.unknown)
