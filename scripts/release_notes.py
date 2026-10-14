#!/usr/bin/env python3
"""Validate a release tag and extract its curated CHANGELOG section."""

import argparse
import json
from pathlib import Path
import re


def release_notes(root, tag):
    if not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag):
        raise ValueError("release tag must be vMAJOR.MINOR.PATCH (no leading zeroes)")
    version = tag[1:]
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    if package["version"] != version:
        raise ValueError("release tag does not match package.json version")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    sections = re.split(r"^## ", changelog, flags=re.MULTILINE)[1:]
    matches = []
    for section in sections:
        heading, _, body = section.partition("\n")
        if re.fullmatch(re.escape(version) + r"(?: - \d{4}-\d{2}-\d{2})?", heading.strip()):
            matches.append(body.strip())
    if len(matches) != 1 or not matches[0]:
        raise ValueError("CHANGELOG.md must contain exactly one nonempty ## " + version + " section")
    return matches[0] + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    args = parser.parse_args()
    try:
        notes = release_notes(Path(__file__).resolve().parents[1], args.tag)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Release validation failed: {exc}\n")
    print(notes, end="")


if __name__ == "__main__":
    main()
