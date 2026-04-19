#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Create a new WhatsApp group.

Usage:
    python3 scripts/create_group.py --name "LT Team" --members "Ezra,Adit,Rani"
    python3 scripts/create_group.py --name "LT Team" \
        --members "Ezra,081234567890" --members "Adit"

Pass --members multiple times and/or use comma-separated values. The agent
should ask the user for the group name and members (with comma-separated
support, repeatable if the list is long) before invoking this script.
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _split_members(raw_values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in raw_values:
        for part in raw.split(","):
            item = part.strip()
            if not item:
                continue
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
    return out


async def main(name: str, members: list[str]) -> dict:
    from src import LoginRequiredError, WhatsAppWeb

    try:
        async with WhatsAppWeb() as wa:
            return await wa.create_group(name=name, members=members)
    except LoginRequiredError:
        print("WhatsApp Web needs you to sign in first.", file=sys.stderr)
        print("Run: python3 scripts/login.py", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new WhatsApp group")
    parser.add_argument("--name", required=True, help="Group name / subject")
    parser.add_argument(
        "--members",
        action="append",
        required=True,
        help="Member name or phone. Repeatable; comma-separated values accepted.",
    )
    args = parser.parse_args()

    members = _split_members(args.members)
    if not members:
        print("No members provided.", file=sys.stderr)
        sys.exit(2)

    result = asyncio.run(main(args.name, members))
    print(json.dumps(result, indent=2, ensure_ascii=False))
