import streamlit as st
import pandas as pd
import io

# --- Page Configuration ---
st.set_page_config(page_title="KorbAnalyst", page_icon="🚀", layout="wide")

st.title("🚀 KorbAnalyst")
st.markdown("### Transactional Intelligence Dashboard")

# --- 1. File Upload Logic ---
st.info("👇 Step 1: Upload your CSV files")
uploaded_files = st.file_uploader(
    "Choose CSV files (sept.csv, oct.csv, nov.csv, dec.csv, etc.)", 
    type="csv", 
    accept_multiple_files=True
)

if uploaded_files:
    st.divider()
    st.subheader("🛠️ Step 2: Individually Match Columns for Each File")
    
    with st.form("mapping_form"):
        file_mappings = {}
        
        for i, file in enumerate(uploaded_files):
            header_df = pd.read_csv(file, nrows=0)
            cols = [c.strip() for c in header_df.columns]
            
            with st.expander(f"📄 Mapping for: {file.name}", expanded=(i == 0)):
                c1, c2, c3 = st.columns(3)
                with c1:
                    seg = st.selectbox(f"BizSegment Col ({i})", cols, index=cols.index('Biz Segment') if 'Biz Segment' in cols else 0, key=f"seg_{i}")
                    name = st.selectbox(f"Business Name Col ({i})", cols, index=cols.index('Name') if 'Name' in cols else 0, key=f"name_{i}")
                    date_col = st.selectbox(f"Date/Time Col ({i})", cols, index=cols.index('Time Created') if 'Time Created' in cols else 0, key=f"date_{i}")
                with c2:
                    cat = st.selectbox(f"Category Col ({i})", cols, index=cols.index('Category') if 'Category' in cols else 0, key=f"cat_{i}")
                    debt = st.selectbox(f"Debit Amt Col ({i})", cols, index=cols.index('Debit Amt') if 'Debit Amt' in cols else 0, key=f"debt_{i}")
                with c3:
                    gross = st.selectbox(f"Gross Margin Col ({i})", cols, index=cols.index('Gross Margin') if 'Gross Margin' in cols else 0, key=f"gross_{i}")
                    net = st.selectbox(f"Net Margin Col ({i})", cols, index=cols.index('Net Margin') if 'Net Margin' in cols else 0, key=f"net_{i}")
                    wallet = st.selectbox(f"Sender Wallet Col ({i})", cols, index=cols.index('Sender Wallet Number') if 'Sender Wallet Number' in cols else 0, key=f"wallet_{i}")
                
                file_mappings[file.name] = {
                    'seg': seg, 'name': name, 'cat': cat, 'debt': debt, 
                    'gross': gross, 'net': net, 'wallet': wallet, 'date': date_col
                }

        submit_btn = st.form_submit_button("🚀 Process & Generate Reports")

    if submit_btn:
        final_dfs = []
        for file in uploaded_files:
            file.seek(0)
            temp_df = pd.read_csv(file, low_memory=False)
            temp_df.columns = temp_df.columns.str.strip()
            
            m = file_mappings[file.name]
            
            # Map selected columns to standardized names
            std = temp_df[[m['seg'], m['cat'], m['name'], m['debt'], m['gross'], m['net'], m['wallet'], m['date']]].copy()
            std.columns = ['BizSegment', 'Category', 'Business_name', 'debit_amt', 'Gross_Margin', 'Net_Margin', 'sender_wallet_number', 'Transaction_Date']
            
            # Data Cleaning
            std['BizSegment'] = std['BizSegment'].astype(str).str.strip()
            std['Category'] = std['Category'].astype(str).str.strip()
            
            # Convert Date Column to Datetime
            std['Transaction_Date'] = pd.to_datetime(std['Transaction_Date'], errors='coerce')
            
            # Numeric conversion
            for col in ['debit_amt', 'Gross_Margin', 'Net_Margin']:
                std[col] = pd.to_numeric(std[col], errors='coerce').fillna(0)
            
            # Apply SMB Category correction logic
            std.loc[(std['BizSegment'].str.upper() == 'SMB') & (std['Category'] == 'Disbursement 2'), 'Category'] = 'Data Purchase'
            
            final_dfs.append(std)

        # Merge and store in session state
        st.session_state['master_df'] = pd.concat(final_dfs, ignore_index=True)
        st.success("✅ Data Processed Successfully!")

