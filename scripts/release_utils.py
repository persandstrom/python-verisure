"""Utilities for release tagging and GitHub Releases."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
SETUP_PY = ROOT / "setup.py"
README = ROOT / "README.md"
VERSION_PATTERN = re.compile(r"version\s*=\s*['\"]([^'\"]+)['\"]")
FINGERPRINT_SUFFIXES = {".py", ".in"}
FINGERPRINT_NAMES = {"LICENSE", "README.md", "setup.py", "MANIFEST.in"}

MANUAL_COMMIT_MAP: dict[str, str] = {
    # Merge commit on version-2 (#183).
    "2.7.1": "7e93418",
    "2.7.0": "f81d3c4",
    "2.6.9": "dceffbe",
}


@dataclass(frozen=True)
class VersionBump:
    should_release: bool
    version: str
    previous_version: str | None
    notes: str
    reason: str


def run(
    *args: str,
    check: bool = True,
    capture: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        check=check,
        capture_output=capture,
        text=text,
        cwd=ROOT,
    )


def parse_setup_version(path: Path = SETUP_PY) -> str:
    content = path.read_text(encoding="utf-8")
    match = VERSION_PATTERN.search(content)
    if not match:
        msg = f"Could not parse version from {path}"
        raise ValueError(msg)
    return match.group(1)


def parse_setup_version_at(ref: str, path: str = "setup.py") -> str | None:
    result = run("git", "show", f"{ref}:{path}", check=False)
    if result.returncode != 0:
        return None
    match = VERSION_PATTERN.search(result.stdout)
    return match.group(1) if match else None


def version_key(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for piece in version.split("."):
        digits = "".join(char for char in piece if char.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def compare_versions(left: str, right: str) -> int:
    left_key = version_key(left)
    right_key = version_key(right)
    if left_key < right_key:
        return -1
    if left_key > right_key:
        return 1
    return 0


def parse_readme_release_note(version: str, readme_path: Path = README) -> str | None:
    for line in readme_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{version} "):
            return stripped[len(version) + 1 :]
    return None


def tag_exists(version: str) -> bool:
    result = run("git", "rev-parse", f"refs/tags/{version}", check=False)
    return result.returncode == 0


def detect_bump(event_name: str, ref: str | None = None) -> VersionBump:
    current = parse_setup_version()
    notes = parse_readme_release_note(current)
    release_notes = notes or "See README Version History"

    if tag_exists(current):
        msg = f"Tag {current} already exists"
        raise ValueError(msg)

    if event_name == "workflow_dispatch":
        return VersionBump(
            should_release=True,
            version=current,
            previous_version=None,
            notes=release_notes,
            reason="Manual release dispatch",
        )

    previous = parse_setup_version_at("HEAD~1")
    if previous is None:
        return VersionBump(
            should_release=True,
            version=current,
            previous_version=None,
            notes=release_notes,
            reason="No previous setup.py to compare",
        )

    direction = compare_versions(current, previous)
    if direction == 0:
        return VersionBump(
            should_release=False,
            version=current,
            previous_version=previous,
            notes=release_notes,
            reason="Version unchanged",
        )
    if direction < 0:
        msg = f"Version decreased from {previous} to {current}"
        raise ValueError(msg)

    return VersionBump(
        should_release=True,
        version=current,
        previous_version=previous,
        notes=release_notes,
        reason=f"Version bumped from {previous} to {current}",
    )


def fingerprint_paths() -> set[str]:
    tracked = run("git", "ls-files").stdout.splitlines()
    paths: set[str] = set()
    for path in tracked:
        pure = PurePosixPath(path)
        if pure.name in FINGERPRINT_NAMES or pure.suffix in FINGERPRINT_SUFFIXES:
            paths.add(path.replace("\\", "/"))
    return paths


def file_fingerprint(relative_path: str, content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def fingerprint_from_tree(paths: set[str], reader) -> dict[str, str]:
    fingerprints: dict[str, str] = {}
    for path in sorted(paths):
        try:
            content = reader(path)
        except (FileNotFoundError, KeyError, subprocess.CalledProcessError):
            continue
        if content is None:
            continue
        fingerprints[path] = file_fingerprint(path, content)
    return fingerprints


def fingerprint_from_commit(commit: str, paths: set[str]) -> dict[str, str]:
    def reader(path: str) -> bytes | None:
        result = run("git", "show", f"{commit}:{path}", check=False)
        if result.returncode != 0:
            return None
        return result.stdout.encode("utf-8")

    return fingerprint_from_tree(paths, reader)


def download_pypi_artifact(version: str) -> tuple[bytes, str]:
    with urllib.request.urlopen(  # noqa: S310
        f"https://pypi.org/pypi/vsure/{version}/json",
    ) as response:
        metadata = json.load(response)
    sdists = [item for item in metadata["urls"] if item["packagetype"] == "sdist"]
    wheels = [item for item in metadata["urls"] if item["packagetype"] == "bdist_wheel"]
    if sdists:
        url = sdists[0]["url"]
        kind = "sdist"
    elif wheels:
        url = wheels[0]["url"]
        kind = "wheel"
    else:
        msg = f"No sdist or wheel found on PyPI for vsure {version}"
        raise ValueError(msg)
    with urllib.request.urlopen(url) as response:  # noqa: S310
        return response.read(), kind


def normalize_artifact_path(path: str) -> str | None:
    pure = PurePosixPath(path)
    if any(part.endswith(".egg-info") or part.endswith(".dist-info") for part in pure.parts):
        return None
    if pure.parts and pure.parts[0] == "test":
        return None
    if pure.name in {"PKG-INFO", "setup.cfg", "METADATA", "WHEEL", "RECORD"}:
        return None
    if pure.name in FINGERPRINT_NAMES or pure.suffix in FINGERPRINT_SUFFIXES:
        return pure.as_posix()
    return None


def normalize_sdist_path(path: str) -> str | None:
    parts = PurePosixPath(path).parts
    if len(parts) < 2:
        return None
    return normalize_artifact_path(PurePosixPath(*parts[1:]).as_posix())


def fingerprint_from_archive(data: bytes, kind: str) -> dict[str, str]:
    contents: dict[str, bytes] = {}
    paths: set[str] = set()

    if kind == "sdist":
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                normalized = normalize_sdist_path(member.name)
                if normalized is None:
                    continue
                paths.add(normalized)
                extracted = tar.extractfile(member)
                if extracted is None:
                    continue
                contents[normalized] = extracted.read()
    elif kind == "wheel":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for name in archive.namelist():
                normalized = normalize_artifact_path(name)
                if normalized is None:
                    continue
                paths.add(normalized)
                contents[normalized] = archive.read(name)
    else:
        msg = f"Unsupported artifact kind: {kind}"
        raise ValueError(msg)

    def reader(path: str) -> bytes:
        return contents[path]

    return fingerprint_from_tree(paths, reader)


def fingerprint_from_pypi(version: str) -> dict[str, str]:
    data, kind = download_pypi_artifact(version)
    return fingerprint_from_archive(data, kind)


def fingerprint_match_score(
    expected: dict[str, str],
    candidate: dict[str, str],
) -> tuple[float, int, int]:
    if not expected:
        return 0.0, 0, 0
    matched = 0
    for path, digest in expected.items():
        if candidate.get(path) == digest:
            matched += 1
    total = len(expected)
    return matched / total, matched, total


def list_pypi_versions(since: str | None = None) -> list[str]:
    with urllib.request.urlopen("https://pypi.org/pypi/vsure/json") as response:  # noqa: S310
        metadata = json.load(response)
    versions = sorted(metadata["releases"], key=version_key)
    if since is None:
        return versions
    return [version for version in versions if compare_versions(version, since) >= 0]


def resolve_commit_for_version(
    version: str,
    *,
    manual_map: dict[str, str] | None = None,
    min_score: float = 0.95,
) -> tuple[str | None, str, float]:
    overrides = {**MANUAL_COMMIT_MAP, **(manual_map or {})}
    if version in overrides:
        commit = overrides[version]
        return commit, "manual", 1.0

    expected = fingerprint_from_pypi(version)
    commits = run("git", "rev-list", "HEAD").stdout.splitlines()
    best_commit: str | None = None
    best_score = 0.0
    best_detail = "0/0"

    repo_paths = fingerprint_paths()
    search_paths = set(expected) | repo_paths

    for commit in commits:
        candidate = fingerprint_from_commit(commit, search_paths)
        score, matched, total = fingerprint_match_score(expected, candidate)
        if score > best_score:
            best_score = score
            best_commit = commit
            best_detail = f"{matched}/{total}"

    if best_commit is None or best_score < min_score:
        return None, f"fingerprint ({best_detail})", best_score
    return best_commit, f"fingerprint ({best_detail})", best_score


def write_github_output(name: str, value: str) -> None:
    output_path = Path(os.environ["GITHUB_OUTPUT"])
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def create_release(version: str, notes: str, commit: str | None = None) -> None:
    target = commit or "HEAD"
    subject = f"Release {version}"
    body = notes if notes else "See README Version History"

    run("git", "tag", "-a", version, target, "-m", subject)
    run("git", "push", "origin", version)
    run(
        "gh",
        "release",
        "create",
        version,
        "--title",
        subject,
        "--notes",
        body,
        "--target",
        target,
    )


def cmd_detect_bump(args: argparse.Namespace) -> int:
    bump = detect_bump(args.event_name, args.ref)
    print(bump.reason)
    if args.github_output:
        write_github_output("should_release", str(bump.should_release).lower())
        write_github_output("version", bump.version)
        write_github_output("notes", bump.notes.replace("\n", " "))
        if bump.previous_version:
            write_github_output("previous_version", bump.previous_version)
    if not bump.should_release:
        return 0
    if args.strict_notes and parse_readme_release_note(bump.version) is None:
        msg = f"No README Version History entry for {bump.version}"
        raise ValueError(msg)
    return 0


def cmd_create_release(args: argparse.Namespace) -> int:
    create_release(args.version, args.notes, args.commit)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect = subparsers.add_parser("detect-bump")
    detect.add_argument(
        "--event-name",
        default="push",
        help="GitHub event name (push or workflow_dispatch)",
    )
    detect.add_argument("--ref")
    detect.add_argument(
        "--github-output",
        action="store_true",
        help="Write step outputs to GITHUB_OUTPUT",
    )
    detect.add_argument(
        "--strict-notes",
        action="store_true",
        help="Fail when README has no release note",
    )
    detect.set_defaults(func=cmd_detect_bump)

    create = subparsers.add_parser("create-release")
    create.add_argument("--version", required=True)
    create.add_argument("--notes", required=True)
    create.add_argument("--commit")
    create.set_defaults(func=cmd_create_release)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
