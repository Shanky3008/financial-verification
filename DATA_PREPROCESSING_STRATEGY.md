# Data Pre-Processing & Normalization Strategy

## Executive Summary

Implementing a comprehensive data preprocessing pipeline to handle edge cases,
ensure data quality, and prevent false matches/mismatches in financial verification.

---

## Problem Categories

### 1. Lines Without Amounts

**Examples:**
```
Line Item                          FY 2024    FY 2023
=====================================
ASSETS                              -          -        ← Section header
  Property, Plant & Equipment    100,000    80,000     ← Data line
  Total Non-Current Assets       150,000   120,000     ← Subtotal
```

**Issues:**
- Headers should not be compared as line items
- Null amounts could indicate missing data OR headers
- Ambiguity between "0" and "no amount"

**Solution:**
```python
def classify_line_type(line_item, amount, original_text):
    """
    Classify each line as: HEADER, SUBTOTAL, TOTAL, LINE_ITEM, NOTE

    Returns:
        - LINE_ITEM: Actual line item with amount
        - HEADER: Section/category header (ASSETS, LIABILITIES)
        - SUBTOTAL: Intermediate sum (Total Current Assets)
        - TOTAL: Grand total (Total Assets, Total Liabilities & Equity)
        - NOTE: Reference or footnote
        - UNKNOWN: Cannot determine
    """

    # Check if amount is missing
    if pd.isna(amount) or amount is None:
        # Check if it's a section header
        if is_section_header(line_item):
            return "HEADER"
        # Check if it's a note reference
        if is_note_reference(line_item):
            return "NOTE"
        return "UNKNOWN"

    # Has amount - check if it's a total/subtotal
    if is_total_line(line_item):
        return "TOTAL"
    if is_subtotal_line(line_item):
        return "SUBTOTAL"

    # Regular line item
    return "LINE_ITEM"
```

### 2. Hierarchical Structure

Financial statements have hierarchy:

```
Level 1: ASSETS
  Level 2: Non-Current Assets
    Level 3: Property, Plant & Equipment
      Level 4: Land                    10,000
      Level 4: Buildings               50,000
      Level 4: Machinery               40,000
    Level 3: Total PPE                100,000  ← Sum of Level 4
  Level 2: Total Non-Current Assets   150,000  ← Sum of Level 3
Level 1: Total Assets                 500,000  ← Sum of Level 2
```

**Issues:**
- Different indentation levels
- Totals calculated from sub-items
- Need to preserve hierarchy for validation

**Solution:**
```python
@dataclass
class FinancialLineItem:
    description: str
    amount: Optional[float]
    line_type: str  # HEADER, LINE_ITEM, SUBTOTAL, TOTAL
    level: int  # Indentation/hierarchy level
    parent: Optional[str]  # Parent item name
    children: List[str]  # Child item names
    is_calculated: bool  # True if it's a sum of other items
    calculation_formula: Optional[str]  # e.g., "sum(line_15:line_20)"
```

### 3. Different Presentation Formats

Companies may restructure statements between years:

**FY 2023:**
```
Current Assets
  Inventories                     50,000
  Trade Receivables              30,000
  Total Current Assets           80,000
```

**FY 2024:**
```
Current Assets
  Inventories
    Raw Materials                 20,000
    Finished Goods                30,000
  Subtotal Inventories            50,000
  Trade Receivables              30,000
  Total Current Assets           80,000
```

**Solution:**
- Flexible matching at multiple hierarchy levels
- Option to compare totals vs detailed items
- Flag restructuring for manual review

---

## Proposed Pre-Processing Pipeline

### Stage 1: Data Extraction & Cleaning

```python
def extract_and_clean(file, file_type, extract_column):
    """
    Extract data with comprehensive cleaning

    Returns: List[RawLineItem]
    """
    # 1. Extract raw data
    raw_data = extract_raw_data(file, file_type)

    # 2. Detect encoding issues
    raw_data = fix_encoding(raw_data)

    # 3. Normalize text
    for item in raw_data:
        item.description = normalize_description(item.description)

    # 4. Parse amounts with validation
    for item in raw_data:
        item.amount = parse_and_validate_amount(item.amount_raw)

    # 5. Detect currency and convert if needed
    currency = detect_currency(raw_data)
    if currency != "default":
        convert_currency(raw_data, currency, "default")

    return raw_data
```

### Stage 2: Structure Detection