# --- 3. Report Generation ---
if 'master_df' in st.session_state:
    # Use a copy so filtering doesn't overwrite the original session data
    full_df = st.session_state['master_df'].copy()
    
    st.divider()
    st.header("🔍 Filter & Reports")

    # --- DATE SLIDER FILTER ---
    min_date = full_df['Transaction_Date'].min().date()
    max_date = full_df['Transaction_Date'].max().date()
    
    # Check if dates are valid
    if pd.isnull(min_date) or pd.isnull(max_date):
        st.warning("⚠️ Could not detect valid dates in the selected date column.")
        df = full_df
    else:
        selected_dates = st.slider(
            "Select Date Range",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date)
        )
        
        # Apply the filter
        df = full_df[
            (full_df['Transaction_Date'].dt.date >= selected_dates[0]) & 
            (full_df['Transaction_Date'].dt.date <= selected_dates[1])
        ]

    # Metrics Display
    m1, m2, m3 = st.columns(3)
    m1.metric("Row Count", f"{len(df):,}")
    m2.metric("Total Debit", f"GH₵ {df['debit_amt'].sum():,.2f}")
    m3.metric("Total Net Margin", f"GH₵ {df['Net_Margin'].sum():,.2f}")

    # REPORT 1: Master Pivot
    st.subheader("1. Master Segment & Category Summary")
    pivot_df = df.groupby(['BizSegment', 'Category']).agg(
        row_count=('BizSegment', 'count'),
        sum_debit_amt=('debit_amt', 'sum'),
        sum_gross_margin=('Gross_Margin', 'sum'),
        sum_net_margin=('Net_Margin', 'sum')
    ).reset_index()
    st.dataframe(pivot_df, use_container_width=True)

    # REPORT 2: Corporate Pivot
    st.subheader("2. Corporate Segment (by Category & Business Name)")
    corp_df = df[df['BizSegment'].str.lower() == 'corporate']
    corporate_pivot = corp_df.groupby(['Category', 'Business_name']).agg(
        row_count=('Business_name', 'count'),
        sum_debit_amt=('debit_amt', 'sum'),
        sum_gross_margin=('Gross_Margin', 'sum'),
        sum_net_margin=('Net_Margin', 'sum')
    ).reset_index().sort_values(by='sum_debit_amt', ascending=False)
    st.dataframe(corporate_pivot, use_container_width=True)

    # REPORT 3: Retail Pivot
    st.subheader("3. Retail Segment (by Category)")
    retail_df = df[df['BizSegment'].str.lower() == 'retail']
    retail_pivot = retail_df.groupby(['Category']).agg(
        row_count=('Category', 'count'),
        sum_debit_amt=('debit_amt', 'sum'),
        sum_gross_margin=('Gross_Margin', 'sum'),
        sum_net_margin=('Net_Margin', 'sum')
    ).reset_index().sort_values(by='sum_debit_amt', ascending=False)
    st.dataframe(retail_pivot, use_container_width=True)

    # REPORT 4 & 5: SMB Reports
    smb_df = df[df['BizSegment'].str.upper() == 'SMB']
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("4. SMB by Category")
        smb_pivot = smb_df.groupby(['Category']).agg(
            row_count=('Category', 'count'),
            sum_debit_amt=('debit_amt', 'sum'),
            sum_gross_margin=('Gross_Margin', 'sum'),
            sum_net_margin=('Net_Margin', 'sum')
        ).reset_index().sort_values(by='sum_debit_amt', ascending=False)
        st.dataframe(smb_pivot, use_container_width=True)

    with col_b:
        st.subheader("5. SMB Zones (by Wallet Number)")
        smb_zone_pivot = smb_df.groupby(['sender_wallet_number']).agg(
            row_count=('sender_wallet_number', 'count'),
            sum_debit_amt=('debit_amt', 'sum'),
            sum_gross_margin=('Gross_Margin', 'sum'),
            sum_net_margin=('Net_Margin', 'sum')
        ).reset_index().sort_values(by='sum_debit_amt', ascending=False)
        st.dataframe(smb_zone_pivot, use_container_width=True)

    # --- 4. Export to Single Excel ---
    st.divider()
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        pivot_df.to_excel(writer, sheet_name='All_Segments', index=False)
        corporate_pivot.to_excel(writer, sheet_name='Corporate', index=False)
        retail_pivot.to_excel(writer, sheet_name='Retail', index=False)
        smb_pivot.to_excel(writer, sheet_name='SMB_Category', index=False)
        smb_zone_pivot.to_excel(writer, sheet_name='SMB_Zones', index=False)
        
    st.download_button(
        label="📥 Download Filtered Reports as Excel",
        data=buffer.getvalue(),
        file_name="Korba_Business_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )