# Eval Case 04: Watchlist CRUD operations

## Input
```bash
# Add
python3 run.py --watchlist add --bill-id <VALID_BILL_ID>

# List
python3 run.py --watchlist list --json

# Remove
python3 run.py --watchlist remove --bill-id <VALID_BILL_ID>

# List again
python3 run.py --watchlist list --json
```

## Acceptance Criteria
- [ ] Add reports success; bill appears in list
- [ ] List returns JSON array with bill details
- [ ] Each tracked bill has: bill_id, number, title, state, status, added_at
- [ ] Remove reports success; bill no longer in list
- [ ] Adding same bill twice does not create duplicate
- [ ] watchlist.json exists in cache directory
