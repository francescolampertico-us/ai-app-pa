# Eval Case 05: Error handling

## Input
```bash
# No API key
LEGISCAN_API_KEY="" python3 run.py --query "test"

# Invalid bill ID
python3 run.py --bill-id 9999999999 --summarize

# No arguments
python3 run.py
```

## Acceptance Criteria
- [ ] Missing API key produces clear error message (not a stack trace)
- [ ] Invalid bill ID produces informative error (not crash)
- [ ] No arguments prints usage help and exits with non-zero code
- [ ] No unhandled exceptions in any error case
