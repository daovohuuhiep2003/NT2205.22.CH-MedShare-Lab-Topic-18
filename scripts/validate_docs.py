"""Validate the Topic 18 documentation bundle without external dependencies.

Run: python scripts/validate_docs.py
Self tests: python scripts/validate_docs.py --self-test
This checks structure and references, NOT Mermaid parsing or application security.
"""
from pathlib import Path
from urllib.parse import unquote
import hashlib
import json
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HASHES = {
    "docs/requirements/course-guideline.md": "749487E95FF70D91289FD31BF1C3F43A689E3E849BF5845734D34FF11EE9E0D6",
    "docs/requirements/topic-18.md": "057CA6227FECCD370BB1F8DA02863EC6988689859DCF0D41B6C7899FCB597CF4",
}
EXCLUDED_DIRS = {'.git', '.local-backups', '.venv', 'venv', '__pycache__',
                 'node_modules', 'build', 'dist', 'results', 'raw', 'oracle',
                 'runs', 'runtime', 'secrets', '.secrets', '.codex', '.agents'}
PHASES = ["System Analysis", "Assets", "Threat Model", "Security Requirements",
          "Security Architecture", "Cryptographic Requirements", "Cryptographic Mechanisms",
          "Implementation", "Security Testing", "Evaluation"]


def local_links(text):
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if re.match(r"^[a-zA-Z]+:", target) or target.startswith("#"):
            continue
        yield unquote(target.split("#", 1)[0])


def phase_errors(text):
    errors, positions = [], []
    for number, phase in enumerate(PHASES, 1):
        match = re.search(r"^## " + str(number) + r"\. " + re.escape(phase) + r"\b", text, re.M)
        if match:
            positions.append(match.start())
        else:
            errors.append("Missing phase: " + phase)
    if positions != sorted(positions):
        errors.append("Wrong phase order")
    return errors


def diagram_errors(text):
    lines = text.splitlines()
    errors = []
    if not lines or not lines[0].startswith(("flowchart ", "sequenceDiagram", "stateDiagram-v2")):
        errors.append("Unknown Mermaid directive")
    opens = sum(bool(re.match(r"\s*(subgraph |alt |opt |loop |par )", line)) for line in lines)
    closes = sum(line.strip() == "end" for line in lines)
    if opens != closes:
        errors.append("Unbalanced Mermaid blocks")
    return errors


def snippet_errors(text):
    errors = []
    if text.count("<augment_code_snippet") != text.count("</augment_code_snippet>"):
        errors.append("Unbalanced snippet wrapper")
    for body in re.findall(r"<augment_code_snippet[^>]*>([\s\S]*?)</augment_code_snippet>", text):
        match = re.search(r"\x60{4}\w+\n([\s\S]*?)\n\x60{4}", body)
        if not match or len(match.group(1).splitlines()) >= 10:
            errors.append("Invalid snippet fence or excerpt length")
    return errors


def validate(root):
    errors, links = [], 0
    for name, digest in SOURCE_HASHES.items():
        path = root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest().upper() != digest:
            errors.append("Missing or modified source: " + name)
    docs = [p for p in root.rglob("*.md")
            if p.relative_to(root).as_posix() not in SOURCE_HASHES
            and not any(part in EXCLUDED_DIRS for part in p.relative_to(root).parts)]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        if chr(65533) in text or any(ord(c) < 32 and c not in "\n\r\t" for c in text):
            errors.append("Encoding/control character: " + path.name)
        for target in local_links(text):
            links += 1
            if not (path.parent / target).exists():
                errors.append("Broken link: " + path.name + " -> " + target)
        errors.extend(path.name + ": " + e for e in snippet_errors(text))
    main = (root / "docs/planning/implementation-plan.md").read_text(encoding="utf-8")
    proposal = (root / "docs/proposal/project-proposal.md").read_text(encoding="utf-8")
    tests = (root / "docs/testing/experiments-and-validation.md").read_text(encoding="utf-8")
    trace = (root / "docs/testing/traceability-matrix.md").read_text(encoding="utf-8")
    crypto = (root / "docs/design/crypto-and-protocol-design.md").read_text(encoding="utf-8")
    for name, text in [("main", main), ("proposal", proposal)]:
        errors.extend(name + ": " + e for e in phase_errors(text))
    for prefix, count, text in [("T", 18, main), ("SR", 18, main), ("CR", 12, main),
                                ("TC", 30, tests), ("M", 12, crypto)]:
        definitions = set(re.findall(r"^\| (" + prefix + r"-\d{2}) \|", text, re.M))
        expected = {f"{prefix}-{i:02d}" for i in range(1, count + 1)}
        if definitions != expected:
            errors.append("Definition mismatch " + prefix + ": " + str(sorted(definitions ^ expected)))
        if prefix in ("T", "SR", "CR", "TC"):
            missing = expected - set(re.findall(prefix + r"-\d{2}", trace))
            if missing:
                errors.append("Missing trace coverage " + prefix + ": " + str(sorted(missing)))
    for number in (1, 2, 3, 4, 5, 7, 8, 9):
        if not re.search(r"^### E" + str(number) + r"\b", tests, re.M):
            errors.append("Missing experiment E" + str(number))
    for number in range(10):
        if not re.search(r"^\| F" + str(number) + r" ", main, re.M):
            errors.append("Missing flow F" + str(number))
    diagrams = list((root / "docs/diagrams").glob("*.mmd"))
    for path in diagrams:
        errors.extend(path.name + ": " + e for e in diagram_errors(path.read_text(encoding="utf-8")))
    return {"markdown_files_checked": len(docs), "local_links_checked": links,
            "diagrams_structurally_checked": len(diagrams),
            "source_hashes_unchanged": not any("modified source" in e for e in errors),
            "errors": errors, "mermaid_validation": "Structural only; parser/render not available",
            "application_security_tests": "NOT_RUN: no application implementation in initial workspace"}


class ValidatorTests(unittest.TestCase):
    def test_links_decode_spaces_and_skip_external(self):
        self.assertEqual(list(local_links("[a](file%20name.md) [b](https://example.org) [c](#id)")), ["file name.md"])

    def test_complete_phases(self):
        text = "\n".join(f"## {i}. {p}" for i, p in enumerate(PHASES, 1))
        self.assertEqual(phase_errors(text), [])

    def test_missing_and_reordered_phases(self):
        self.assertTrue(phase_errors("## 2. Assets\n## 1. System Analysis"))

    def test_balanced_mermaid(self):
        self.assertEqual(diagram_errors('flowchart LR\nsubgraph X["Trusted"]\nA-->B\nend\n'), [])

    def test_unbalanced_mermaid(self):
        self.assertTrue(diagram_errors("sequenceDiagram\nalt denied\nA->>B: reject\n"))

    def test_snippet_wrapper_and_length(self):
        fence = chr(96) * 4
        good = '<augment_code_snippet mode="EXCERPT">\n' + fence + 'mermaid\nflowchart LR\nA-->B\n' + fence + '\n</augment_code_snippet>'
        self.assertEqual(snippet_errors(good), [])
        self.assertTrue(snippet_errors(good.replace("A-->B", "\n".join(["A-->B"] * 12))))
        self.assertTrue(snippet_errors(good.replace("</augment_code_snippet>", "")))


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        result = validate(ROOT)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        sys.exit(1 if result["errors"] else 0)
