import sys

block = []
for raw in sys.stdin:
    line = raw.rstrip("\n")
    if line == "END":
        if any(item.startswith("TURN ") for item in block):
            print("END", flush=True)
        block = []
    else:
        block.append(line)

