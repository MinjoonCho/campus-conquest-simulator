import sys

for raw in sys.stdin:
    if raw.startswith("TURN "):
        raise SystemExit(3)

