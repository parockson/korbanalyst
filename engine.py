"""
engine.py
Responsible for all backend DataFrame calculations. Connects uploaded raw CSVs 
to the mapping logic provided by the user, aggregating and filtering data internally
without touching the UI state directly.
"""

import pandas as pd
from utils import clean_wallet, classify_segment

def process_transaction_files(uploaded_files, file_mappings, enable_zones, zone_file, z_wallet_col, z_name_col):
    """
    Core function mapping raw transaction CSVs, normalizing structure, assigning clean segments,
    handling date transformations, and applying zone clustering if toggled active.
    
    Args:
        uploaded_files (list): The list of Streamlit UploadedFile objects (CSVs).
        file_mappings (dict): A mapping schema configured by the user assigning internal keys to explicit columns.
        enable_zones (bool): Flag indicating if geospatial merging is requested.
        zone_file (UploadedFile): Raw file containing the Zone Mapping logic.
        z_wallet_col (str): The column denoting the joining key within the `zone_file`.
        z_name_col (str): The column denoting the geospatial label inside `zone_file`.
        
    Returns:
        pd.DataFrame: A fully curated, standardized 'master' dataframe containing all combined data elements.
    """
    all_data = []
    
    # -------------------------------------------------------------
    # 1. READ & INGEST INDIVIDUAL FILES
    # -------------------------------------------------------------
    for file in uploaded_files:
        file.seek(0)
        
        # Try generic read, handle distinct internal encodings if Latin character sets leak into output
        try:
            tmp = pd.read_csv(file, low_memory=False)
        except:
            file.seek(0)
            tmp = pd.read_csv(file, low_memory=False, encoding='latin1')
        
        # Lock mapping dictionary targeting precisely the current iterated file
        m = file_mappings[file.name]
        
        # Instantiate normalized baseline structure based on the mapped selections
        std = tmp[[m['seg'], m['cat'], m['name'], m['debit'], m['gross'], m['net'], m['wallet'], m['date'], m['budget']]].copy()
        
        # Hard code renaming sequence for strict standardization down pipeline
        std.columns = ['BizSegment', 'Category', 'Business_name', 'debit_amt', 'Gross_Margin', 'Net_Margin', 'sender_wallet_number', 'Transaction_Date', 'Budgetkey']
        
        # ---------------------------------------------------------
        # 2. FEATURE ENGINEERING & CLEANING
        # ---------------------------------------------------------
        # Dynamically calculate the core business segment
        std['Biz_Seg'] = std['BizSegment'].apply(classify_segment)
        
        # Convert explicit Dates and safely cull corruptions natively
        dfmt = m.get('date_fmt', '').strip()
        if dfmt:
            # User explicitly provided a format — use it exactly
            std['Transaction_Date'] = pd.to_datetime(std['Transaction_Date'], errors='coerce', format=dfmt)
        else:
            # Auto mode: pandas handles YYYY-MM-DD and ISO formats correctly without dayfirst
            # NOTE: dayfirst=True was removed because it caused ambiguous MM/DD swaps on YYYY-MM-DD inputs
            std['Transaction_Date'] = pd.to_datetime(std['Transaction_Date'], errors='coerce')
        
        # INSTEAD of dropping rows with invalid or entirely absent dates (which causes total volume mismatches), 
        # we natively forward-fill and back-fill the last valid Date. Sequentially exported CSVs handle this cleanly!
        std['Transaction_Date'] = std['Transaction_Date'].ffill().bfill()
        
        # Enforce numeric handling converting everything else to zeros natively
        for col in ['debit_amt', 'Gross_Margin', 'Net_Margin']:
            std[col] = pd.to_numeric(std[col], errors='coerce').fillna(0)
        
        # Split dates for deeper Analytics Tabs 
        std['Date'] = std['Transaction_Date'].dt.date
        std['Hour'] = std['Transaction_Date'].dt.hour
        
        # Clean wallet numbers to link Zone tables and track unique agents uniformly
        std['clean_wallet'] = clean_wallet(std['sender_wallet_number'])
        
        all_data.append(std)

    # Compile files into an overarching universal dataframe
    master_df = pd.concat(all_data, ignore_index=True)

    # -------------------------------------------------------------
    # 3. GEOSPATIAL MERGING (ZONES)
    # -------------------------------------------------------------
    if enable_zones and zone_file and z_wallet_col and z_name_col:
        zone_file.seek(0)
        
        # Identify file structure cleanly
        z_raw = pd.read_csv(zone_file) if zone_file.name.endswith('.csv') else pd.read_excel(zone_file)
        
        # Normalize target merge key
        z_raw['clean_wallet'] = clean_wallet(z_raw[z_wallet_col])
        
        # Clean specific trailing texts explicitly to merge robustly ('Northern Zone' -> 'Northern')
        z_raw[z_name_col] = z_raw[z_name_col].astype(str).str.replace(r'(?i)\bzone\b', '', regex=True).str.strip()
        
        # Map internal counts and dedup references to limit massive cardinality issues within the DB JOIN
        agents = z_raw.groupby(z_name_col)['clean_wallet'].nunique().reset_index()
        agents.columns = ['Zone_Name', 'Agent_Counts']
        
        # Compile unique reference identifiers to execute join mechanics cleanly
        z_map = z_raw[['clean_wallet', z_name_col]].drop_duplicates()
        z_map.columns = ['clean_wallet', 'Zone_Name']
        
        # Merge target references successively to the master structure
        master_df = master_df.merge(z_map, on='clean_wallet', how='left')
        master_df = master_df.merge(agents, on='Zone_Name', how='left')
        
        # Patch unhandled cases cleanly
        master_df['Zone_Name'] = master_df['Zone_Name'].fillna('Unmapped')
        master_df['Agent_Counts'] = master_df['Agent_Counts'].fillna(0)

    return master_df
