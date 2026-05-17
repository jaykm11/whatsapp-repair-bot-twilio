"""One-off: add deploy test marker to welcome message on main's agent.py."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "app" / "services" / "agent.py"

text = subprocess.run(
    ["git", "show", "origin/main:app/services/agent.py"],
    capture_output=True,
    check=True,
    cwd=ROOT,
).stdout.decode("utf-8")

anchor = 'Send a photo to get started! \U0001f527"""'
replacement = 'Send a photo to get started! \U0001f527\n\nBuild marker: banana-test-2026-05-16"""'
if anchor not in text:
    raise SystemExit("anchor not found in origin/main agent.py")
AGENT.write_text(text.replace(anchor, replacement, 1), encoding="utf-8", newline="\n")
print("Updated", AGENT)
