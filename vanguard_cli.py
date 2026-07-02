#!/usr/bin/env python3
"""Console entry point for `vanguard` (installed via pip)."""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    argv = sys.argv[1:]
    routes = {
        "verify": ROOT / "verify.py",
        "replay": ROOT / "attack_replay.py",
        "demo": ROOT / "demo.py",
        "blue": ROOT / "blue_team" / "vanguard.py",
    }
    if not argv or argv[0] in ("-h", "--help"):
        print("vanguard <verify|replay|demo|blue> [args...]")
        print("  verify   run the 44-check correctness suite")
        print("  replay   run the ATT&CK attack-replay coverage report")
        print("  demo     run the end-to-end attack->defense story")
        print("  blue     the 24-tool blue-team CLI (e.g. vanguard blue tools)")
        return 0
    cmd, rest = argv[0], argv[1:]
    target = routes.get(cmd)
    if target is None:
        print(f"unknown command: {cmd}")
        return 2
    sys.argv = [str(target)] + rest
    sys.path.insert(0, str(target.parent))
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    sys.exit(main())
