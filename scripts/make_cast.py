#!/usr/bin/env python3
"""
Generate an asciinema v2 .cast recording of demo.py with cinematic timing.
Upload the result to asciinema.org, or convert to GIF with `agg demo.cast demo.gif`.
Usage: python3 scripts/make_cast.py > media/demo.cast
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    # capture demo output (ANSI preserved)
    proc = subprocess.run([sys.executable, str(ROOT / "demo.py")],
                          capture_output=True, text=True, timeout=90,
                          env={"PYTHONUNBUFFERED": "1", "PATH": "/usr/bin:/bin",
                               "TERM": "xterm-256color"})
    out = proc.stdout

    header = {"version": 2, "width": 100, "height": 44,
              "timestamp": int(time.time()),
              "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
              "title": "Vanguard-OOB — live ransomware defense"}
    lines = [json.dumps(header)]

    t = 0.0
    # opening prompt keystrokes for realism
    for ch in "python3 demo.py\n":
        t += 0.04
        lines.append(json.dumps([round(t, 3), "o", ch]))
    t += 0.6

    # stream demo output line-by-line; pause longer on the dramatic beats
    for line in out.splitlines(keepends=True):
        plain = line
        delay = 0.09
        if "ATTACK" in plain or "CRYPTO-SPIKE" in plain:
            delay = 0.9
        elif "AUTO-ISOLATION" in plain or "FAILOVER" in plain:
            delay = 0.8
        elif "INCIDENT NEUTRALISED" in plain or "Recovery time" in plain:
            delay = 0.7
        elif plain.strip() == "":
            delay = 0.15
        t += delay
        lines.append(json.dumps([round(t, 3), "o", plain]))

    t += 1.2
    lines.append(json.dumps([round(t, 3), "o", "\n"]))
    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