```python
def detect_structure(raw_data):
    """
    Detect document structure and classify line types

    Returns: List[StructuredLineItem]
    """
    structured_data = []

    for item in raw_data:
        # Detect indentation level
        level = detect_indentation_level(item.description)

        # Classify line type
        line_type = classify_line_type(
            item.description,
            item.amount,
            item.original_text
        )

        # Build hierarchy
        parent = find_parent(structured_data, level)

        structured_item = StructuredLineItem(
            description=item.description,
            amount=item.amount,
            line_type=line_type,
            level=level,
            parent=parent,
            original_text=item.original_text
        )

        structured_data.append(structured_item)

    return structured_data
```

### Stage 3: Validation & Cross-Checking

```python
def validate_structure(structured_data):
    """
    Validate mathematical relationships and data integrity

    Returns: (validated_data, warnings)
    """
    warnings = []

    # 1. Check totals match sum of components
    for item in structured_data:
        if item.line_type in ["TOTAL", "SUBTOTAL"]:
            expected = calculate_sum_of_children(item, structured_data)
            actual = item.amount

            if abs(expected - actual) > 0.01:
                warnings.append(
                    f"⚠️ {item.description}: "
                    f"Total ({actual:,.2f}) != Sum of components ({expected:,.2f})"
                )

    # 2. Check balance sheet balances
    assets = get_total_by_category(structured_data, "Total Assets")
    liabilities = get_total_by_category(structured_data, "Total Liabilities")
    equity = get_total_by_category(structured_data, "Total Equity")

    if assets and liabilities and equity:
        if abs(assets - (liabilities + equity)) > 0.01:
            warnings.append(
                "⚠️ Balance Sheet does not balance: "
                f"Assets ({assets:,.2f}) != Liabilities + Equity ({liabilities + equity:,.2f})"
            )

    # 3. Check for duplicate line items
    descriptions = [item.description for item in structured_data
                    if item.line_type == "LINE_ITEM"]
    duplicates = find_duplicates(descriptions)
    if duplicates:
        warnings.append(f"⚠️ Duplicate line items found: {duplicates}")

    return structured_data, warnings
```

### Stage 4: Normalization to Standard Format

```python
def normalize_to_standard_format(structured_data):
    """
    Convert to standardized format for comparison

    Standard Format:
    - Consistent naming (e.g., "PPE" -> "Property, Plant & Equipment")
    - Consistent grouping
    - Consistent hierarchy levels
    """

    # 1. Apply name normalization rules
    name_mapping = {
        "PPE": "Property, Plant & Equipment",
        "Trade Receivables": "Accounts Receivable - Trade",
        "Cash & Bank": "Cash and Cash Equivalents",
        # ... comprehensive mapping
    }

    for item in structured_data:
        normalized = normalize_line_item_name(item.description, name_mapping)
        item.description_normalized = normalized

    # 2. Standardize hierarchy
    standardized = reorganize_to_standard_hierarchy(structured_data)

    return standardized
```

### Stage 5: Filtering for Comparison

```python
def prepare_for_comparison(normalized_data, include_totals=False):
    """
    Filter and prepare data for comparison

    Args:
        include_totals: Whether to include TOTAL/SUBTOTAL lines

    Returns: List[ComparableLineItem]
    """
    comparable = []

    for item in normalized_data:
        # Skip headers and notes
        if item.line_type in ["HEADER", "NOTE"]:
            continue

        # Optionally skip totals
        if not include_totals and item.line_type in ["TOTAL", "SUBTOTAL"]:
            continue

        # Must have valid amount
        if item.amount is None or pd.isna(item.amount):
            continue

        # Must be from relevant statement
        if not is_relevant_statement(item):
            continue

        comparable.append(item)

    return comparable
```

---

## Enhanced Line Item Classification

### Header Detection (Improved)

```python
def is_section_header(text: str) -> bool:
    """Enhanced header detection"""

    # Common section headers
    section_headers = [
        # Balance Sheet
        r"^ASSETS?$",
        r"^LIABILITIES?$",
        r"^EQUITY$",
        r"^SHAREHOLDERS?' EQUITY$",
        r"^NON[- ]?CURRENT ASSETS?$",
        r"^CURRENT ASSETS?$",
        r"^NON[- ]?CURRENT LIABILITIES?$",
        r"^CURRENT LIABILITIES?$",

        # Income Statement
        r"^INCOME STATEMENT$",
        r"^REVENUE$",
        r"^EXPENSES?$",
        r"^OTHER INCOME$",
        r"^FINANCE COSTS?$",

        # Cash Flow
        r"^CASH FLOWS? FROM",
        r"^OPERATING ACTIVITIES$",
        r"^INVESTING ACTIVITIES$",
        r"^FINANCING ACTIVITIES$",

        # Generic
        r"^PARTICULARS?$",
        r"^DESCRIPTION$",
        r"^NOTE$",
        r"^\d+\.\s*[A-Z]",  # "1. SHARE CAPITAL"
    ]

    text_clean = text.strip().upper()

    for pattern in section_headers:
        if re.match(pattern, text_clean):
            return True

    # Check if all caps and < 5 words (likely header)
    if text_clean == text.strip() and len(text.split()) <= 5:
        return True

    return False
```

