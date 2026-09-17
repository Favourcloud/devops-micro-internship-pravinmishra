#!/usr/bin/python3
"""Copilot-authored draft; an allowlist hook, not an operating-system sandbox."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_COMMAND = "/usr/bin/python3 -I scripts/validate_offline.py"
MANIFEST = ".claude/trusted-files.json"
PROTECTED = frozenset({
    "CLAUDE.md", ".claude/settings.json.example", ".mcp.json.example",
    ".claude/agents/terraform-engineer.md",
    ".claude/agents/architecture-security-reviewer.md",
    "hooks/pre_tool_guard.py", "hooks/post_tool_validate.py",
    "scripts/validate_offline.py",
})
MCP_TOOLS = frozenset("mcp__terraform__" + name for name in (
    "search_providers", "get_provider_details", "get_latest_provider_version",
    "get_provider_capabilities", "search_modules", "get_module_details",
    "get_latest_module_version",
))
AGENTS = frozenset({"terraform-engineer", "architecture-security-reviewer"})
SUFFIXES = frozenset({".tf", ".hcl", ".md", ".json", ".py", ".sh", ".tpl",
                      ".tftpl", ".template", ".conf", ".service", ".timer", ".txt", ".yaml", ".yml"})
TOP_FIELDS = frozenset({"session_id", "transcript_path", "cwd", "permission_mode",
                        "hook_event_name", "tool_name", "tool_input", "tool_use_id",
                        "agent_id", "agent_type"})


class Denied(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Denied(reason)


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    def invalid(_):
        raise Denied("Non-finite JSON number")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def plain(value, maximum=8192):
    require(isinstance(value, str) and 0 < len(value) <= maximum, "Invalid string")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in value), "Control character")
    return value


def canonical(value, root=ROOT, exists=True):
    plain(value)
    path = Path(value)
    require(".." not in path.parts and "~" not in path.parts, "Noncanonical path")
    path = path if path.is_absolute() else root / path
    try:
        relative = path.relative_to(root)
    except ValueError:
        raise Denied("Path outside project") from None
    current = root
    require(not root.is_symlink() and root.resolve() == root, "Noncanonical project")
    for part in relative.parts:
        current = current / part
        require(not current.is_symlink(), "Symlink denied")
        if current.exists():
            mode = current.lstat().st_mode
            require(stat.S_ISDIR(mode) or stat.S_ISREG(mode), "Special file denied")
            require(not stat.S_ISREG(mode) or current.stat().st_nlink == 1, "Hardlink denied")
    require(not exists or path.exists(), "Missing path")
    require(path.resolve().is_relative_to(root), "Path escape")
    return path


def private(relative):
    for index, part in enumerate(relative.parts):
        low = part.lower()
        if low.startswith(".") and part not in {".claude", ".terraform.lock.hcl", ".mcp.json.example", ".gitignore"}:
            return True
        if (low in {"credentials", "node_modules", "__pycache__", "override.tf", "override.tf.json"}
                or (low == "secrets" and relative.parts[:index + 1] != ("terraform", "modules", "secrets"))
                or ".tfstate" in low or ".tfplan" in low
                or low.endswith((".pem", ".key", ".p12", ".plan"))
                or (".tfvars" in low and not low.endswith(".tfvars.example"))
                or low.endswith(("_override.tf", "_override.tf.json"))):
            return True
    return False


def readable(path, root=ROOT):
    rel = path.relative_to(root)
    require(not private(rel), "Private/artifact path denied")
    if path.is_file():
        require(path.suffix in SUFFIXES or path.name in {".gitignore", ".mcp.json.example", "terraform.tfvars.example", "settings.json.example"},
                "Unsupported file type")


def safe_tree(path, root=ROOT):
    readable(path, root)
    if path.is_dir():
        count = 0
        for base, dirs, files in os.walk(path, followlinks=False):
            for name in dirs + files:
                count += 1
                require(count <= 4096, "Search tree too large")
                candidate = canonical(str(Path(base) / name), root)
                readable(candidate, root)


def writable(value, root=ROOT):
    path = canonical(value, root, exists=False)
    rel = path.relative_to(root)
    readable(path, root)
    require(rel.as_posix() not in PROTECTED and rel.as_posix() not in {
        MANIFEST, "source-lock.json", "terraform/.terraform.lock.hcl", "runtime/deploy-manifest.json", ".gitignore",
    }, "Protected trust input")
    require(rel.parts and rel.parts[0] not in {"hooks", ".claude", "tests"}, "Protected policy/test directory")
    require(not path.name.endswith(".tftest.hcl"), "Protected Terraform test")
    allowed = (
        rel == Path("README.md")
        or (rel.parts[0] == "terraform" and "tests" not in rel.parts and path.suffix == ".tf")
        or (rel.parts[0] == "runtime" and path.suffix in SUFFIXES - {".json", ".hcl", ".tf"})
        or rel == Path("scripts/verify_upstream.py")
    )
    require(allowed, "Write outside editable source allowlist")
    require(not path.exists() or path.is_file(), "Not a regular source file")
    return path


def trust(root=ROOT, validation=False):
    manifest = canonical(MANIFEST, root)
    data = strict_json(manifest.read_text(encoding="utf-8"))
    require(isinstance(data, dict) and set(data) == {"version", "files", "terraform_tests"}
            and data["version"] == 1, "Invalid trust manifest")
    files, tests = data["files"], data["terraform_tests"]
    require(isinstance(files, dict) and isinstance(tests, dict), "Invalid trust maps")
    require(PROTECTED <= files.keys(), "Incomplete policy manifest")
    require(not (files.keys() & tests.keys()), "Overlapping trust maps")
    if validation:
        require({"source-lock.json", "terraform/.terraform.lock.hcl"} <= files.keys(), "Source/lock trust not sealed")
        require(bool(tests), "Mock test trust not sealed")
    for name, digest in {**files, **tests}.items():
        require(isinstance(name, str) and isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), "Invalid digest")
        if name in tests:
            require(re.fullmatch(r"terraform/tests/[a-z0-9_]+\.tftest\.hcl", name), "Invalid test manifest path")
        target = canonical(name, root)
        require(target.is_file() and target.stat().st_size <= 2 * 1024 * 1024, "Invalid trusted file")
        require(hashlib.sha256(target.read_bytes()).hexdigest() == digest, "Trusted file changed; human review required")
    return data


def fields(data, allowed, required=()):
    require(isinstance(data, dict) and set(data) <= set(allowed) and set(required) <= data.keys(), "Unsupported or missing tool fields")


def glob_pattern(value):
    plain(value, 1024)
    require(not value.startswith(("/", "~")) and ".." not in value.split("/")
            and re.fullmatch(r"[A-Za-z0-9_.*?/\[\]{}!, -]+", value), "Unsafe glob")
    require(not any(p.startswith(".") for p in value.split("/")), "Hidden glob denied")


def registry_arguments(tool, args):
    # Parameter names verified against pkg/tools/registry at official v1.3.0.
    schemas = {
        "search_providers": ({"provider_name", "provider_namespace", "service_slug", "provider_document_type"}, {"provider_version"}),
        "get_provider_details": ({"provider_doc_id"}, set()),
        "get_latest_provider_version": ({"namespace", "name"}, set()),
        "get_provider_capabilities": ({"namespace", "name"}, {"version"}),
        "search_modules": ({"module_query"}, {"current_offset"}),
        "get_module_details": ({"module_id"}, set()),
        "get_latest_module_version": ({"module_publisher", "module_name", "module_provider"}, set()),
    }
    required, optional = schemas[tool.removeprefix("mcp__terraform__")]
    fields(args, required | optional, required)
    for key, value in args.items():
        if key == "current_offset":
            require(type(value) is int and 0 <= value <= 10000, "Invalid pagination")
            continue
        plain(value, 256)
        if key in {"version", "provider_version"}:
            require(value == "latest" or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value), "Invalid registry version")
        elif key == "provider_doc_id":
            require(re.fullmatch(r"[0-9]{1,20}", value), "Invalid provider document ID")
        elif key == "provider_document_type":
            require(value in {"overview", "guides", "resources", "data-sources", "functions", "actions", "list-resources"}, "Invalid document category")
        elif key == "module_id":
            require(re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/[0-9]+\.[0-9]+\.[0-9]+", value), "Invalid public module ID")
        elif key == "module_query":
            require(re.fullmatch(r"[A-Za-z0-9_ /-]+", value), "Invalid public module query")
        else:
            require(re.fullmatch(r"[A-Za-z0-9_-]+", value), "Invalid public registry identifier")


def decide(event, root=ROOT, expected_event="PreToolUse"):
    fields(event, TOP_FIELDS | ({"tool_response"} if expected_event == "PostToolUse" else set()),
           {"hook_event_name", "cwd", "tool_name", "tool_input"})
    require(event["hook_event_name"] == expected_event, "Unexpected event")
    for name in TOP_FIELDS - {"tool_input"}:
        if name in event:
            plain(event[name])
    require(canonical(event["cwd"], root) == root, "Start Claude in this project root")
    if "permission_mode" in event:
        require(event["permission_mode"] in {"default", "plan", "acceptEdits"}, "Unsupported permission mode")
    agent = event.get("agent_type")
    require(agent is None or agent in AGENTS, "Unknown agent identity")
    require("agent_id" not in event or agent in AGENTS, "Missing agent type")
    trust(root)
    tool, args = event["tool_name"], event["tool_input"]
    require(isinstance(args, dict), "Invalid tool input")
    if tool == "Bash":
        fields(args, {"command", "description", "timeout"}, {"command"})
        require(args["command"] == VALIDATION_COMMAND, "Only exact protected validation command permitted")
        require(agent != "architecture-security-reviewer", "Reviewer is read-only")
        if "description" in args:
            plain(args["description"], 256)
        if "timeout" in args:
            require(type(args["timeout"]) is int and 1000 <= args["timeout"] <= 600000, "Invalid timeout")
        trust(root, validation=True)
    elif tool == "Read":
        fields(args, {"file_path", "offset", "limit"}, {"file_path"})
        path = canonical(args["file_path"], root)
        require(path.is_file(), "Read needs a regular file")
        readable(path, root)
        for key in ("offset", "limit"):
            if key in args:
                require(type(args[key]) is int and 0 < args[key] <= 100000, "Invalid read range")
    elif tool in {"Glob", "Grep"}:
        allowed = {"pattern", "path"} if tool == "Glob" else {
            "pattern", "path", "glob", "type", "output_mode", "-A", "-B", "-C", "-n", "-i", "multiline", "head_limit", "offset",
        }
        fields(args, allowed, {"pattern"})
        plain(args["pattern"], 2048)
        if tool == "Glob":
            glob_pattern(args["pattern"])
        if "glob" in args:
            glob_pattern(args["glob"])
        if "type" in args:
            require(args["type"] in {"tf", "py", "sh", "md", "json", "yaml"}, "Unsupported search type")
        if "output_mode" in args:
            require(args["output_mode"] in {"content", "files_with_matches", "count"}, "Invalid output mode")
        for key in {"-A", "-B", "-C", "head_limit", "offset"} & args.keys():
            require(type(args[key]) is int and 0 <= args[key] <= 10000, "Invalid search bound")
        for key in {"-n", "-i", "multiline"} & args.keys():
            require(type(args[key]) is bool, "Invalid search flag")
        safe_tree(canonical(args.get("path", str(root)), root), root)
    elif tool in {"Edit", "Write"}:
        require(agent != "architecture-security-reviewer", "Reviewer is read-only")
        fields(args, {"file_path", "old_string", "new_string", "replace_all"} if tool == "Edit" else {"file_path", "content"},
               {"file_path", "old_string", "new_string"} if tool == "Edit" else {"file_path", "content"})
        writable(args["file_path"], root)
        for key in ("old_string", "new_string", "content"):
            if key in args:
                require(isinstance(args[key], str) and len(args[key]) <= 2 * 1024 * 1024 and "\x00" not in args[key], "Invalid source text")
        if "replace_all" in args:
            require(type(args["replace_all"]) is bool, "Invalid edit flag")
    elif tool in MCP_TOOLS:
        registry_arguments(tool, args)
    elif tool == "Agent":
        require(agent is None, "Nested delegation denied")
        fields(args, {"subagent_type", "description", "prompt"}, {"subagent_type", "description", "prompt"})
        require(args["subagent_type"] in AGENTS, "Unapproved subagent")
        plain(args["description"], 256)
        require(isinstance(args["prompt"], str) and 0 < len(args["prompt"]) <= 32768, "Invalid prompt")
    else:
        raise Denied("Unknown tool denied")
    return "Allowed by offline source policy"


def main():
    try:
        text = sys.stdin.read(2 * 1024 * 1024 + 1)
        require(len(text) <= 2 * 1024 * 1024, "Oversize event")
        reason = decide(strict_json(text))
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "permissionDecisionReason": reason}}))
        return 0
    except Exception:
        # Fail closed without reflecting user-controlled paths, commands or secrets.
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "Offline guard denied input; inspect policy or obtain human review."}}))
        print("Offline guard DENIED (invalid, unsupported, or untrusted input).", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
