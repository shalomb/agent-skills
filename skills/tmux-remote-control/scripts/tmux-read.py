import sys
import re

def main():
    try:
        lines = [line.rstrip() for line in sys.stdin]
    except UnicodeDecodeError:
        return # Handle binary junk gracefully

    # Remove empty lines from end
    while lines and not lines[-1].strip():
        lines.pop()
    
    if not lines:
        return

    # The last line is the current prompt (where cursor is).
    current_prompt = lines[-1]
    
    # 1. Identify Prompt Pattern
    # Matches typical shell prompts ending in symbol + space
    # We broaden the regex to capture any non-alphanumeric character as the terminator.
    # This covers $, #, %, >, ➜, Φ, ℵ, etc.
    regex = r'([^a-zA-Z0-9])(\s*)$'
    match = re.search(regex, current_prompt)
    
    start_index = 0
    
    if match:
        symbol = match.group(1)
        # Identify the "stable prefix" of the prompt.
        # e.g. "user@host:~/dir$ " -> prefix "user@host:~"
        # We can't assume the path is stable, but "user@host" usually is.
        # Let's take the first 30% of the prompt as a required match?
        # Or just the first 4 chars?
        
        full_prefix = current_prompt[:match.start(1)]
        
        # Heuristic: Use the first 5 chars as a signature, if available.
        signature = full_prefix[:5] if len(full_prefix) >= 5 else full_prefix
        
        # Scan backwards for the previous prompt
        # We start from the line before the last one
        for i in range(len(lines) - 2, -1, -1):
            line = lines[i]
            
            # Candidate Check 1: Must contain the symbol
            if symbol not in line:
                continue
                
            # Candidate Check 2: Must start with the signature (if signature exists)
            # This filters out "echo $VAR" output lines that don't start with "user@"
            if signature and not line.startswith(signature):
                continue
                
            # If we are here, it's highly likely this is the previous command line.
            # We break here. The output starts at i+1.
            start_index = i + 1
            break
    
    # Extract result
    # From start_index to -1 (exclude last prompt)
    result = lines[start_index:-1]
    
    # Trim leading empty lines (often occurs after command)
    while result and not result[0].strip():
        result.pop(0)
    
    # Trim trailing empty lines
    while result and not result[-1].strip():
        result.pop()
        
    for line in result:
        print(line)

if __name__ == "__main__":
    main()
