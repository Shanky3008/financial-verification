# Excel File Support Documentation

## Overview
The CSV/Excel tab now accepts both CSV and Microsoft Excel files (.xlsx, .xls), providing more flexibility for financial data input.

## New Features

### 1. File Format Support
**Supported formats**:
- `.csv` - Comma-separated values
- `.xlsx` - Excel 2007+ format
- `.xls` - Excel 97-2003 format

### 2. Multi-Sheet Excel Support
**Automatic sheet detection**:
- Detects all visible sheets in Excel workbook
- Automatically skips hidden sheets
- Single-sheet files: Uses first sheet automatically
- Multi-sheet files: Provides dropdown to select sheet

**Sheet selection UI**:
```
Select sheet (Current Year): [▼ Balance Sheet]
                              [  Income Statement]
                              [  Cash Flow]
```

### 3. Preview Functionality
- Works for both CSV and Excel files
- Shows first 5 rows of data
- Displays selected sheet for Excel files
- Updates dynamically when sheet selection changes

## Implementation Details

### New Functions

#### `get_excel_sheets(uploaded_file)`
**Location**: app.py:502-513

Extracts list of visible sheet names from Excel workbook.

**Logic**:
1. Opens Excel file in read-only mode
2. Gets all sheet names
3. Filters out hidden sheets
4. Returns list of visible sheet names

**Returns**: List of sheet names or empty list if error

**Example**:
```python
sheets = get_excel_sheets(excel_file)
# Returns: ['Balance Sheet', 'Income Statement', 'Cash Flow']
```

---

#### `read_file_to_dataframe(uploaded_file, sheet_name=None)`
**Location**: app.py:515-548

Unified function to read both CSV and Excel files into DataFrame.

**Parameters**:
- `uploaded_file`: Streamlit UploadedFile object
- `sheet_name`: Sheet name for Excel (None for CSV or first sheet)

**Logic**:
1. Detects file type by extension
2. CSV: Uses `pd.read_csv()`
3. Excel: Uses `pd.read_excel()` with openpyxl engine
4. Handles errors gracefully

**Returns**: DataFrame or None if error

**Example**:
```python
# CSV file
df = read_file_to_dataframe(csv_file)

# Excel file - first sheet
df = read_file_to_dataframe(excel_file)

# Excel file - specific sheet
df = read_file_to_dataframe(excel_file, sheet_name='Balance Sheet')
```

---

#### `extract_financial_data_csv(uploaded_file, column_to_extract='last', sheet_name=None)`
**Location**: app.py:550-634

Enhanced to support both CSV and Excel files.

**Changes**:
- Added `sheet_name` parameter
- Now uses `read_file_to_dataframe()` instead of `pd.read_csv()`
- All other logic unchanged (parsing, validation, hierarchy detection)

**Backward compatible**: Works with existing CSV files without changes

---

### UI Changes

#### Tab Name
**Before**: "📄 CSV Version"
**After**: "📄 CSV/Excel Version"

#### Header
**Before**: "CSV-Based Comparison"
**After**: "CSV/Excel-Based Comparison"

#### File Uploaders
**Before**:
```python
st.file_uploader("Upload Current Year CSV", type=['csv'])
```

**After**:
```python
st.file_uploader("Upload Current Year File", type=['csv', 'xlsx', 'xls'])
```

#### Sheet Selection (New)
Appears below file uploader when Excel file with multiple sheets is uploaded:
```python
if sheets and len(sheets) > 1:
    cy_sheet_name = st.selectbox(
        "Select sheet (Current Year)",
        sheets,
        key='cy_sheet'
    )
```

#### Preview Enhancement
**Before**: Only worked with CSV
**After**: Works with both CSV and Excel, shows selected sheet

---

## User Workflow

### Single-Sheet Excel File
1. Upload Excel file
2. System detects single sheet
3. Displays: "📄 Using sheet: Balance Sheet"
4. Preview shows data from that sheet
5. Click "Compare" to proceed

### Multi-Sheet Excel File
1. Upload Excel file
2. System detects multiple sheets
3. Dropdown appears: "Select sheet (Current Year)"
4. User selects desired sheet
5. Preview updates to show selected sheet
6. Click "Compare" to proceed

