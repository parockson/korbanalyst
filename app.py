import streamlit as st
import pandas as pd
import io

# --- Page Configuration ---
st.set_page_config(page_title="KorbAnalyst", page_icon="🚀", layout="wide")

st.title("🚀 KorbAnalyst")
st.markdown("### Transactional Intelligence Dashboard")

# --- Refresh/Reset Logic ---
if st.sidebar.button("🔄 Reset & Clear All Data"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# --- Helper Function for Wallet Cleaning ---
def clean_wallet(series):
    return series.astype(str).str.replace(" ", "", regex=False).str.replace("o", "0", case=False).str.slice(-9)

# --- 1. File Upload ---
st.info("👇 Step 1: Upload Transactional CSVs")
uploaded_files = st.file_uploader("Choose Monthly CSV files", type="csv", accept_multiple_files=True)

# --- Zone Sidebar ---
st.sidebar.divider()
st.sidebar.header("📍 Zone Analysis")
enable_zones = st.sidebar.checkbox("Process Zone Data?")
zone_file = None
if enable_zones:
    zone_file = st.sidebar.file_uploader("Upload Zone Mapping", type=["csv", "xlsx"])

if uploaded_files:
    st.divider()
    st.subheader("🛠️ Step 2: Column Mapping")
    
    with st.form("main_mapping_form"):
        file_mappings = {}
        for i, file in enumerate(uploaded_files):
            header_df = pd.read_csv(file, nrows=0)
            cols = [c.strip() for c in header_df.columns]
            
            with st.expander(f"📄 Mapping: {file.name}", expanded=(i == 0)):
                c1, c2, c3 = st.columns(3)
                with c1:
                    seg = st.selectbox(f"BizSegment ({i})", cols, index=cols.index('Biz Segment') if 'Biz Segment' in cols else 0, key=f"seg_{i}")
                    name = st.selectbox(f"Business Name ({i})", cols, index=cols.index('Name') if 'Name' in cols else 0, key=f"name_{i}")
                    date_col = st.selectbox(f"Date/Time ({i})", cols, index=cols.index('Time Created') if 'Time Created' in cols else 0, key=f"date_{i}")
                with c2:
                    cat = st.selectbox(f"Category ({i})", cols, index=cols.index('Category') if 'Category' in cols else 0, key=f"cat_{i}")
                    debt = st.selectbox(f"Debit Amt ({i})", cols, index=cols.index('Debit Amt') if 'Debit Amt' in cols else 0, key=f"debt_{i}")
                with c3:
                    gross = st.selectbox(f"Gross Margin ({i})", cols, index=cols.index('Gross Margin') if 'Gross Margin' in cols else 0, key=f"gross_{i}")
                    net = st.selectbox(f"Net Margin ({i})", cols, index=cols.index('Net Margin') if 'Net Margin' in cols else 0, key=f"net_{i}")
                    wallet = st.selectbox(f"Sender Wallet ({i})", cols, index=cols.index('Sender Wallet Number') if 'Sender Wallet Number' in cols else 0, key=f"wallet_{i}")
                
                file_mappings[file.name] = {'seg': seg, 'name': name, 'cat': cat, 'debt': debt, 'gross': gross, 'net': net, 'wallet': wallet, 'date': date_col}

        zone_map_cols = {}
        if enable_zones and zone_file:
            st.markdown("---")
            z_df_prev = pd.read_csv(zone_file, nrows=0) if zone_file.name.endswith('.csv') else pd.read_excel(zone_file, nrows=0)
            z_cols = z_df_prev.columns.tolist()
            zc1, zc2 = st.columns(2)
            zone_map_cols['wallet'] = zc1.selectbox("Zone Wallet Number Col", z_cols)
            zone_map_cols['zone_name'] = zc2.selectbox("Zone Name Col", z_cols)

        submit_btn = st.form_submit_button("🚀 Process & Generate All Reports")

    if submit_btn:
        final_dfs = []
        for file in uploaded_files:
            file.seek(0)
            temp_df = pd.read_csv(file, low_memory=False)
            temp_df.columns = temp_df.columns.str.strip()
            m = file_mappings[file.name]
            
            std = temp_df[[m['seg'], m['cat'], m['name'], m['debt'], m['gross'], m['net'], m['wallet'], m['date']]].copy()
            std.columns = ['BizSegment', 'Category', 'Business_name', 'debit_amt', 'Gross_Margin', 'Net_Margin', 'sender_wallet_number', 'Transaction_Date']
            
            # Cleaning
            std['BizSegment'] = std['BizSegment'].astype(str).str.strip()
            std['Category'] = std['Category'].astype(str).str.strip()
            std['Transaction_Date'] = pd.to_datetime(std['Transaction_Date'], errors='coerce')
            for col in ['debit_amt', 'Gross_Margin', 'Net_Margin']:
                std[col] = pd.to_numeric(std[col], errors='coerce').fillna(0)
            
            std['clean_wallet'] = clean_wallet(std['sender_wallet_number'])
            
            # SMB Correction
            std.loc[(std['BizSegment'].str.upper() == 'SMB') & (std['Category'] == 'Disbursement 2'), 'Category'] = 'Data Purchase'
            final_dfs.append(std)

        master_df = pd.concat(final_dfs, ignore_index=True)

        if enable_zones and zone_file:
            zone_file.seek(0)
            z_raw = pd.read_csv(zone_file) if zone_file.name.endswith('.csv') else pd.read_excel(zone_file)
            z_raw['clean_wallet'] = clean_wallet(z_raw[zone_map_cols['wallet']])
            z_clean = z_raw[['clean_wallet', zone_map_cols['zone_name']]].drop_duplicates('clean_wallet')
            z_clean.columns = ['clean_wallet', 'Zone_Name']
            master_df = master_df.merge(z_clean, on='clean_wallet', how='left')
            master_df['Zone_Name'] = master_df['Zone_Name'].fillna('Unmapped')

        st.session_state['master_df'] = master_df
        st.success("✅ Processing Complete!")

# --- 3. Reports Display ---
if 'master_df' in st.session_state:
    df = st.session_state['master_df'].copy()
    
    st.sidebar.subheader("Filter Dates")
    min_date = df['Transaction_Date'].min().date()
    max_date = df['Transaction_Date'].max().date()
    start_d = st.sidebar.date_input("Start", min_date)
    end_d = st.sidebar.date_input("End", max_date)
    df = df[(df['Transaction_Date'].dt.date >= start_d) & (df['Transaction_Date'].dt.date <= end_d)]

    st.header(f"📊 Dashboard: {start_d} to {end_d}")

    # 1. MASTER SUMMARY
    st.subheader("1. Master Segment & Category Summary")
    master_pivot = df.groupby(['BizSegment', 'Category']).agg(
        volume=('BizSegment', 'count'),
        value=('debit_amt', 'sum'),
        gross=('Gross_Margin', 'sum'),
        net=('Net_Margin', 'sum')
    ).reset_index()
    st.dataframe(master_pivot, width='stretch')

    # 2. CORPORATE
    st.subheader("2. Corporate Segment Performance")
    corp_df = df[df['BizSegment'].str.contains('corporate', case=False, na=False)]
    if not corp_df.empty:
        corp_pivot = corp_df.groupby(['Category', 'Business_name']).agg(volume=('Business_name', 'count'), value=('debit_amt', 'sum')).reset_index()
        st.dataframe(corp_pivot, width='stretch')
    else:
        st.warning("⚠️ No Corporate data found. Check 'Master Summary' above to see how segments are named.")

    # 3. RETAIL
    st.subheader("3. Retail Segment Summary")
    retail_df = df[df['BizSegment'].str.contains('retail', case=False, na=False)]
    if not retail_df.empty:
        retail_pivot = retail_df.groupby(['Category']).agg(
            volume=('Category', 'count'), 
            value=('debit_amt', 'sum'), 
            net_margin=('Net_Margin', 'sum')
        ).reset_index().sort_values(by='value', ascending=False)
        st.dataframe(retail_pivot, width='stretch')
    else:
        st.warning("⚠️ No Retail data found. Check 'Master Summary' above to see how segments are named.")

    # 4. SMB by Category
    st.subheader("4. SMB by Category")
    smb_df = df[df['BizSegment'].str.contains('smb', case=False, na=False)]
    if not smb_df.empty:
        smb_cat_pivot = smb_df.groupby(['Category']).agg(volume=('Category', 'count'), value=('debit_amt', 'sum')).reset_index().sort_values(by='value', ascending=False)
        st.dataframe(smb_cat_pivot, width='stretch')
    else:
        st.warning("⚠️ No SMB data found. Check 'Master Summary' above to see how segments are named.")

    # 5. SMB by Wallet Number
    st.subheader("5. SMB by Wallet Number")
    if not smb_df.empty:
        smb_wallet_pivot = smb_df.groupby(['sender_wallet_number']).agg(volume=('sender_wallet_number', 'count'), value=('debit_amt', 'sum')).reset_index().sort_values(by='value', ascending=False)
        st.dataframe(smb_wallet_pivot, width='stretch')

    # 6. SMB BY ZONE (Conditional)
    if 'Zone_Name' in df.columns:
        st.subheader("6. 📍 SMB Zone Performance")
        zone_report = smb_df.groupby('Zone_Name').agg(
            agent_count=('sender_wallet_number', 'nunique'),
            volume=('sender_wallet_number', 'count'),
            value=('debit_amt', 'sum'),
            gross_rev=('Gross_Margin', 'sum'),
            net_rev=('Net_Margin', 'sum')
        ).reset_index().sort_values(by='value', ascending=False)
        st.dataframe(zone_report, width='stretch')

    # Export
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        master_pivot.to_excel(writer, sheet_name='Master', index=False)
        if not corp_df.empty: corp_pivot.to_excel(writer, sheet_name='Corporate', index=False)
        if not retail_df.empty: retail_pivot.to_excel(writer, sheet_name='Retail', index=False)
        if not smb_df.empty:
            smb_cat_pivot.to_excel(writer, sheet_name='SMB_Category', index=False)
            smb_wallet_pivot.to_excel(writer, sheet_name='SMB_By_Wallet', index=False)
        if 'Zone_Name' in df.columns: 
            zone_report.to_excel(writer, sheet_name='Zones', index=False)
            
    st.download_button("📥 Download Full Excel Report", data=buffer.getvalue(), file_name="Korba_Analysis_Final.xlsx")