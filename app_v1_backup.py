"""
Financial Statements Comparatives Verification Tool - Web UI
Built with Streamlit for easy web deployment
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from io import BytesIO
from comparatives_verification_tool import (
    FinancialStatementParser,
    ComparativesVerifier,
    ReportGenerator
)

# Page configuration
st.set_page_config(
    page_title="Financial Statements Comparatives Verification",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">📊 Financial Statements Comparatives Verification Tool</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Automatically verify comparative figures in your financial statements</p>', unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.markdown("---")
    st.subheader("Matching Settings")
    
    similarity_threshold = st.slider(
        "Text Similarity Threshold",
        min_value=0.5,
        max_value=1.0,
        value=0.85,
        step=0.05,
        help="How closely text descriptions must match (0.5 = lenient, 1.0 = exact)"
    )
    
    st.info("💰 **Amount Matching**: Amounts must match exactly to the last paisa/cent. Any difference will be flagged as a mismatch.")

    # Amount tolerance fixed at 0 - exact match required
    amount_tolerance = 0.0
    
    st.markdown("---")
    st.subheader("📖 About")
    st.info("""
    This tool compares:
    - **Current Year's** comparative figures
    - **Previous Year's** actual figures
    
    It identifies:
    - ✅ Matches (Green)
    - ⚠️ Mismatches (Yellow)
    - ➕ Added items (Red)
    - ➖ Deleted items (Red)
    """)

# Main content
tab1, tab2, tab3 = st.tabs(["📤 Upload & Verify", "📊 Results", "ℹ️ Help"])

with tab1:
    st.header("Upload Financial Statements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Current Year")
        st.caption("Financial statements with previous year comparatives")
        st.markdown("_Example: FY 2025 statements showing FY 2024 comparatives_")
        current_year_file = st.file_uploader(
            "Upload current year financial statements",
            type=['pdf', 'xlsx', 'xls'],
            key='current'
        )
        if current_year_file:
            st.success(f"✅ {current_year_file.name}")

    with col2:
        st.subheader("📅 Previous Year")
        st.caption("Actual financial statements to verify against")
        st.markdown("_Example: FY 2024 actual statements_")
        previous_year_file = st.file_uploader(
            "Upload previous year financial statements",
            type=['pdf', 'xlsx', 'xls'],
            key='previous'
        )
        if previous_year_file:
            st.success(f"✅ {previous_year_file.name}")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        verify_button = st.button(
            "🔍 Verify Comparatives",
            type="primary",
            use_container_width=True,
            disabled=(current_year_file is None or previous_year_file is None)
        )
    
    if verify_button:
        with st.spinner("Processing... Please wait."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    current_path = os.path.join(tmpdir, current_year_file.name)
                    with open(current_path, 'wb') as f:
                        f.write(current_year_file.getvalue())
                    
                    previous_path = os.path.join(tmpdir, previous_year_file.name)
                    with open(previous_path, 'wb') as f:
                        f.write(previous_year_file.getvalue())
                    
                    progress_bar = st.progress(0)
                    parser = FinancialStatementParser()
                    
                    if current_year_file.name.endswith(('.xlsx', '.xls')):
                        current_items = parser.parse_excel(current_path)
                    else:
                        current_items = parser.parse_pdf(current_path)
                    progress_bar.progress(33)
                    
                    if previous_year_file.name.endswith(('.xlsx', '.xls')):
                        previous_items = parser.parse_excel(previous_path)
                    else:
                        previous_items = parser.parse_pdf(previous_path)
                    progress_bar.progress(66)
                    
                    verifier = ComparativesVerifier(
                        similarity_threshold=similarity_threshold,
                        amount_tolerance=amount_tolerance
                    )
                    results = verifier.verify(current_items, previous_items)
                    progress_bar.progress(90)
                    
                    report_gen = ReportGenerator()
                    output_path = os.path.join(tmpdir, 'verification_report.xlsx')
                    report_gen.generate_excel_report(results, output_path)
                    
                    with open(output_path, 'rb') as f:
                        excel_data = f.read()
                    
                    st.session_state['results'] = results
                    st.session_state['excel_data'] = excel_data
                    st.session_state['summary'] = report_gen.generate_summary(results)
                    progress_bar.progress(100)
                    
                st.success("✅ Verification completed! Switch to Results tab.")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

with tab2:
    st.header("Verification Results")
    
    if 'results' in st.session_state:
        summary = st.session_state['summary']
        results = st.session_state['results']
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Items", summary['total_items'])
        with col2:
            st.metric("✅ Matches", summary['matches'])
        with col3:
            st.metric("⚠️ Mismatches", summary['mismatches'])
        with col4:
            st.metric("➕ Added", summary['added_items'])
        with col5:
            st.metric("➖ Deleted", summary['deleted_items'])
        
        st.progress(summary['match_percentage'] / 100)
        st.caption(f"**{summary['match_percentage']:.2f}%** match rate")
        
        st.markdown("---")
        
        df_results = pd.DataFrame([
            {
                'Line Item': r.current_year_item,
                'Current Year': r.current_year_comparative,
                'Previous Year': r.previous_year_actual if r.previous_year_actual else 'N/A',
                'Difference': r.difference if r.difference else 'N/A',
                'Status': r.status,
                'Similarity': f"{r.similarity_score:.1%}"
            }
            for r in results
        ])
        
        status_filter = st.multiselect(
            "Filter by Status",
            ['MATCH', 'MISMATCH', 'ADDED', 'DELETED'],
            ['MATCH', 'MISMATCH', 'ADDED', 'DELETED']
        )
        
        filtered_df = df_results[df_results['Status'].isin(status_filter)]
        
        def color_status(val):
            colors = {
                'MATCH': 'background-color: #90EE90',
                'MISMATCH': 'background-color: #FFFF00',
                'ADDED': 'background-color: #FFB6C1',
                'DELETED': 'background-color: #FFB6C1'
            }
            return colors.get(val, '')
        
        styled_df = filtered_df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        st.download_button(
            "📊 Download Excel Report",
            st.session_state['excel_data'],
            'verification_report.xlsx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    else:
        st.info("Upload files and verify to see results")

with tab3:
    st.header("Help & Documentation")
    
    st.subheader("🎯 What This Tool Does")
    st.markdown("""
    Verifies that comparative figures in current year's financial statements 
    match the actual figures from previous year's statements.
    """)
    
    st.subheader("📊 Status Indicators")
    st.markdown("""
    - **🟢 MATCH**: Amounts match
    - **🟡 MISMATCH**: Amounts differ
    - **🔴 ADDED**: New line item
    - **🔴 DELETED**: Removed item
    """)

st.markdown("---")
