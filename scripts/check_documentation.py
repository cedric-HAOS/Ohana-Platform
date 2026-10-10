#!/usr/bin/env python3
"""Read-only checks of Ohana document links, examples and catalogue mirrors."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml


def document_paths(root: Path) -> list[Path]:
    paths = []
    for repo in sorted(root.glob("Ohana-*")):
        if not (repo / ".git").exists() or repo.name.endswith(".worktrees"):
            continue
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
                "*.md",
            ],
            capture_output=True,
            check=True,
        )
        paths.extend(
            repo / name
            for name in result.stdout.decode("utf-8").split("\0")
            if name and not name.startswith("graphify-out/") and (repo / name).is_file()
        )
    return sorted(set(paths))


def blocks(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    """Keep line offsets outside fences; return their language and contents."""
    prose, examples = [], []
    marker, start, language, body = "", 0, "", []
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\r\n"))
        if not marker and match:
            marker, start = match[1], number
            language = match[2].strip().split(" ", 1)[0].lower()
            body = []
            prose.append("\n")
        elif marker:
            prose.append("\n")
            if (
                match
                and match[1][0] == marker[0]
                and len(match[1]) >= len(marker)
                and not match[2].strip()
            ):
                examples.append((start, language, "".join(body)))
                marker = ""
            else:
                body.append(line)
        else:
            prose.append(line)
    if marker:
        raise ValueError(f"unclosed code fence at line {start}")
    return "".join(prose), examples


def anchors(text: str) -> set[str]:
    prose, _ = blocks(text)
    counts: Counter[str] = Counter()
    result = set(re.findall(r"(?:id|name)=[\"']([^\"']+)[\"']", prose))
    for heading in re.findall(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", prose, re.MULTILINE):
        heading = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", heading)
        heading = re.sub(r"<[^>]+>|`", "", heading)
        slug = re.sub(r"[^\w\-\s]", "", heading.lower()).replace(" ", "-")
        count = counts[slug]
        counts[slug] += 1
        result.add(slug if not count else f"{slug}-{count}")
    return result


def destinations(prose: str) -> list[tuple[int, str]]:
    prose = re.sub(r"`+[^`\n]*`+", "", prose)
    references = {
        name.lower(): target
        for name, target in re.findall(
            r"^\s*\[([^\]]+)\]:\s*(<[^>]+>|\S+)",
            prose,
            re.MULTILINE,
        )
    }
    found = [
        (match.start(), match[1])
        for match in re.finditer(
            r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^)\n]+)\s*\)",
            prose,
        )
    ]
    for match in re.finditer(r"!?\[[^\]\n]*\]\[([^\]]+)\]", prose):
        if match[1].lower() in references:
            found.append((match.start(), references[match[1].lower()]))
    results = []
    for position, target in found:
        target = target.strip()
        target = (
            target[1 : target.index(">")]
            if target.startswith("<")
            else re.sub(r"\s+[\"'].*$", "", target)
        )
        results.append((prose.count("\n", 0, position) + 1, target))
    return results


def check(root: Path) -> dict:
    counts: Counter[str] = Counter()
    issues = []
    anchor_cache = {}

    def issue(path: Path, line: int, detail: str) -> None:
        issues.append(
            {"path": path.relative_to(root).as_posix(), "line": line, "detail": detail}
        )

    for path in document_paths(root):
        counts["documents"] += 1
        try:
            prose, examples = blocks(path.read_text(encoding="utf-8-sig"))
        except ValueError as error:
            issue(path, 1, str(error))
            continue
        for line, destination in destinations(prose):
            parts = urlsplit(destination)
            if parts.scheme or parts.netloc:
                match = re.fullmatch(
                    r"/cedric-HAOS/(Ohana-[^/]+)/(?:blob|tree)/main/(.+)", parts.path
                )
                if parts.hostname != "github.com" or not match:
                    counts["external_links_not_fetched"] += 1
                    continue
                target = root / match[1] / unquote(match[2])
                counts["github_main_links_checked_locally"] += 1
            else:
                target = (
                    (path.parent / unquote(parts.path)).resolve()
                    if parts.path
                    else path
                )
                counts["local_links"] += 1
            if not target.exists():
                issue(path, line, f"missing target: {destination}")
            elif parts.fragment and target.suffix.lower() == ".md":
                if target not in anchor_cache:
                    anchor_cache[target] = anchors(
                        target.read_text(encoding="utf-8-sig")
                    )
                if unquote(parts.fragment) not in anchor_cache[target]:
                    issue(path, line, f"missing heading: {destination}")
        for line, language, body in examples:
            counts["code_blocks"] += 1
            try:
                if language in {"yaml", "yml"}:
                    list(yaml.safe_load_all(body))
                    counts["yaml_examples"] += 1
                elif language == "json":
                    json.loads(body)
                    counts["json_examples"] += 1
                elif language in {"bash", "sh"}:
                    previous = ""
                    for offset, command in enumerate(body.splitlines(), 1):
                        if (
                            command.lstrip().startswith("--")
                            and previous
                            and not previous.endswith(("\\", "|", "&&", "("))
                        ):
                            issue(
                                path,
                                line + offset,
                                "shell option without command continuation",
                            )
                        previous = command.rstrip()
                    counts["shell_examples"] += 1
            except (yaml.YAMLError, json.JSONDecodeError):
                issue(path, line, f"invalid {language} example")

    for name in ("release-manifest.yaml", "release-catalog.yaml"):
        canonical = root / "Ohana-Platform" / name
        mirror = root / "Ohana-Installer" / "config" / name
        if (
            not canonical.is_file()
            or not mirror.is_file()
            or canonical.read_bytes() != mirror.read_bytes()
        ):
            issue(mirror, 1, f"differs from Ohana-Platform/{name}")
        else:
            counts["identical_catalogue_files"] += 1
    for path in sorted((root / "Ohana-Platform" / "diagrams").rglob("*.svg")):
        try:
            ET.parse(path)
            counts["svg_documents"] += 1
        except ET.ParseError:
            issue(path, 1, "invalid SVG XML")
    return {"counts": dict(counts), "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument(
        "--json", type=Path, help="Write the evidence report to this file"
    )
    args = parser.parse_args()
    report = check(args.root.resolve())
    if not report["counts"].get("documents"):
        parser.error("no Ohana documents found")
    if args.json:
        args.json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(json.dumps(report["counts"], ensure_ascii=True))
    for entry in report["issues"]:
        print(f"{entry['path']}:{entry['line']}: {entry['detail']}")
    return bool(report["issues"])


if __name__ == "__main__":
    raise SystemExit(main())
