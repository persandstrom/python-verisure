#!/usr/bin/env python3
"""Backfill git tags and GitHub Releases from PyPI release history."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from release_utils import (  # noqa: E402
    create_release,
    list_pypi_versions,
    parse_readme_release_note,
    resolve_commit_for_version,
    tag_exists,
    version_key,
)


@dataclass(frozen=True)
class BackfillRow:
    version: str
    commit: str | None
    source: str
    score: float
    notes: str
    action: str


def parse_versions(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


def select_versions(
    *,
    since: str | None,
    versions: list[str] | None,
) -> list[str]:
    if versions:
        return sorted(versions, key=version_key)
    return list_pypi_versions(since)


def plan_backfill(
    versions: list[str],
    *,
    min_score: float,
) -> list[BackfillRow]:
    rows: list[BackfillRow] = []
    for version in versions:
        if tag_exists(version):
            rows.append(
                BackfillRow(
                    version=version,
                    commit=None,
                    source="existing-tag",
                    score=1.0,
                    notes=parse_readme_release_note(version) or "",
                    action="skip",
                )
            )
            continue

        try:
            commit, source, score = resolve_commit_for_version(
                version,
                min_score=min_score,
            )
        except ValueError as exc:
            rows.append(
                BackfillRow(
                    version=version,
                    commit=None,
                    source=str(exc),
                    score=0.0,
                    notes=parse_readme_release_note(version) or "",
                    action="skip-error",
                )
            )
            continue
        notes = parse_readme_release_note(version) or "See README Version History"
        if commit is None:
            action = "skip-low-confidence"
        else:
            action = "create"
        rows.append(
            BackfillRow(
                version=version,
                commit=commit,
                source=source,
                score=score,
                notes=notes,
                action=action,
            )
        )
    return rows


def print_table(rows: list[BackfillRow]) -> None:
    headers = ("version", "commit", "source", "score", "action")
    print(
        f"{'version':<8} {'commit':<10} {'source':<18} {'score':<6} action"
    )
    print("-" * 60)
    for row in rows:
        commit = row.commit[:9] if row.commit else "-"
        print(
            f"{row.version:<8} {commit:<10} {row.source:<18} "
            f"{row.score:<6.2f} {row.action}"
        )


def apply_backfill(rows: list[BackfillRow], *, dry_run: bool) -> int:
    created = 0
    for row in rows:
        if row.action != "create" or row.commit is None:
            continue
        if dry_run:
            print(f"DRY RUN would create tag {row.version} at {row.commit}")
            created += 1
            continue
        try:
            create_release(row.version, row.notes, row.commit)
        except subprocess.CalledProcessError as exc:
            command = subprocess.list2cmdline(exc.cmd)
            print(
                f"Failed to create tag/release for {row.version}: {command}",
                file=sys.stderr,
            )
            if exc.stdout:
                print(exc.stdout, file=sys.stderr, end="")
            if exc.stderr:
                print(exc.stderr, file=sys.stderr, end="")
            return 1
        print(f"Created tag and release {row.version} at {row.commit}")
        created += 1
    return created


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--since",
        default="2.6.2",
        help="Include PyPI releases at or after this version (default: 2.6.2)",
    )
    parser.add_argument(
        "--versions",
        help="Comma-separated explicit version list (overrides --since)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.95,
        help="Minimum fingerprint match score (default: 0.95)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create tags and GitHub Releases (default is dry-run)",
    )
    parser.add_argument(
        "--confirm",
        default="",
        help='Required for --apply; must be "I-have-reviewed-the-table"',
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    dry_run = not args.apply
    if args.apply and args.confirm != "I-have-reviewed-the-table":
        print(
            'Refusing to apply without --confirm "I-have-reviewed-the-table"',
            file=sys.stderr,
        )
        return 1

    versions = select_versions(
        since=args.since,
        versions=parse_versions(args.versions),
    )
    rows = plan_backfill(versions, min_score=args.min_score)
    print_table(rows)

    creatable = sum(1 for row in rows if row.action == "create")
    skipped = len(rows) - creatable
    print()
    print(f"Planned: {creatable} create, {skipped} skip")

    if creatable == 0:
        return 0

    result = apply_backfill(rows, dry_run=dry_run)
    if isinstance(result, int) and result == 1 and not dry_run:
        return 1

    created = result
    if dry_run:
        print(f"DRY RUN complete ({created} tag(s) would be created)")
    else:
        print(f"Applied {created} tag(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
