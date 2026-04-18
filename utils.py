"""
utils.py
Provides shared configuration constants and standard helper functions
used across the entire KorbAnalyst architecture.
"""

import pandas as pd

# =========================================================
# CONFIGURATION & MAPPINGS
# =========================================================

# Dictionary containing arrays of common keywords used to auto-guess columns from uploaded CSVs.
# 'key': represents internal system requirements
# 'value': represents common header names frequently uploaded
AUTO_MAP = {
    'seg': ['segment', 'bizsegment', 'type', 'client_type'],
    'name': ['name', 'business', 'merchant', 'recipient', 'customer'],
    'cat': ['category', 'service', 'product', 'transaction_type'],
    'debit': ['debit', 'amount', 'value', 'tran_amount', 'total_amount'],
    'gross': ['gross', 'commission', 'markup'],
    'net': ['net', 'profit', 'margin', 'revenue'],
    'wallet': ['wallet', 'account', 'sender', 'mobile', 'msisdn'],
    'date': ['date', 'time', 'created', 'timestamp'],
    'budget': ['budget', 'budgetkey', 'target', 'key', 'targetkey']
}

# =========================================================
# HELPER FUNCTIONS
# =========================================================

def guess_column_index(columns, key):
    """
    Scans a list of column headers from an uploaded file and tries to auto-guess
    the target column's index using standard keywords defined in AUTO_MAP.
    
    Args:
        columns (list): Extract column headers of the DataFrame.
        key (str): Targeting key identifying what data type we are looking for (e.g., 'date', 'wallet').
        
    Returns:
        int: The integer index of the identified column. Returns 0 if no match is found.
    """
    keywords = AUTO_MAP.get(key, [])
    for i, col in enumerate(columns):
        col_lower = str(col).lower()
        if any(kw in col_lower for kw in keywords):
            return i
    return 0

def clean_wallet(series):
    """
    Normalizes wallet/account strings by stripping whitespace, standardizing 'O' to zero, 
    and slicing string logic to only keep the last 9 fundamental identifying digits.
    
    Args:
        series (pd.Series): Raw pandas series targeting the wallet numbers.
        
    Returns:
        pd.Series: The cleaned, standard wallet series.
    """
    return series.fillna('').astype(str).str.replace(" ", "", regex=False).str.replace("o", "0", case=False).str.slice(-9)

def classify_segment(x):
    """
    Classify business units into strict standardized internal segments based on keyword hits.
    Forces 'retail' to be recognized robustly even within edge cases.
    
    Args:
        x (str): A string representing the raw segment value attached to a transaction.
        
    Returns:
        str: Either 'retail', 'corporate', 'smb', or 'other'.
    """
    x = str(x).lower().strip()
    
    # Highest priority parsing
    if any(k in x for k in ['retail', 'consumer', 'individual', 'personal', 'b2c']): 
        return 'retail'
    if any(k in x for k in ['corporate', 'corp', 'enterprise', 'b2b']): 
        return 'corporate'
    if any(k in x for k in ['smb', 'sme', 'small', 'merchant']): 
        return 'smb'
        
    return 'other'

def clean_report(rdf):
    """
    General utility formatter intended exclusively for the UI Layer output.
    Renames column headers sequentially and guarantees standardized descent sorting.
    
    Args:
        rdf (pd.DataFrame): Aggregated report generated inside the Streamlit Tabs.
        
    Returns:
        pd.DataFrame: Ready-to-render DataFrame for st.dataframe() outputs.
    """
    if rdf.empty: 
        return rdf
        
    rdf.columns = ['Volume', 'Value', 'Gross', 'Net']
    return rdf.sort_values('Value', ascending=False)
