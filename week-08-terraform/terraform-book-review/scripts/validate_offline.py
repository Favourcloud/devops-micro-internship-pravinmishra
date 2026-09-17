#!/usr/bin/python3
"""Fixed, credential-free mock validation. Copilot-authored inactive-kit draft.

This deliberately accepts a restricted HCL subset, not arbitrary HCL. It is not
an HCL security sandbox or network firewall. The host, interpreter, sealed trust
manifest, Terraform binary and checksum-locked provider mirror must be trusted.
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TERRAFORM_VERSION = "1.13.5"
TERRAFORM_SHA256 = "f9ebc400e229738b593bb4691263c0a55f6e4ba420199571a25f204db85281db"
AWS_VERSION = "6.64.0"
AWS_PROVIDER = "registry.terraform.io/hashicorp/aws"
TRUSTED = frozenset({
    "CLAUDE.md", ".claude/settings.json.example", ".mcp.json.example",
    ".claude/agents/terraform-engineer.md", ".claude/agents/architecture-security-reviewer.md",
    "hooks/pre_tool_guard.py", "hooks/post_tool_validate.py", "scripts/validate_offline.py",
    "source-lock.json", "terraform/.terraform.lock.hcl",
})
RUNTIME_SUFFIXES = {".py", ".sh", ".tpl", ".tftpl", ".template", ".conf", ".service", ".timer", ".txt", ".json", ".yaml", ".yml", ".md"}
EXTRACTOR_SOURCE = "scripts/verify_upstream.py"
DEPLOY_MANIFEST = "runtime/deploy-manifest.json"
RUNTIME_MANIFEST_EXPRESSION = '''{ for tier in ["web", "app", "initializer"] : tier => [
    for filename in concat(local.deploy_manifest.common, local.deploy_manifest.tiers[tier]) : {
      path        = "/opt/book-review/configuration/${filename}"
      content     = file("${path.module}/../runtime/${filename}")
      owner       = "root:root"
      permissions = endswith(filename, ".sh") || endswith(filename, ".py") ? "0755" : "0644"
    }
  ] }'''
RUNTIME_MANIFEST_WITH_SOURCE_LOCK = RUNTIME_MANIFEST_EXPRESSION.replace(
    'file("${path.module}/../runtime/${filename}")',
    'filename == "source-lock.json" ? file("${path.module}/../source-lock.json") : file("${path.module}/../runtime/${filename}")',
)
DEPLOY_MANIFEST_EXPRESSION = 'jsondecode(file("${path.module}/../runtime/deploy-manifest.json"))'
DEPLOY_MANIFEST_RELATIVE_EXPRESSION = 'jsondecode(file("../runtime/deploy-manifest.json"))'
# A reviewed, closed expression: filename is bound only by this runtime fileset.
# Matching tokens (not arbitrary variable names) prevents shadowing/escape tricks.
RUNTIME_FILESET_EXPRESSION = r'''[for filename in sort(fileset("${path.module}/../runtime", "**")) : {
    path        = "/opt/book-review/configuration/${filename}"
    content     = file("${path.module}/../runtime/${filename}")
    owner       = "root:root"
    permissions = endswith(filename, ".sh") || endswith(filename, ".py") ? "0755" : "0644"
  } if can(regex("\\.(py|sh|json|txt|conf|service|template|tftpl)$", filename))]'''
FORBIDDEN_BLOCKS = {"backend", "cloud", "provisioner", "connection", "import", "removed", "ephemeral"}
FORBIDDEN_FUNCTIONS = {"pathexpand", "abspath", "fileexists", "filebase64", "filebase64sha256", "filebase64sha512", "filemd5", "filesha1", "filesha256", "filesha512", "filebase64sha1"}


class Refused(ValueError):
    pass


def need(condition, reason):
    if not condition:
        raise Refused(reason)


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    def invalid(_):
        raise Refused("Non-finite JSON")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def project_path(root, relative, exists=True):
    need(isinstance(relative, str) and relative and not Path(relative).is_absolute()
         and ".." not in Path(relative).parts and "\x00" not in relative, "Unsafe project path")
    path = root
    for part in Path(relative).parts:
        path /= part
        need(not path.is_symlink(), "Symlink source denied")
        if path.exists():
            mode = path.lstat().st_mode
            need(stat.S_ISDIR(mode) or stat.S_ISREG(mode), "Special source denied")
            need(not path.is_file() or path.stat().st_nlink == 1, "Hardlinked source denied")
    need(path.resolve().is_relative_to(root), "Source escapes project")
    need(not exists or path.exists(), "Required source missing")
    return path


def trusted_manifest(root):
    path = project_path(root, ".claude/trusted-files.json")
    need(path.stat().st_size < 128 * 1024, "Manifest too large")
    manifest = strict_json(path.read_text())
    need(isinstance(manifest, dict) and set(manifest) == {"version", "files", "terraform_tests"}
         and manifest["version"] == 1, "Invalid manifest")
    files, tests = manifest["files"], manifest["terraform_tests"]
    need(isinstance(files, dict) and isinstance(tests, dict), "Invalid trust maps")
    need(TRUSTED <= files.keys() and bool(tests), "Human must seal source lock, provider lock and fixed mock tests")
    need(not (files.keys() & tests.keys()), "Overlapping trust entries")
    for name, expected in {**files, **tests}.items():
        need(isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected), "Invalid trusted digest")
        if name in tests:
            need(re.fullmatch(r"terraform/tests/[a-z0-9_]+\.tftest\.hcl", name), "Unsafe test path")
        target = project_path(root, name)
        need(target.is_file() and target.stat().st_size <= 2 * 1024 * 1024, "Invalid trusted file")
        need(digest(target) == expected, "Trusted file changed; human resealing required")
    return manifest


def reject_live_inputs(root):
    # Inspect names/metadata, never read live state or credential content. Scan the
    # whole project, so ignored or nested inputs cannot silently enter Terraform.
    count = 0
    for base, dirs, files in os.walk(root, followlinks=False):
        if Path(base) == root / "hooks" and ".offline-work" in dirs:
            dirs.remove(".offline-work")
        for name in dirs + files:
            count += 1
            need(count <= 8192, "Source tree too large")
            rel = (Path(base) / name).relative_to(root).as_posix()
            path = project_path(root, rel)
            low = name.lower()
            need(not (low in {".terraform", ".env", ".aws", ".ssh", "credentials", "node_modules"}
                      or (low == "secrets" and rel != "terraform/modules/secrets")
                      or low.startswith(".env.")
                      or ".tfstate" in low or ".tfplan" in low
                      or low.endswith((".plan", ".pem", ".key", ".p12"))
                      or (".tfvars" in low and not (low.endswith(".tfvars.example") and path.parent in {root, root / "terraform"}))
                      or low in {"override.tf", "override.tf.json"}
                      or low.endswith(("_override.tf", "_override.tf.json", ".tf.json"))), "Live/unsupported input present")
            need(not path.is_file() or path.stat().st_size <= 2 * 1024 * 1024, "Oversize source file")


@dataclass(frozen=True)
class Token:
    kind: str
    value: str


@dataclass
class Block:
    kind: str
    labels: list
    attrs: dict
    blocks: list


def quoted_end(text, start):
    i = start + 1
    while i < len(text):
        if text[i] == "\\":
            i += 2
        elif text.startswith(("${", "%{"), i) and (i == 0 or text[i - 1] not in "$%"):
            i = expression_end(text, i + 2) + 1
        elif text[i] == '"':
            return i + 1
        else:
            i += 1
    raise Refused("Unterminated HCL string")


def expression_end(text, start):
    depth, i = 1, start
    while i < len(text):
        if text[i] == '"':
            i = quoted_end(text, i)
            continue
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise Refused("Unterminated interpolation")


def lex(text):
    result, i = [], 0
    need(len(text) <= 2 * 1024 * 1024 and "\x00" not in text, "Invalid HCL text")
    while i < len(text):
        c = text[i]
        if c in " \t\r":
            i += 1
        elif c == "\n":
            result.append(Token("nl", c)); i += 1
        elif c == "#" or text.startswith("//", i):
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            need(end >= 0, "Unterminated comment")
            if "\n" in text[i:end]:
                result.append(Token("nl", "\n"))
            i = end + 2
        elif c == '"':
            end = quoted_end(text, i)
            result.append(Token("string", text[i:end])); i = end
        elif text.startswith("<<", i):
            match = re.match(r"<<-?([A-Za-z_][A-Za-z0-9_]*)\r?\n", text[i:])
            need(match is not None, "Unsupported heredoc")
            begin = i + match.end()
            end = re.search(r"(?m)^[ \t]*" + re.escape(match[1]) + r"[ \t]*\r?$", text[begin:])
            need(end is not None, "Unterminated heredoc")
            result.append(Token("template", text[begin:begin + end.start()]))
            i = begin + end.end()
        elif c.isalpha() or c == "_":
            match = re.match(r"[A-Za-z_][A-Za-z0-9_-]*", text[i:])
            need(match is not None, "Unsupported identifier")
            result.append(Token("id", match[0])); i += len(match[0])
        elif c.isdigit():
            match = re.match(r"[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?", text[i:])
            result.append(Token("number", match[0])); i += len(match[0])
        else:
            need(c in "{}[]()=.,?:!<>+-*/%&|", "Unsupported HCL token")
            result.append(Token("symbol", c)); i += 1
    return result


def compact(tokens):
    return [t for t in tokens if t.kind != "nl"]


def literal(tokens):
    tokens = compact(tokens)
    need(len(tokens) == 1 and tokens[0].kind == "string", "Expected literal string")
    value = json.loads(tokens[0].value)
    need("${" not in value and "%{" not in value, "Dynamic literal denied")
    return value


def parse(tokens):
    def body(index, nested=False):
        attrs, blocks = {}, []
        while index < len(tokens):
            if tokens[index].kind == "nl":
                index += 1; continue
            if tokens[index].value == "}":
                need(nested, "Unexpected closing brace")
                return attrs, blocks, index + 1
            name = tokens[index]
            need(name.kind == "id", "Unsupported HCL body")
            index += 1
            need(index < len(tokens), "Incomplete HCL body")
            if tokens[index].value == "=":
                need(name.value not in attrs, "Duplicate HCL attribute")
                index += 1
                start, stack = index, []
                while index < len(tokens):
                    token = tokens[index]
                    if not stack and (token.kind == "nl" or token.value == "}"):
                        break
                    if token.value in {"(", "[", "{"}:
                        stack.append({"(": ")", "[": "]", "{": "}"}[token.value])
                    elif token.value in {")", "]", "}"}:
                        need(stack and stack.pop() == token.value, "Unbalanced expression")
                    index += 1
                need(not stack and index > start, "Incomplete expression")
                attrs[name.value] = tokens[start:index]
            else:
                labels = []
                while index < len(tokens) and tokens[index].kind in {"string", "id"}:
                    labels.append(literal([tokens[index]]) if tokens[index].kind == "string" else tokens[index].value)
                    index += 1
                need(index < len(tokens) and tokens[index].value == "{", "Unsupported block")
                child_attrs, child_blocks, index = body(index + 1, True)
                blocks.append(Block(name.value, labels, child_attrs, child_blocks))
        need(not nested, "Unclosed HCL block")
        return attrs, blocks, index
    attrs, blocks, _ = body(0)
    return attrs, blocks


def walk_blocks(blocks):
    for block in blocks:
        yield block
        yield from walk_blocks(block.blocks)


def call_arguments(tokens, index):
    args, start, stack = [], index + 2, [")"]
    i = start
    while i < len(tokens):
        value = tokens[i].value
        if value in {"(", "[", "{"}:
            stack.append({"(": ")", "[": "]", "{": "}"}[value])
        elif value in {")", "]", "}"}:
            need(stack and stack.pop() == value, "Unbalanced function")
            if not stack:
                args.append(tokens[start:i]); return args
        elif value == "," and len(stack) == 1:
            args.append(tokens[start:i]); start = i + 1
        i += 1
    raise Refused("Incomplete function")


def file_literal(tokens, origin, root):
    tokens = compact(tokens)
    need(len(tokens) == 1 and tokens[0].kind == "string", "Dynamic file path denied")
    raw = json.loads(tokens[0].value)
    raw = raw.replace("${path.module}", str(origin.parent)).replace("${path.root}", str(root / "terraform"))
    need("${" not in raw and "%{" not in raw and "~" not in raw and "\x00" not in raw, "Dynamic file path denied")
    path = Path(raw)
    if not path.is_absolute():
        # Terraform file functions resolve ordinary relative paths at the root module.
        path = root / "terraform" / path
    path = path.resolve()
    need(path.is_relative_to(root / "runtime") or path in {root / "source-lock.json", root / EXTRACTOR_SOURCE}, "Only staged runtime/source-lock/extractor reads permitted")
    project_path(root, path.relative_to(root).as_posix())
    return path


def inspect_deploy_manifest(root, source_lock_root=True):
    path = project_path(root, DEPLOY_MANIFEST)
    need(path.is_file() and path.stat().st_size <= 65536, "Invalid deployment manifest")
    data = strict_json(path.read_text())
    need(isinstance(data, dict) and {"common", "tiers"} <= data.keys()
         and isinstance(data["tiers"], dict) and set(data["tiers"]) == {"web", "app", "initializer"}, "Invalid deployment tiers")
    for names in [data["common"], *data["tiers"].values()]:
        need(isinstance(names, list) and len(names) <= 128, "Invalid deployment file list")
        for name in names:
            need(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_./-]+", name)
                 and not name.startswith("/") and ".." not in name.split("/")
                 and not any(part.startswith(".") for part in name.split("/")), "Unsafe deployment filename")
            target = project_path(root, name if source_lock_root and name == "source-lock.json" else "runtime/" + name)
            need(target.is_file() and target.suffix in RUNTIME_SUFFIXES, "Deployment source missing/unsupported")


def approved_runtime_paths(blocks, origin, root):
    approved = set()
    if origin.parent != root / "terraform":
        return approved
    fileset = compact(lex(RUNTIME_FILESET_EXPRESSION))
    manifest = compact(lex(RUNTIME_MANIFEST_EXPRESSION))
    source_lock_manifest = compact(lex(RUNTIME_MANIFEST_WITH_SOURCE_LOCK))
    declarations = [compact(lex(value)) for value in (DEPLOY_MANIFEST_EXPRESSION, DEPLOY_MANIFEST_RELATIVE_EXPRESSION)]
    for block in blocks:
        expression = block.attrs.get("runtime_files", []) if block.kind == "locals" else []
        value = compact(expression)
        matched = value == fileset
        if value in (manifest, source_lock_manifest) and compact(block.attrs.get("deploy_manifest", [])) in declarations:
            inspect_deploy_manifest(root, source_lock_root=value == source_lock_manifest)
            matched = True
        if matched:
            approved.update(id(token) for token in expression if token.kind == "string"
                            and token.value == '"${path.module}/../runtime/${filename}"')
    return approved


def inspect_expressions(tokens, origin, root, approved_dynamic=frozenset()):
    tokens = compact(tokens)
    for i, token in enumerate(tokens):
        if token.kind in {"string", "template"}:
            text = token.value
            cursor = 0
            while cursor < len(text):
                if text.startswith(("${", "%{"), cursor) and (cursor == 0 or text[cursor - 1] not in "$%"):
                    end = expression_end(text, cursor + 2)
                    inspect_expressions(lex(text[cursor + 2:end]), origin, root)
                    cursor = end + 1
                else:
                    cursor += 1
        if token.kind != "id":
            continue
        need(not (token.value == "provider" and tokens[i + 1:i + 3] == [Token("symbol", ":"), Token("symbol", ":")]), "Provider-defined functions denied")
        if i + 1 >= len(tokens) or tokens[i + 1].value != "(":
            continue
        name = token.value
        need(name not in FORBIDDEN_FUNCTIONS, "Unapproved filesystem function")
        if name in {"file", "templatefile", "fileset"}:
            args = call_arguments(tokens, i)
            need(len(args) == (1 if name == "file" else 2), "Unexpected filesystem function arity")
            argument = compact(args[0])
            if name == "file" and len(argument) == 1 and id(argument[0]) in approved_dynamic:
                need(project_path(root, "runtime").is_dir(), "Runtime fileset source missing")
                continue
            target = file_literal(args[0], origin, root)
            if name == "fileset":
                pattern = literal(args[1])
                need(target.is_dir() and target.is_relative_to(root / "runtime")
                     and re.fullmatch(r"[A-Za-z0-9_*?./-]+", pattern) and ".." not in pattern.split("/")
                     and not pattern.startswith("/"), "Unsafe fileset")
            else:
                need(target.is_file(), "Missing staged file")
                if name == "templatefile":
                    # Recursively evaluating templates could introduce hidden file reads.
                    content = target.read_text()
                    cursor = 0
                    while cursor < len(content):
                        if content.startswith(("${", "%{"), cursor) and (cursor == 0 or content[cursor - 1] not in "$%"):
                            end = expression_end(content, cursor + 2)
                            expression = compact(lex(content[cursor + 2:end]))
                            # Inspect nested interpolation strings too. Reject any
                            # file-like token conservatively rather than evaluating
                            # source-controlled template dependencies recursively.
                            for part in expression:
                                need(not (part.kind == "id" and (part.value.startswith("file") or part.value in {"templatefile", "pathexpand", "abspath"})), "Template filesystem calls denied")
                            inspect_expressions(expression, target, root)
                            cursor = end + 1
                        else:
                            cursor += 1


def inspect_config(path, root):
    tokens = lex(path.read_text())
    attrs, blocks = parse(tokens)
    need(not attrs, "Root HCL attributes denied")
    allowed = {"terraform", "provider", "variable", "locals", "output", "module", "resource", "data", "check"}
    need(all(b.kind in allowed for b in blocks), "Unsupported root block")
    for block in walk_blocks(blocks):
        need(block.kind not in FORBIDDEN_BLOCKS, "Execution/live-backend block denied")
        if block.kind == "dynamic":
            need(block.labels and block.labels[0] not in FORBIDDEN_BLOCKS, "Dynamic execution block denied")
        if block.kind in {"resource", "data"}:
            need(len(block.labels) == 2 and block.labels[0].startswith("aws_"), "Only mocked AWS resource/data types permitted")
        if block.kind == "provider":
            need(block.labels == ["aws"] and len(block.blocks) <= 1
                 and all(child.kind == "default_tags" and not child.labels and not child.blocks
                         and set(child.attrs) == {"tags"} for child in block.blocks), "Only unaliased AWS provider/default_tags permitted")
            need(set(block.attrs) <= {"region", "skip_credentials_validation", "skip_requesting_account_id", "skip_metadata_api_check", "skip_region_validation"}, "Provider credentials/endpoint/alias denied")
        if block.kind == "module":
            need("source" in block.attrs, "Missing module source")
            source = literal(block.attrs["source"])
            need(source.startswith(("./", "../")), "Remote module denied")
            target = (path.parent / source).resolve()
            need(target.is_relative_to(root / "terraform" / "modules") and target.is_dir(), "Module outside staged local modules")
            project_path(root, target.relative_to(root).as_posix())
            need("version" not in block.attrs and "providers" not in block.attrs, "Module provider remapping denied")
        if "provider" in block.attrs:
            need(compact(block.attrs["provider"]) == [Token("id", "aws")], "Provider alias denied")
        if block.kind == "required_providers":
            need(not block.blocks and set(block.attrs) == {"aws"}, "Only exact AWS requirement permitted")
            value = compact(block.attrs["aws"])
            need(value[0].value == "{" and value[-1].value == "}", "Invalid provider requirement")
            # Object attributes are newline separated in the original token stream.
            declaration = block.attrs["aws"]
            provider_attrs, provider_blocks = parse(declaration[1:-1])
            need(not provider_blocks and set(provider_attrs) == {"source", "version"}, "Invalid AWS declaration")
            need(literal(provider_attrs["source"]) in {"hashicorp/aws", AWS_PROVIDER}
                 and literal(provider_attrs["version"]) in {AWS_VERSION, "= " + AWS_VERSION}, "AWS provider not exactly pinned")
        if block.kind == "terraform":
            need(set(block.attrs) <= {"required_version"} and all(b.kind == "required_providers" for b in block.blocks), "Live Terraform settings denied")
            if "required_version" in block.attrs:
                need(literal(block.attrs["required_version"]) in {TERRAFORM_VERSION, "= " + TERRAFORM_VERSION}, "Terraform version not pinned")
    inspect_expressions(tokens, path, root, approved_runtime_paths(blocks, path, root))
    return blocks


def inspect_test(path, root):
    tokens = lex(path.read_text())
    attrs, blocks = parse(tokens)
    need(not attrs and all(b.kind in {"mock_provider", "run", "variables", "override_resource", "override_data"} for b in blocks), "Unsupported test structure")
    mocks = [b for b in blocks if b.kind == "mock_provider"]
    runs = [b for b in blocks if b.kind == "run"]
    need(len(mocks) == 1 and mocks[0].labels == ["aws"]
         and set(mocks[0].attrs) <= {"override_during"} and runs, "Exactly one local unaliased AWS mock required")
    allowed = {"mock_provider", "mock_resource", "mock_data", "run", "variables", "assert", "plan_options", "override_resource", "override_data"}
    for block in walk_blocks(blocks):
        need(block.kind in allowed, "Unsupported nested test block")
        need(not ({"providers", "alias", "source"} & block.attrs.keys()), "Test provider/module override denied")
        if block.kind == "run":
            need(compact(block.attrs.get("command", [])) == [Token("id", "plan")], "Every test run must explicitly use command = plan")
        if block.kind in {"mock_resource", "mock_data"}:
            need(len(block.labels) == 1 and block.labels[0].startswith("aws_"), "Only AWS mock fixtures permitted")
        if block.kind in {"override_resource", "override_data"}:
            target = "".join(t.value for t in compact(block.attrs.get("target", [])))
            need(re.fullmatch(r"(?:module\.[a-zA-Z0-9_]+\.)*(?:data\.)?aws_[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+", target), "Only explicit mocked AWS address overrides permitted")
        if "override_during" in block.attrs:
            need(compact(block.attrs["override_during"]) == [Token("id", "plan")], "Only explicit override_during = plan permitted")
    inspect_expressions(tokens, path, root)


def source_inventory(root, manifest):
    reject_live_inputs(root)
    if (root / DEPLOY_MANIFEST).is_file():
        need(DEPLOY_MANIFEST in manifest["files"]
             and digest(root / DEPLOY_MANIFEST) == manifest["files"][DEPLOY_MANIFEST], "Human must seal runtime/deploy-manifest.json")
        inspect_deploy_manifest(root)
    files = []
    for path in sorted((root / "terraform").rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if path.name.endswith(".tftest.hcl"):
            need(rel in manifest["terraform_tests"], "Unsealed Terraform test")
            inspect_test(path, root)
            files.append(rel)
        elif path.suffix == ".tf":
            need("tests" not in path.relative_to(root / "terraform").parts, "Terraform config in test directory denied")
            inspect_config(path, root)
            files.append(rel)
        elif rel == "terraform/.terraform.lock.hcl":
            attrs, blocks = parse(lex(path.read_text()))
            need(not attrs and len(blocks) == 1 and blocks[0].kind == "provider"
                 and blocks[0].labels == [AWS_PROVIDER]
                 and literal(blocks[0].attrs.get("version", [])) == AWS_VERSION
                 and "hashes" in blocks[0].attrs, "Lockfile must pin sole official AWS provider")
            files.append(rel)
        else:
            need(path.name == "README.md" or (path.parent == root / "terraform" and path.name.endswith(".tfvars.example")), "Unsupported Terraform input")
    need(any(name.startswith("terraform/") and name.count("/") == 1 and name.endswith(".tf") for name in files), "Root module missing")
    need(set(manifest["terraform_tests"]) <= set(files), "Trusted tests missing")
    root_blocks = []
    for name in files:
        if name.count("/") == 1 and name.endswith(".tf"):
            root_blocks.extend(parse(lex((root / name).read_text()))[1])
    terraform = [b for b in root_blocks if b.kind == "terraform"]
    need(any("required_version" in b.attrs for b in terraform)
         and any(c.kind == "required_providers" for b in terraform for c in b.blocks), "Pinned root requirements missing")
    for path in sorted((root / "runtime").rglob("*")):
        if path.is_file():
            need(path.suffix in RUNTIME_SUFFIXES and not path.name.startswith("."), "Unsupported runtime data")
            files.append(path.relative_to(root).as_posix())
    files.append("source-lock.json")
    extractor = project_path(root, EXTRACTOR_SOURCE, exists=False)
    if extractor.is_file():
        files.append(EXTRACTOR_SOURCE)
    need(len(files) <= 512 and sum((root / name).stat().st_size for name in files) <= 12 * 1024 * 1024, "Staging budget exceeded")
    return files


def isolated_environment(work):
    # Go's os.TempDir preserves relative TMPDIR. Both Terraform and its provider
    # inherit this cwd; relative Unix socket names avoid macOS sockaddr limits
    # without writing outside this project or using a system temporary directory.
    return {
        "PATH": "/usr/bin:/bin", "HOME": str(work / "home"),
        "TMPDIR": "../socket", "TF_DATA_DIR": str(work / "data"),
        "TF_CLI_CONFIG_FILE": str(work / "terraform.rc"),
        "TF_IN_AUTOMATION": "1", "TF_INPUT": "0", "CHECKPOINT_DISABLE": "1",
        "AWS_EC2_METADATA_DISABLED": "true", "AWS_SDK_LOAD_CONFIG": "false",
        "AWS_CONFIG_FILE": str(work / "empty-config"),
        "AWS_SHARED_CREDENTIALS_FILE": str(work / "empty-config"),
        "BOTO_CONFIG": str(work / "empty-config"),
        "LANG": "C", "LC_ALL": "C",
    }


def verify_schema(schema):
    resources = schema.get("provider_schemas", {}).get(AWS_PROVIDER, {}).get("resource_schemas", {})
    for resource, attribute in (("aws_db_instance", "password_wo"), ("aws_secretsmanager_secret_version", "secret_string_wo")):
        field = resources.get(resource, {}).get("block", {}).get("attributes", {}).get(attribute, {})
        need(field.get("write_only") is True and field.get("sensitive") is True, "Pinned provider lacks sensitive write-only contract")


def assert_no_markers(serialized, markers):
    """Helper for separately reviewed synthetic artifact tests, never live state.

    A passing scan only covers the supplied serialization. It is not evidence
    that an unapplied plan JSON or a sensitive flag proves state confidentiality.
    """
    need(markers and all(isinstance(m, str) and len(m) >= 16 for m in markers), "Use unmistakable synthetic markers")
    text = serialized if isinstance(serialized, str) else json.dumps(serialized, sort_keys=True)
    need(not any(marker in text for marker in markers), "Synthetic marker leaked into ordinary serialization")


def run_stage(binary, arguments, cwd, env, label):
    result = subprocess.run([str(binary), *arguments], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=240, check=False)
    # Do not reflect diagnostics containing source expressions or synthetic secrets.
    need(result.returncode == 0, "Offline stage failed: " + label + " (diagnostics suppressed)")
    need(len(result.stdout) <= 64 * 1024 * 1024, "Unexpected tool output size")
    print("PASS " + label)
    return result.stdout


def validate(root, binary_input, mirror_input):
    root = root.resolve()
    manifest = trusted_manifest(root)
    files = source_inventory(root, manifest)
    need(binary_input and mirror_input, "Set A5_TERRAFORM_BIN and A5_PROVIDER_MIRROR, or explicit CLI paths")
    binary, mirror = Path(binary_input).expanduser().resolve(), Path(mirror_input).expanduser().resolve()
    need(binary.is_file() and os.access(binary, os.X_OK) and digest(binary) == TERRAFORM_SHA256, "Approved immutable Terraform binary missing/mismatched")
    need(mirror.is_dir(), "Approved filesystem provider mirror missing; no download permitted")
    scratch_root = root / "hooks" / ".offline-work"
    project_path(root, "hooks/.offline-work", exists=False)
    scratch_root.mkdir(mode=0o700, exist_ok=True)
    need(stat.S_IMODE(scratch_root.stat().st_mode) == 0o700, "Scratch root must have mode 0700")
    work = Path(tempfile.mkdtemp(prefix="validation-", dir=scratch_root))
    try:
        for directory in ("home", "data", "source", "source/terraform", "source/socket"):
            (work / directory).mkdir(mode=0o700, parents=True, exist_ok=True)
        (work / "empty-config").write_text("")
        (work / "empty-config").chmod(0o600)
        config = ('disable_checkpoint = true\nprovider_installation {\n'
                  '  filesystem_mirror {\n    path = ' + json.dumps(str(mirror)) + '\n'
                  '    include = ["' + AWS_PROVIDER + '"]\n  }\n}\n')
        (work / "terraform.rc").write_text(config)
        (work / "terraform.rc").chmod(0o600)
        for name in files:
            target = work / "source" / name
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            source = project_path(root, name)
            # Trusted tests/lock cannot change between review and staging unnoticed.
            data = source.read_bytes()
            expected = {**manifest["files"], **manifest["terraform_tests"]}.get(name)
            need(expected is None or hashlib.sha256(data).hexdigest() == expected, "Trust input changed during staging")
            target.write_bytes(data)
            target.chmod(0o600)
        # Recheck the snapshot actually executed; no source-controlled Python or
        # shell is ever imported or executed, including developer unit tests.
        staged = work / "source"
        source_inventory(staged, manifest)
        cwd, env = staged / "terraform", isolated_environment(work)
        version = strict_json(run_stage(binary, ["version", "-json"], cwd, env, "version"))
        need(version.get("terraform_version") == TERRAFORM_VERSION, "Terraform version mismatch")
        platform = version.get("platform", "")
        need(re.fullmatch(r"(?:darwin|linux)_(?:amd64|arm64)", platform), "Unsupported provider platform")
        need((mirror / AWS_PROVIDER / AWS_VERSION / platform).is_dir(), "Pinned platform provider absent; parent must supply mirror/lock, no downloads")
        run_stage(binary, ["fmt", "-check", "-recursive", "-no-color"], cwd, env, "fmt")
        run_stage(binary, ["init", "-backend=false", "-lockfile=readonly", "-input=false", "-no-color"], cwd, env, "init")
        run_stage(binary, ["validate", "-no-color"], cwd, env, "validate")
        schema = strict_json(run_stage(binary, ["providers", "schema", "-json"], cwd, env, "provider-schema"))
        verify_schema(schema)
        filters = ["-filter=" + name.removeprefix("terraform/") for name in sorted(manifest["terraform_tests"])]
        run_stage(binary, ["test", "-no-color", "-test-directory=tests", *filters], cwd, env, "mock-plan-tests")
        print("Offline validation passed; no real plan/apply, cloud, runtime or Claude evidence.")
    finally:
        shutil.rmtree(work)
        try:
            scratch_root.rmdir()
        except OSError:
            pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terraform-bin", default=os.environ.get("A5_TERRAFORM_BIN"))
    parser.add_argument("--provider-mirror", default=os.environ.get("A5_PROVIDER_MIRROR"))
    args = parser.parse_args(argv)
    try:
        validate(ROOT, args.terraform_bin, args.provider_mirror)
        return 0
    except Exception as error:
        reason = str(error) if isinstance(error, Refused) else "Malformed input, tool timeout, or filesystem error"
        print("OFFLINE VALIDATION REFUSED: " + reason, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
