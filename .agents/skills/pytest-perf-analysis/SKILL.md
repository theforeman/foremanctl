---
name: pytest-perf-analysis
description: Analyze pytest timing output to diagnose slow tests and fixtures, then produce ranked optimization recommendations. Use this skill whenever the user pastes pytest duration output, asks "why are my tests slow", shows a pytest timing report, or wants to speed up their test suite. Also trigger when the user completes a test run and mentions slow tests, fixture overhead, or setup/teardown time.
---

# pytest Performance Analysis

Analyze pytest timing data and the associated fixture/test code to identify root causes of slowness and produce concrete, ranked recommendations.

## Input

Accept timing data in any of these forms — detect which one the user provided:

1. **Pasted output** — pytest's `--durations`, `--fixture-durations`, or the combined summary block. Parse directly from the conversation. See `references/fixture-antipatterns.md` for the format variants to expect.
2. **File path** — a saved pytest log or JUnit XML file. Read it.
3. **No data** — run pytest to generate it:
   ```bash
   python -m pytest --durations=20 --fixture-durations=20 -q 2>&1 | tee /tmp/pytest-timing.txt
   ```
   Then parse `/tmp/pytest-timing.txt`.

If the user provides partial output (e.g., only the fixture table or only the test table), proceed with what's available and note what's missing.

## Analysis Process

Read `references/fixture-antipatterns.md` before starting — it contains the specific patterns to look for, expected speedups, and the output format variants you will encounter.

### Step 1: Extract the slow items

From the timing data, build two ranked lists:
- Top slow **fixtures** by total time (fixture duration table)
- Top slow **tests** by call time (test call duration table)

Focus analysis on anything consuming more than 5% of total runtime, or more than 10 seconds individually.

### Step 2: Find the fixture definitions

For each slow fixture, locate its definition:
1. Search `conftest.py` files from the test directory upward (pytest's fixture resolution order)
2. Note the `scope=` parameter — missing scope means function scope (re-created per test)
3. Note the `yield` point — everything before yield is setup, everything after is teardown
4. Count the API/subprocess/SSH calls in setup and teardown separately

For each slow test, read the test file and note which fixtures it requests.

### Step 3: Apply the anti-pattern checklist

For each slow fixture, check each pattern in `references/fixture-antipatterns.md`. Mark which patterns apply. Note the fixture's scope and how many times the timing data shows it ran — that `num` column is the multiplier for the waste.

### Step 4: Check the fixture dependency graph

For fixtures that are slow themselves but also depend on other fixtures, trace the chain:
- How deep is the dependency chain?
- Does a function-scoped fixture depend on another function-scoped fixture? Each layer multiplies the cost.
- If the chain is expensive, lifting the root fixture to module scope benefits the whole chain.

### Step 5: Identify inherently-slow tests

Some tests are irreducibly slow — they restart services, run real backups, boot containers. Check whether:
- They have a slow/expensive marker already
- They are mixed into the default test run
- They could be separated into a dedicated CI stage

## Output Format

ALWAYS produce output using this exact structure:

---

## Root Causes

For each significant slow item:

**`fixture_name` / `test_name`** — `Xs total, N runs`
> One sentence explaining WHY it's slow (not what it does). Reference the specific file and line if possible.
> Anti-patterns: [list which ones from the reference apply]

---

## Recommendations

### High Impact
Each recommendation includes:
- What to change and where (file, line range, or fixture name)
- Why this is slow now
- What the change does
- Estimated time saved (order of magnitude)

### Medium Impact
[same format]

### Low Impact
[same format]

---

## Not Optimizable
List inherently-slow tests with a note on how to isolate them (marker + CI stage).
