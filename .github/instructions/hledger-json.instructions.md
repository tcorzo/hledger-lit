---
applyTo: "hledger_lit/hledger.py"
description: "Use when parsing hledger JSON output, adding new hledger commands, or debugging JSON field access. Documents the two hledger JSON response schemas."
---

# hledger JSON Schema Reference

hledger produces two JSON formats depending on the command. Both use `-O json`.

## Historical Balance Report (`balance --historical -O json`)

Used by `HledgerRunner.run_historical_command()`.

```
{
  "prDates": [                          # list of periods
    [{"contents": "2024-01-01"}],       # each period = list with one object
    [{"contents": "2024-02-01"}]
  ],
  "prRows": [                          # one row per account
    {
      "prrName": "assets:checking",    # full hierarchical account name
      "prrAmounts": [                  # one entry per period (parallel to prDates)
        [                              # each period = list of amounts (multi-commodity)
          {
            "acommodity": "£",
            "aquantity": {"floatingPoint": 1000.0}
          }
        ]
      ]
    }
  ]
}
```

Key access patterns:
- Dates: `data["prDates"][i][0]["contents"]`
- Account name: `row["prrName"]`
- Amount for commodity: find `amt` in `row["prrAmounts"][period_idx]` where `amt["acommodity"] == commodity`, then `amt["aquantity"]["floatingPoint"]`

## Current Balance Report (`balance -O json`)

Used by `HledgerRunner.read_current_balances()`.

```
[
  [                                     # first element = list of account entries
    [
      "expenses:food",                  # [0] account name (str)
      0,                                # [1] unused
      0,                                # [2] unused
      [                                 # [3] list of amounts
        {
          "acommodity": "£",
          "aquantity": {"floatingPoint": 300.0}
        }
      ]
    ]
  ]
]
```

Key access patterns:
- Accounts list: `data[0]`
- Account name: `entry[0]`
- Amounts: `entry[3]` (may be empty → default to `0.0`)
- Balance: `entry[3][0]["aquantity"]["floatingPoint"]`

## Common Amount Object

Both formats share the same amount structure:

| Field | Type | Description |
|-------|------|-------------|
| `acommodity` | `str` | Currency/commodity symbol (e.g. `"£"`, `"$"`, `"EUR"`) |
| `aquantity.floatingPoint` | `float` | Numeric value of the amount |
