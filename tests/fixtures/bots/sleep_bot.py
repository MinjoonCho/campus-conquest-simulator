import sys
import time

delay = float(sys.argv[1])
block = []
for raw in sys.stdin:
    line = raw.rstrip("\n")
    if line == "END":
        if any(item.startswith("TURN ") for item in block):
            time.sleep(delay)
            print("END", flush=True)
        block = []
    else:
        block.append(line)

