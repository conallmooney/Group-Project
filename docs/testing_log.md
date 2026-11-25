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
| 12 | 22 Nov | Hannah | 2 | Ran the full dashboard (app.py) on my laptop | All panels load | Crashed at Panel 2 with StreamlitSecretNotFoundError (no FRED API key), so the panels after it didn't load | Fail | Eoin adding a saved CSV fallback in data/fallback/ for when there's no key |
| 13 | 22 Nov | Hannah | all | Checked which panels app.py draws | All four panels shown | Only Panel 2 was imported and drawn; Panels 1, 3 and 4 missing | Fail | Eoin adding all four render() calls in order 1–4 |
| 14 | 22 Nov | Hannah | 4 | Changed the scenario's inflation in the full dashboard | Panel 4 inflation slider updates | Slider stayed at 3.50 (Streamlit remembered the old slider value) | Fail → Fixed | Reset the slider whenever the scenario's inflation changes (st.session_state) |
| 15 | 22 Nov | Hannah | 3→4 | Chose "My Panel 3 portfolio" with a portfolio built in Panel 3 | Panel 4 uses Panel 3's funds | Blue "hasn't built a portfolio" box still showed; the p3_result code was on Conall's branch but not merged into main | Fail → Fixed | Conall's panel_c PR merged into main; Panel 4 now uses Panel 3's portfolio |
| 16 | 22 Nov | Hannah | 2 | Turned Wi-Fi off, reran the full dashboard and pressed Calculate Sensitivities | All panels work from saved data | Panels 1, 3 and 4 used saved data; Panel 2 crashed with ValueError: No ETF price data was downloaded | Fail → Fixed |Eoin added saved-data fallbacks (ETF prices and Treasury yields); all four panels now work offline |
| 17 | 22 Nov | Hannah | 2 | Known-answer tests for Panel 2's calculate_sensitivities (fake ETF that moves exactly -2 per 1-point yield change; and a 10-row history) | Beta -2, Alpha 0.5, R² 1; short history skipped | All matched; 23 tests pass | Pass | - |
| 18 | 25 Nov | Eoin | all | Ran pytest after merging latest main into panel_b | All 23 tests pass | ModuleNotFoundError from an obsolete local test file referencing interest_rate_model_b.py | Fail → Fixed | Ran python -m pytest tests/ -v to exclude the obsolete untracked file |
| 19 | 25 Nov | Eoin | all | Ran all 23 official automated tests on Windows (Python 3.13.14) | All pass | 23 passed in 4.26 seconds, including both Panel 2 known-answer tests | Pass | – |
| 20 | 24 Nov | Lecturer | all | Ran the dashboard and tests on the lecturer's Mac | Everything loads and passes | Setup problems on that machine: SciPy failed to load, and packages were installed into a different Python from the one running the tests | Fail → Fixed | Setup steps in README and user manual now use a virtual environment and python -m; confirmed by a fresh clone and setup (row 22) |
| 21 | 25 Nov | Hannah | 4 | Set Custom scenario inflation to 1.25 | Panel 4 shows 1.25 | Showed 1.20 (slider rounded to one decimal) | Fail → Fixed | Two decimals and step 0.05 |
| 22 | 25 Nov | Hannah | all | Fresh clone into a new folder, new virtual environment, followed the README setup steps | Install succeeds, tests pass, dashboard loads | All 23 tests passed; all four panels loaded | Pass | – |


## Full dashboard test plan (run after all panels are merged)

| Check | Expected result | Passed? |
|---|---|---|
| Run `streamlit run app.py` | Dashboard loads with no red errors | Fail at first (rows 12–13); Pass after Eoin's fix |
| Change the scenario | Panel 4's inflation slider changes to match (3.5 shows as 3.50) | Fail at first (row 14); Pass after fix |
| Build a portfolio in Panel 3, pick "My Panel 3 portfolio" in Panel 4 | Blue box disappears, captions name Panel 3's funds | Fail at first (row 15); Pass after Conall's PR |
| Look at each panel's heading | Each title appears only once | Fail at first (Panel 4 repeated "Panel 4"); Pass after shortening Panel 4's heading |
| Panel 4: monthly 0, years 5, goal 0 | No crash, sensible numbers | Pass |
| Turn Wi-Fi off and reload | Still works using the saved CSV backups | Fail at first (row 16); Pass after Eoin's fix – all four panels work offline |
