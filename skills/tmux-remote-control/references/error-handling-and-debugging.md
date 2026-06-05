---
title: Tmux Error Handling and Debugging
description: Strategies for debugging tmux command failures and interpreting output
---

# Tmux Error Handling and Debugging Guide

## Overview

Tmux command execution can sometimes produce silent failures, confusing output, or unexpected behavior. This guide covers debugging strategies and how to interpret tmux command results.

## Common Issues

### Issue 1: Silent Failures (No Output, Non-Zero Exit Code)

**Symptom**:
```bash
./scripts/tmux-exec.sh "session:window.pane" 'gh api repos/owner/repo'
# Returns: (empty output, exit code 1)
```

**Root Causes**:
- Command doesn't exist in tmux pane
- Command requires authentication (not available in pane)
- Command producing output but script not capturing it properly
- Network timeout or API failure

**Solution**:
```bash
# 1. Read pane contents directly to see what happened
./scripts/tmux-read.sh "session:window.pane"

# 2. Check tmux pane state
tmux capture-pane -t "session:window.pane" -p

# 3. List all available sessions/panes
./scripts/tmux-list.sh

# 4. Test with simple command first
./scripts/tmux-exec.sh "session:window.pane" 'echo "test"'

# 5. Run command directly in pane to see raw output
tmux send-keys -t "session:window.pane" 'gh api repos/owner/repo' Enter
```

### Issue 2: Incomplete Output

**Symptom**:
```bash
./scripts/tmux-exec.sh "session:window.pane" 'gh api repos/owner/repo | jq .'
# Returns: Partial JSON, cut off mid-object
```

**Root Causes**:
- Large JSON response truncated
- Command output buffering issues
- Tmux pane line limit (usually 2000 lines)
- Output redirection problems

**Solution**:
```bash
# 1. Redirect to file instead
./scripts/tmux-exec.sh "session:window.pane" \
  'gh api repos/owner/repo > /tmp/output.json'

# 2. Read file back
./scripts/tmux-exec.sh "session:window.pane" 'cat /tmp/output.json'

# 3. For very large responses, use pagination
gh api --paginate repos/owner/repo
```

### Issue 3: Command Not Found

**Symptom**:
```bash
./scripts/tmux-exec.sh "session:window.pane" 'gh api ...'
# Returns: "gh: command not found" or similar
```

**Root Causes**:
- `gh` CLI not in PATH in tmux session
- Wrong shell (bash vs zsh)
- PATH doesn't match login shell PATH

**Solution**:
```bash
# 1. Check if command is available
./scripts/tmux-exec.sh "session:window.pane" 'which gh'

# 2. Use full path if available
./scripts/tmux-exec.sh "session:window.pane" '/usr/local/bin/gh api ...'

# 3. Load shell profile if needed
./scripts/tmux-exec.sh "session:window.pane" 'source ~/.bashrc && gh api ...'

# 4. Check environment variables
./scripts/tmux-exec.sh "session:window.pane" 'echo $PATH'
```

### Issue 4: Authentication Failures

**Symptom**:
```bash
./scripts/tmux-exec.sh "session:window.pane" 'gh api repos/owner/repo'
# Returns: "HTTP 401: Unauthorized" or "Not authenticated"
```

**Root Causes**:
- No GitHub token in pane environment
- Token expired or invalid
- Credentials not loaded in tmux session

**Solution**:
```bash
# 1. Check authentication status
./scripts/tmux-exec.sh "session:window.pane" 'gh auth status'

# 2. Verify token is available
./scripts/tmux-exec.sh "session:window.pane" 'echo $GITHUB_TOKEN'

# 3. Re-authenticate if needed
./scripts/tmux-exec.sh "session:window.pane" 'gh auth login'

# 4. Export token explicitly
export GITHUB_TOKEN=$(gh auth token)
./scripts/tmux-exec.sh "session:window.pane" \
  "export GITHUB_TOKEN=$GITHUB_TOKEN && gh api ..."
```

### Issue 5: Timeout

**Symptom**:
```bash
./scripts/tmux-exec.sh "session:window.pane" 'long-running-command'
# Returns: timeout after 30 seconds
```

**Root Causes**:
- Command takes longer than timeout (usually 30s)
- Network delay/API latency
- Command hangs waiting for input

**Solution**:
```bash
# 1. Use longer timeout if available
timeout 120 ./scripts/tmux-exec.sh "session:window.pane" 'command'

# 2. Run in background and poll
./scripts/tmux-exec.sh "session:window.pane" 'command &'
# Then check status later

# 3. Redirect to file for long operations
./scripts/tmux-exec.sh "session:window.pane" \
  'long-command > /tmp/output.txt 2>&1 &'

# 4. Monitor progress
./scripts/tmux-exec.sh "session:window.pane" 'tail -f /tmp/output.txt'
```

## Debugging Workflow