### Total/Subtotal Detection

```python
def is_total_line(text: str) -> bool:
    """Detect total lines"""

    total_patterns = [
        r"^TOTAL",
        r"^GRAND TOTAL",
        r"TOTAL$",
        r"^NET\s+",  # Net Assets, Net Profit
        r"^GROSS\s+",  # Gross Profit, Gross Assets
    ]

    text_upper = text.upper().strip()

    for pattern in total_patterns:
        if re.search(pattern, text_upper):
            return True

    return False

def is_subtotal_line(text: str) -> bool:
    """Detect subtotal lines"""

    subtotal_patterns = [
        r"^SUB[- ]?TOTAL",
        r"^TOTAL\s+[A-Z]",  # Total Current Assets
        r"^AGGREGATE",
    ]

    text_upper = text.upper().strip()

    for pattern in subtotal_patterns:
        if re.search(pattern, text_upper):
            return True

    return False
```

### Note Reference Detection

```python
def is_note_reference(text: str) -> bool:
    """Detect note references"""

    note_patterns = [
        r"^NOTE\s+\d+",  # "Note 15"
        r"^SEE NOTE",
        r"^\d+\s*$",  # Just a number (likely note reference)
        r"^AS PER",
        r"^REFER",
    ]

    text_upper = text.upper().strip()

    for pattern in note_patterns:
        if re.match(pattern, text_upper):
            return True

    return False
```

---

## Amount Parsing & Validation

### Robust Amount Parser

```python
def parse_and_validate_amount(amount_raw: Any) -> Optional[float]:
    """
    Parse amount with comprehensive validation

    Handles:
    - Different number formats (1,234.56 vs 1.234,56)
    - Negative indicators ((1000), -1000, 1000-, 1000 DR)
    - Currency symbols ($, £, ₹, €)
    - Words (thousand, million, crore, lakh)
    - Scientific notation (1.23e6)
    """

    if pd.isna(amount_raw) or amount_raw == '' or amount_raw == '-':
        return None

    text = str(amount_raw).strip()

    # 1. Check for text indicators
    is_negative = False

    # Debit/Credit notation
    if text.upper().endswith(' DR') or text.upper().endswith(' DEBIT'):
        is_negative = True
        text = re.sub(r'\s+(DR|DEBIT)$', '', text, flags=re.IGNORECASE)
    if text.upper().endswith(' CR') or text.upper().endswith(' CREDIT'):
        text = re.sub(r'\s+(CR|CREDIT)$', '', text, flags=re.IGNORECASE)

    # Parentheses for negatives: (1000)
    if text.startswith('(') and text.endswith(')'):
        is_negative = True
        text = text[1:-1]

    # 2. Remove currency symbols
    text = re.sub(r'[$£₹€¥]', '', text)

    # 3. Handle word multipliers
    multiplier = 1.0
    text_upper = text.upper()

    if 'CRORE' in text_upper or 'CR' in text_upper:
        multiplier = 10000000  # 1 crore = 10 million
        text = re.sub(r'\s*(CRORE|CR)\s*', '', text, flags=re.IGNORECASE)
    elif 'LAKH' in text_upper or 'LAC' in text_upper:
        multiplier = 100000  # 1 lakh = 100 thousand
        text = re.sub(r'\s*(LAKH|LAC)\s*', '', text, flags=re.IGNORECASE)
    elif 'MILLION' in text_upper or 'MN' in text_upper:
        multiplier = 1000000
        text = re.sub(r'\s*(MILLION|MN)\s*', '', text, flags=re.IGNORECASE)
    elif 'THOUSAND' in text_upper or 'K' in text_upper:
        multiplier = 1000
        text = re.sub(r'\s*(THOUSAND|K)\s*', '', text, flags=re.IGNORECASE)

    # 4. Normalize number format
    # Detect format: US (1,234.56) vs European (1.234,56)
    if ',' in text and '.' in text:
        # Both present - determine which is decimal separator
        last_comma = text.rfind(',')
        last_dot = text.rfind('.')

        if last_dot > last_comma:
            # US format: 1,234.56
            text = text.replace(',', '')
        else:
            # European format: 1.234,56
            text = text.replace('.', '').replace(',', '.')
    elif ',' in text:
        # Only comma - check if it's thousands separator or decimal
        if text.count(',') > 1:
            # Multiple commas = thousands separator: 1,234,567
            text = text.replace(',', '')
        else:
            # Single comma - check position
            parts = text.split(',')
            if len(parts[1]) == 3:
                # Likely thousands: 1,000
                text = text.replace(',', '')
            else:
                # Likely decimal: 123,45
                text = text.replace(',', '.')

    # 5. Parse to float
    try:
        amount = float(text) * multiplier

        # 6. Validate
        import math

        if math.isinf(amount):
            raise ValueError("Amount is infinity")

        if math.isnan(amount):
            return None

        # Check reasonable range (adjust as needed)
        if abs(amount) > 1e15:  # 1 quadrillion
            logging.warning(f"Extremely large amount: {amount:,.2f}")

        # Apply negative if needed
        if is_negative:
            amount = -amount

        return amount

    except ValueError as e:
        logging.warning(f"Could not parse amount: {amount_raw} - {e}")
        return None
```

