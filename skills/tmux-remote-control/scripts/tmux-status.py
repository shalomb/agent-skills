#!/usr/bin/env python3
"""
tmux-status.py — token-efficient, tiered pane reads for agent TUI streams.
"""

import sys
import re
import argparse
from collections import Counter

def dedup_lines(lines):
    deduped = []
    last_line = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not deduped or deduped[-1].strip():
                deduped.append(line)
            continue
        if stripped == last_line:
            continue
        deduped.append(line)
        last_line = stripped
    return deduped

def get_signatures(lines):
    marker_pattern = re.compile(r'^([\s]*)([^\w\s\#\*\.\/\"\'\(\)\{\}\[\]])')
    signatures = []
    for i, line in enumerate(lines):
        m = marker_pattern.match(line)
        if m:
            marker = m.group(2)
            stripped = line.strip()
            if len(stripped) >= 3 and all(c == marker for c in stripped):
                continue
            sig = f"{len(m.group(1))}:{marker}"
            signatures.append((i, sig))
    return signatures

def infer_input_marker(signatures, total_lines):
    if not signatures:
        return None
    counts = Counter(sig for _, sig in signatures)
    last_sig = signatures[-1][1]
    for _, sig in reversed(signatures[-10:]):
        if 1 < counts[sig] < total_lines / 3:
            return sig
    return last_sig

def extract_turn(lines, signatures, input_marker):
    boundaries = [i for i, sig in signatures if sig == input_marker]
    if len(boundaries) >= 2:
        start_idx = boundaries[-2]
        end_idx = boundaries[-1]
    elif len(boundaries) == 1:
        start_idx = 0
        end_idx = boundaries[0]
    else:
        start_idx = 0
        end_idx = len(lines)
    return lines[start_idx:end_idx]

def cook_for_tokens(lines):
    cooked = []
    blank_count = 0
    box_chars = set('─━═_╭╮╯╰┏┓┛┗┣┫┳┻╋╏')
    
    for line in lines:
        stripped = line.strip()
        
        # Drop purely repeating TUI separator lines
        if len(stripped) >= 5 and len(set(stripped)) == 1 and stripped[0] in box_chars:
            continue
            
        # Remove known TUI tooltips that add zero value for LLMs
        line = line.replace(' (ctrl+o to expand)', '')
        line = line.replace(' (ctrl+r to review)', '')
        
        # Drop trailing spaces
        line = line.rstrip()
        
        # Remove up to 2 spaces of global TUI left-margin padding to save tokens
        # but preserve relative indentation for code blocks
        if line.startswith('  '):
            line = line[2:]
        elif line.startswith(' '):
            line = line[1:]
            
        line = line + '\n'
        
        # Collapse multiple blank lines
        if not line.strip():
            blank_count += 1
            if blank_count > 1:
                continue
        else:
            blank_count = 0
            
        cooked.append(line)
        
    while cooked and not cooked[-1].strip():
        cooked.pop()
    if cooked:
        cooked[-1] = cooked[-1].rstrip() + '\n'
        
    return cooked

def main():
    parser = argparse.ArgumentParser(description="Tiered reading for agent TUIs")
    parser.add_argument("--tier", choices=["status", "turn", "full"], default="turn",
                        help="Amount of context to return")
    args = parser.parse_args()

    raw_lines = sys.stdin.readlines()
    if not raw_lines:
        return

    deduped = dedup_lines(raw_lines)
    
    if args.tier == "full":
        final_lines = cook_for_tokens(deduped)
    elif args.tier == "status":
        final_lines = cook_for_tokens(deduped[-40:])[-30:]
    else:
        signatures = get_signatures(deduped)
        if not signatures:
            final_lines = cook_for_tokens(deduped[-40:])[-30:]
        else:
            input_marker = infer_input_marker(signatures, len(deduped))
            turn_lines = extract_turn(deduped, signatures, input_marker)
            final_lines = cook_for_tokens(turn_lines)
            
    for line in final_lines:
        sys.stdout.write(line)

if __name__ == "__main__":
    main()