### Step 1: Verify Target Pane
```bash
# Check if pane exists and is accessible
./scripts/tmux-list.sh | jq '.[] | select(.session_name == "my-session")'

# Confirm pane is active
tmux list-panes -t "my-session:0" -F "#{pane_id} #{pane_active} #{pane_current_command}"
```

### Step 2: Test Basic Connectivity
```bash
# Simplest possible test
./scripts/tmux-exec.sh "session:window.pane" 'echo "hello"'

# If this fails, pane is unreachable
# If this works, pane is accessible
```

### Step 3: Check Environment
```bash
# Check PATH, shell, user
./scripts/tmux-exec.sh "session:window.pane" 'echo $SHELL; echo $PATH; whoami'

# Check if required tools exist
./scripts/tmux-exec.sh "session:window.pane" 'which gh; which jq; which curl'
```

### Step 4: Run Simpler Version of Command
```bash
# Instead of: gh api repos/owner/repo | jq complex_filter
# Try: gh api repos/owner/repo

# See if output arrives without jq
# See if it's a piping issue vs. command issue
```

### Step 5: Inspect Pane Directly
```bash
# Look at what's actually in the pane right now
tmux capture-pane -t "session:window.pane" -p | tail -50

# Look for error messages, partial output, hang indicators
```

## Debug Pattern for Complex Operations

```bash
#!/bin/bash

SESSION="target:window.pane"
CMD='your-command-here'

echo "=== Debug Info ==="
echo "Session: $SESSION"
echo "Command: $CMD"
echo ""

# Step 1: Verify pane exists
echo "1. Verifying pane exists..."
./scripts/tmux-list.sh | jq ".[] | select(.session_name == \"${SESSION%:*}\")" || {
  echo "ERROR: Session not found"
  exit 1
}

# Step 2: Test echo
echo "2. Testing basic connectivity..."
./scripts/tmux-exec.sh "$SESSION" 'echo "pane-is-responsive"' || {
  echo "ERROR: Pane not responding"
  exit 1
}

# Step 3: Check environment
echo "3. Checking environment..."
./scripts/tmux-exec.sh "$SESSION" 'echo "PATH: $PATH"; which gh || echo "gh not found"'

# Step 4: Run command with error output
echo "4. Running target command..."
RESULT=$(./scripts/tmux-exec.sh "$SESSION" "$CMD" 2>&1)
RC=$?

echo "Exit Code: $RC"
echo "Output Length: ${#RESULT}"
echo "Output:"
echo "$RESULT" | head -20
[ ${#RESULT} -gt 100 ] && echo "... (${#RESULT} bytes total)"

# Step 5: If failed, try alternatives
if [ $RC -ne 0 ]; then
  echo ""
  echo "5. Command failed. Trying alternatives..."
  
  # Alternative 1: Direct tmux send
  echo "   Trying direct tmux send..."
  tmux send-keys -t "$SESSION" "$CMD" Enter
  sleep 2
  ./scripts/tmux-read.sh "$SESSION"
  
  # Alternative 2: With explicit output redirect
  echo "   Trying with file redirect..."
  ./scripts/tmux-exec.sh "$SESSION" "$CMD > /tmp/debug.txt 2>&1" || true
  ./scripts/tmux-exec.sh "$SESSION" 'cat /tmp/debug.txt'
fi
```

## Output Validation Pattern

```bash
#!/bin/bash

# Run command and validate output
RESULT=$(./scripts/tmux-exec.sh "session:window.pane" 'gh api repos/owner/repo')
RC=$?

# Check exit code
if [ $RC -ne 0 ]; then
  echo "Command failed with exit code $RC"
  exit 1
fi

# Check if output looks like JSON
if ! echo "$RESULT" | jq empty 2>/dev/null; then
  echo "Output is not valid JSON"
  echo "Received: ${RESULT:0:200}"
  exit 1
fi

# Check if output is empty
if [ -z "$RESULT" ]; then
  echo "Command produced no output"
  exit 1
fi

# If all checks pass
echo "Output is valid and non-empty"
echo "$RESULT" | jq .
```

## Prevention Tips

1. **Always test with echo first**: Verify pane responds to basic commands
2. **Check environment upfront**: Ensure required tools and credentials exist
3. **Use file redirects for large output**: Avoid tmux line limits
4. **Add explicit error handling**: Capture both stdout and stderr
5. **Log operations**: Keep audit trail of what was attempted
6. **Use separate debug pane**: Allocate pane just for debugging if available
7. **Monitor pane state**: Check if pane is still active before each operation

## References

- [Tmux Manual](https://man7.org/linux/man-pages/man1/tmux.1.html)
- [Tmux capture-pane](https://man7.org/linux/man-pages/man1/tmux.1.html#capture-pane)
- [Tmux send-keys](https://man7.org/linux/man-pages/man1/tmux.1.html#send-keys)
