# Critical Comparison Logic Issues

## Problem Summary

The tool currently has **ambiguous and potentially incorrect** comparison logic that doesn't match standard accounting practices for comparatives verification.

## Issue 1: What is Being Compared?

### Current Behavior (UNCLEAR):

**Excel/CSV Version:**
- Takes LAST column from both files
- Current Year file → Last column (could be FY 2023 comparative)
- Previous Year file → Last column (could be FY 2022 comparative)
- **Result:** Comparing FY 2023 vs FY 2022 ❌

**LLM/PDF Version:**
- Extracts from column named in `year_label`
- Current Year file → "Current Year" column (FY 2024 actuals)
- Previous Year file → "Previous Year" column (FY 2022 comparative)
- **Result:** Comparing FY 2024 vs FY 2022 ❌

###Correct Accounting Practice (SHOULD BE):

```
Purpose: Verify that comparative figures in current year statements
         match the actual figures from previous year statements

FY 2024 Financial Statements:
├── Line Items
├── Column 2: FY 2024 (Current Year Actual) ← DON'T USE
└── Column 3: FY 2023 (Previous Year Comparative) ← USE THIS ✅

FY 2023 Financial Statements:
├── Line Items
├── Column 2: FY 2023 (Current Year Actual) ← USE THIS ✅
└── Column 3: FY 2022 (Previous Year Comparative) ← DON'T USE

VERIFY: FY 2023 Comparative (from FY 2024 statements)
     == FY 2023 Actual (from FY 2023 statements)
```

## Issue 2: Statement Type Coverage

### Current Status:

| Feature | Balance Sheet | Income Statement | Cash Flow | Notes/Schedules |
|---------|---------------|------------------|-----------|-----------------|
| **LLM/PDF** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Excel** | ✅ Yes (via sheet name) | ✅ Yes (via sheet name) | ✅ Yes (via sheet name) | ✅ Yes (any sheet) |
| **CSV** | ❌ No (all labeled "CSV Data") | ❌ No | ❌ No | ❌ No |

### Recommendation:
- **Excel:** Already works perfectly - uses actual sheet names ✅
- **LLM/PDF:** Should add "Notes" and "Schedules" to extraction ⚠️
- **CSV:** Add column or user input for statement type ⚠️

## Recommended Fixes

### Fix 1: Add Column Selection UI (HIGH PRIORITY)

```python
with st.sidebar:
    st.markdown("### 📊 Column Configuration")

    st.markdown("**Current Year File:**")
    cy_column = st.radio(
        "Extract from:",
        ["Last Column (PY Comparative)", "Second Column (CY Actual)"],
        index=0,  # Default to PY comparative
        key="cy_col"
    )

    st.markdown("**Previous Year File:**")
    py_column = st.radio(
        "Extract from:",
        ["Second Column (CY Actual)", "Last Column (PY Comparative)"],
        index=0,  # Default to CY actual
        key="py_col"
    )
```

### Fix 2: Update Excel Parsing Logic

```python
def parse_excel_with_column_choice(self, file_path: str, column_choice: str) -> List[LineItem]:
    """
    Extract line items with specific column selection

    Args:
        column_choice: "cy_actual" or "py_comparative"
    """
    ...
    if column_choice == "cy_actual":
        amount = amounts[0] if len(amounts) >= 1 else None  # First amount column
    else:  # py_comparative
        amount = amounts[-1] if len(amounts) >= 2 else amounts[0]  # Last amount column
```

### Fix 3: Update LLM Prompts

```python
# For Current Year file:
prompt = f"""Extract ONLY from the PREVIOUS YEAR COMPARATIVE column.
This is typically the rightmost amount column (column 3).
Label: {previous_year_label} (e.g., "2023", "FY2023")
"""

# For Previous Year file:
prompt = f"""Extract ONLY from the CURRENT YEAR column.
This is typically the first amount column (column 2).
Label: {current_year_label} (e.g., "2023", "FY2023")
"""
```

### Fix 4: Clarify UI Labels

Change from ambiguous:
- "Current Year" / "Previous Year"

To explicit:
- "FY 2024 Statements (containing FY 2023 comparatives)"
- "FY 2023 Statements (containing FY 2023 actuals)"

## Testing Scenarios

### Test Case 1: Standard Comparatives Verification
```
Input:
- FY 2024 Statements: Cash = [100,000 (2024), 80,000 (2023 comp)]
- FY 2023 Statements: Cash = [80,000 (2023), 75,000 (2022 comp)]

Expected Output:
- Comparing: 80,000 (2023 comp from 2024) vs 80,000 (2023 actual from 2023)
- Status: MATCH ✅
```

### Test Case 2: Mismatch Detection
```
Input:
- FY 2024 Statements: Revenue = [500,000 (2024), 450,000 (2023 comp)]
- FY 2023 Statements: Revenue = [445,000 (2023), 400,000 (2022 comp)]

Expected Output:
- Comparing: 450,000 vs 445,000
- Status: MISMATCH ❌
- Difference: 5,000
```

## Decision Required

**Before implementing fixes, please confirm:**

1. **Primary Use Case:**
   - [ ] Verify PY comparatives (in CY statements) match PY actuals (in PY statements) ← Standard practice
   - [ ] Compare CY actuals vs PY actuals (year-over-year analysis) ← Different purpose
   - [ ] Other: _______________

2. **Column Flexibility:**
   - [ ] Add UI for column selection (recommended)
   - [ ] Use fixed logic (last column vs first column)
   - [ ] Auto-detect based on column headers

3. **Statement Type Priority:**
   - [ ] Balance Sheet, P&L, Cash Flow only
   - [ ] Include all schedules and notes
   - [ ] User customizable

## Impact Assessment

**If not fixed:**
- ❌ Incorrect verification results
- ❌ False matches/mismatches
- ❌ Cannot be used for audit purposes
- ❌ Misleading stakeholders

**Severity:** 🔴 CRITICAL - Affects core functionality
**Estimated Fix Time:** 4-6 hours
**Testing Required:** Full regression with real financial statements