### CSV File
1. Upload CSV file
2. Preview shows data (no sheet selection needed)
3. Click "Compare" to proceed

---

## Technical Details

### Excel Reading Configuration
```python
pd.read_excel(
    uploaded_file,
    sheet_name=sheet_name,
    engine='openpyxl'
)
```

**Settings**:
- `engine='openpyxl'`: Required for .xlsx files
- `data_only=True`: Reads values, not formulas (for sheet detection)
- `read_only=True`: Faster sheet detection

### Hidden Sheet Handling
Hidden sheets are automatically skipped:
```python
sheets = [sheet for sheet in wb.sheetnames if wb[sheet].sheet_state != 'hidden']
```

This prevents users from accidentally selecting hidden working sheets or templates.

### File Type Detection
Uses file extension:
```python
filename.lower().endswith(('.xlsx', '.xls'))  # Excel
filename.lower().endswith('.csv')              # CSV
```

---

## Benefits

### 1. User Convenience
- No need to export Excel to CSV
- Direct upload of financial statements
- Preserves original formatting

### 2. Multi-Sheet Support
- Extract data from specific statement
- Balance Sheet, Income Statement, etc. in separate sheets
- User controls which sheet to compare

### 3. Data Integrity
- Reads values directly from Excel
- Handles formulas correctly (`data_only=True`)
- Skips hidden sheets automatically

### 4. Backward Compatibility
- Existing CSV workflow unchanged
- Same validation and processing
- No breaking changes

---

## Error Handling

### Invalid Excel File
```
❌ Error reading Excel file: [error message]
```

### No Sheets Found
```
❌ Error reading file: [error message]
```

### File Size Validation
Same 50MB limit applies to both CSV and Excel files.

---

## Limitations

### 1. File Size
- Maximum: 50MB per file
- Large Excel files may be slow to process
- Consider exporting to CSV for very large files

### 2. Excel Format Support
- Supports: .xlsx (2007+), .xls (97-2003)
- Does not support: .xlsm (macros), .xlsb (binary)
- Macros are ignored even if present

### 3. Formula Handling
- Reads calculated values, not formulas
- If Excel shows errors (#REF!, #VALUE!), they'll be read as text
- Recommend fixing errors before upload

### 4. Merged Cells
- May cause issues with data extraction
- Best practice: Unmerge cells before upload
- System will try to read first cell of merged range

---

## Testing Recommendations

### Test Cases

1. **Single-sheet Excel (.xlsx)**
   - Upload file with one sheet
   - Verify auto-detection
   - Verify extraction works

2. **Multi-sheet Excel (.xlsx)**
   - Upload file with 3+ sheets
   - Verify dropdown appears
   - Select different sheets, verify preview updates
   - Verify extraction from selected sheet

3. **Legacy Excel (.xls)**
   - Upload .xls file
   - Verify compatibility
   - Verify extraction works

4. **CSV file**
   - Upload CSV file
   - Verify no sheet selection appears
   - Verify existing workflow unchanged

5. **Hidden sheets**
   - Upload Excel with hidden sheets
   - Verify hidden sheets don't appear in dropdown
   - Verify only visible sheets selectable

6. **Large Excel file**
   - Upload 10MB+ Excel file
   - Verify performance acceptable
   - Verify memory usage reasonable

7. **Excel with formulas**
   - Upload Excel with formulas
   - Verify values (not formulas) are read
   - Verify amounts parse correctly

8. **Mixed formats**
   - Upload Excel for Current Year
   - Upload CSV for Previous Year
   - Verify comparison works correctly

---

## Future Enhancements

Potential additions:
1. **Multiple sheet extraction**: Extract and combine data from multiple sheets
2. **Sheet auto-detection**: Automatically identify which sheet is Balance Sheet, Income Statement, etc.
3. **Excel template download**: Provide pre-formatted Excel template
4. **Column mapping UI**: Visual interface to map columns instead of first/last
5. **Excel validation**: Check for merged cells, formulas with errors, etc.

---

## Conclusion

Excel support makes the tool more user-friendly and practical for real-world financial statement verification, eliminating the need for manual CSV conversion while maintaining the same robust validation and comparison logic.
