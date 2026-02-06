#!/usr/bin/env python3
import sys
import os
import re
from typing import Optional
from pathlib import Path

LINE_RE = re.compile(r"^\s*0x([01]{2}),\s*$")

def parse_line(line: str, line_no: int) -> int:
    """
    Parse '0x10,' where digits after 0x are BINARY bits (00/01/10/11).
    Returns integer 0..3.
    """
    m = LINE_RE.match(line)
    if not m:
        raise ValueError(f"Line {line_no}: invalid format: {line.strip()!r}")
    return int(m.group(1), 2)

def main(input_path: str, output_path: str, debug: bool = False, debug_limit: Optional[int] = None) -> None:
    in_file = Path(input_path)
    if not in_file.exists():
        print(f"ERROR: input file not found: {in_file}", file=sys.stderr)
        sys.exit(2)

    values = []
    original_lines = []

    with in_file.open("r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, start=1):
            if not line.strip():
                continue
            values.append(parse_line(line, i))
            original_lines.append(line.strip())

    original = len(values)
    padded = (4 - original % 4) % 4

    # pad with 00
    for _ in range(padded):
        values.append(0)
        original_lines.append("0x00,")

    packed = []
    mapping = []  # for debug mapping

    for i in range(0, len(values), 4):
        b0, b1, b2, b3 = values[i:i+4]
        byte = (b0 << 6) | (b1 << 4) | (b2 << 2) | b3
        packed.append(byte)

        if debug:
            mapping.append((byte, original_lines[i:i+4]))

    # write output
    with open(output_path, "w", encoding="utf-8") as out:
        for b in packed:
            out.write(f"0x{b:02X},\n")

    print("=== Pack Result (MSB-first) ===")
    print(f"Input file            : {in_file}")
    print(f"Valid level lines used : {original}")
    if padded:
        print(f"Padded lines added     : {padded} (as 0x00,)")
    print(f"Output lines           : {len(packed)}")
    if original:
        print(f"Line ratio             : {original} -> {len(packed)} (x{original/len(packed):.2f} smaller)")

    # debug print
    if debug:
        if debug_limit is None:
            print("\n=== Debug Mapping (all bytes) ===")
            items = mapping
        else:
            print(f"\n=== Debug Mapping (first {debug_limit} bytes) ===")
            items = mapping[:debug_limit]
        for idx, (byte, src) in enumerate(items):
            print(f"{idx:04d}: 0x{byte:02X}  <=  {', '.join(src)}")

if __name__ == "__main__":
    # If double-clicked on Windows (no args), use default filenames.
    if len(sys.argv) < 3:
        input_path = "input.txt"
        output_path = "output.txt"
        debug_flag = True
        debug_limit = None
        print("No args detected. Using defaults:")
        print(f"  input : {input_path}")
        print(f"  output: {output_path}")
        print("  debug : enabled")
        try:
            main(input_path, output_path, debug_flag)
        finally:
            if os.name == "nt":
                input("\nPress Enter to close...")
    else:
        debug_flag = False
        debug_limit = None
        args = []
        i = 1
        while i < len(sys.argv):
            a = sys.argv[i]
            if a == "--debug":
                debug_flag = True
                # Optional numeric limit after --debug
                if i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
                    debug_limit = int(sys.argv[i + 1])
                    i += 1
            elif a.startswith("--debug="):
                debug_flag = True
                val = a.split("=", 1)[1]
                if val.isdigit():
                    debug_limit = int(val)
            else:
                args.append(a)
            i += 1

        if len(args) < 2:
            print("Usage: python pack_levels_debug.py input.txt output.txt [--debug [N]]")
            sys.exit(1)

        main(args[0], args[1], debug_flag, debug_limit)