---

## Comparison Strategy

### Multi-Level Matching

```python
def match_with_preprocessing(cy_data, py_data):
    """
    Match with full preprocessing pipeline
    """

    # Stage 1: Preprocess both files
    cy_processed = preprocess_pipeline(cy_data)
    py_processed = preprocess_pipeline(py_data)

    # Stage 2: Filter for comparison (exclude headers, totals)
    cy_comparable = prepare_for_comparison(cy_processed, include_totals=False)
    py_comparable = prepare_for_comparison(py_processed, include_totals=False)

    # Stage 3: Match line items
    matches = match_line_items(cy_comparable, py_comparable)

    # Stage 4: Validate totals separately (if needed)
    total_validations = validate_totals(cy_processed, py_processed)

    # Stage 5: Check for missing items
    missing_items = find_missing_items(cy_comparable, py_comparable, matches)

    return {
        'matches': matches,
        'total_validations': total_validations,
        'missing_items': missing_items,
        'warnings': cy_processed.warnings + py_processed.warnings
    }
```

---

## Recommended Implementation Priority

### Phase 1 (Critical - 2-3 days):
1. ✅ Robust amount parsing (handle all formats)
2. ✅ Enhanced header detection
3. ✅ Skip lines without amounts
4. ✅ Line type classification (HEADER vs LINE_ITEM vs TOTAL)

### Phase 2 (Important - 3-4 days):
5. Hierarchy detection
6. Validation of totals/subtotals
7. Duplicate detection
8. Balance sheet balancing check

### Phase 3 (Nice to have - 1 week):
9. Name normalization/standardization
10. Currency detection and conversion
11. Flexible matching for restructured statements
12. Machine learning for intelligent classification

---

## Configuration Options for Users

```python
class VerificationConfig:
    """User-configurable options"""

    # What to compare
    include_totals: bool = False  # Compare total lines?
    include_subtotals: bool = False  # Compare subtotal lines?
    include_schedules: bool = True  # Compare schedule/note items?

    # Matching behavior
    similarity_threshold: float = 0.85  # Fuzzy matching threshold
    amount_tolerance: float = 0.01  # Tolerance in currency units

    # Validation checks
    validate_balance_sheet: bool = True  # Check Assets = Liabilities + Equity
    validate_totals: bool = True  # Check totals match sum of items
    flag_duplicates: bool = True  # Warn on duplicate items

    # Display options
    group_by_statement: bool = True  # Group results by statement type
    show_only_mismatches: bool = False  # Hide matches?
    show_warnings: bool = True  # Display warnings?
```

---

## Summary

**Key Improvements Needed:**

1. **Line Classification**: Distinguish HEADER vs LINE_ITEM vs TOTAL vs NOTE
2. **Amount Parsing**: Handle all number formats, currencies, word multipliers
3. **Validation**: Check mathematical relationships (totals, balance)
4. **Hierarchy**: Preserve and use document structure
5. **Normalization**: Standardize names and formats
6. **Filtering**: Only compare actual line items, not headers/totals

**Expected Benefits:**

- ✅ Eliminate false matches on headers
- ✅ Catch mathematical errors in source documents
- ✅ Handle restructured statements
- ✅ Support international formats
- ✅ Comprehensive data quality checks
- ✅ User-configurable behavior
