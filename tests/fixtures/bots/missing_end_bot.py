import sys
import time

for raw in sys.stdin:
    if raw.startswith("TURN "):
        print("MOVE 0 0 F 1 R", flush=True)
        time.sleep(10)

