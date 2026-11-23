# Testing log

Everyone adds a row when they test something, especially when it breaks

| # | Date | Tester | Panel | What we tried | Expected | What happened | Result | Fix |
|---|------|--------|-------|---------------|----------|---------------|--------|-----|
| 1 | 6 Nov | Hannah | 4 | Ran pytest on the first three Panel 4 tests | All Pass | 3 passed | Pass | - | 
| 2 | 6 Nov | Hannah | 4 | Ran one random future with 0 volatility | Same as fixed-return result (166,668.31) | Matched exactly | Pass | - |
| 3 | 20 Nov | Hannah | 1 | Ran Ciara's PR #4 locally for review | Panel loads | ModuleNotFoundError: scipy | Fixed | Installed from requirements.txt (scipy was listed) |
| 4 | 20 Nov | Hannah | 3 | Known-answer test for Panel 3's Sharpe ratio (10% return, 20% vol, 2% risk-free) | Sharpe = 0.4 | 0.4 | Pass | – |
| 5 | 20 Nov | Hannah | all | Merged main into panel_d | Merges cleanly | Conflict in .gitignore; a line on main was broken (two entries joined) | Fixed | Kept both sets of rules, fixed the broken line; 18 tests pass |
| 6 | 20 Nov | Hannah | 4 | Ran Panel 4 after merging Ciara's new data.py | Page loads | TypeError: load_world_bank() now returns (table, note) | Fixed | Unpacked the two values before use |
| 7 | 21 Nov | Conall (review) | 4 | Passed Panel 2's scenario inflation (3.5 = 3.5%) to Panel 4 | Slider starts at 3.5% | Read as 350%, outside the slider's range, crash | Fixed | scenario_inflation() divides by 100; test added; slider shows 3.50 |
| 8 | 21 Nov | Conall (review) | 4 | Used Panel 3's expected return (annualised arithmetic mean) | Same monthly return in both panels | Panel 4 treated it as compound, slightly different | Fixed | compound_annual_return() converts it; test added |
| 9 | 21 Nov | Conall (review) | 4 | Bootstrapped a Panel 3 portfolio | Uses Panel 3's estimation dates | Used all months since 2015 | Fixed | Loads prices over Panel 3's estimation window; checked with a pretend p3_result |
| 10 | 21 Nov | Hannah | 4 | Picked "My Panel 3 portfolio" with Panel 3 not run | Message, quiz used, no crash | As expected | Pass | – |
| 11 | 21 Nov | Hannah | 4 | Gave every Panel 4 control a unique key (p4_...) | No clash when panels share a page | Page works as before; 21 tests pass | Pass | Prevents errors in app.py |
