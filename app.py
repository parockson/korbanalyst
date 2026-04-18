"""
app.py
The Core UI architecture handling all interaction logic from Streamlit.
This file handles only the DOM rendering elements, mapping visual features out and routing calls 
dynamically into the analytical engine file explicitly.
"""

import streamlit as st
import pandas as pd
import io
import plotly.graph_objects as go
from utils import guess_column_index, clean_report
from engine import process_transaction_files

# =========================================================
# 🚀 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(page_title="KorbAnalyst", page_icon="🚀", layout="wide")

st.title("🚀 KorbAnalyst")
st.markdown("### Transactional Intelligence Dashboard")

# =========================================================
# 📂 2. FILE UPLOAD & SIDEBAR CONTROLLER 
# =========================================================
# Clear the cache explicitly directly to start cleanly at session inception if requested
st.sidebar.button("🔄 Reset App", on_click=lambda: st.session_state.clear())

st.info("👇 Step 1: Upload Transactional CSVs")

# File components
uploaded_files = st.file_uploader("Choose CSV files", type="csv", accept_multiple_files=True)

# Toggle handling explicit geospatial logic natively using checkboxes
enable_zones = st.sidebar.checkbox("Process Zone Data?")
zone_file = st.sidebar.file_uploader("Upload Zone Mapping", type=["csv", "xlsx"]) if enable_zones else None

# Toggle handling explicit target vs actual logic
enable_targets = st.sidebar.checkbox("Process Target vs Actual?")
target_file = st.sidebar.file_uploader("Upload Target File", type=["csv", "xlsx"]) if enable_targets else None

# =========================================================
# 🛠️ 3. MAPPING LOGIC & ENGINE EXECUTION
# =========================================================
if uploaded_files:
    with st.form("main_form"):
        st.subheader("🛠️ Step 2: Column Mapping")
        file_mappings = {}
        
        # Build individual logic handling targeting explicitly uploaded sequences 
        for i, file in enumerate(uploaded_files):
            # Probe directly to extract native column headers safely
            try:
                header_df = pd.read_csv(file, nrows=0)
            except:
                file.seek(0)
                header_df = pd.read_csv(file, nrows=0, encoding='latin1')
            
            cols = header_df.columns.tolist()
            
            # Map parameters targeting individual attributes leveraging guess patterns efficiently
            with st.expander(f"📄 Mapping: {file.name}", expanded=(i == 0)):
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    seg = st.selectbox(f"BizSegment ({i})", cols, index=guess_column_index(cols, 'seg'), key=f"seg_{i}")
                    name = st.selectbox(f"Business Name ({i})", cols, index=guess_column_index(cols, 'name'), key=f"name_{i}")
                    date_col = st.selectbox(f"Date ({i})", cols, index=guess_column_index(cols, 'date'), key=f"date_{i}")
                
                with c2:
                    cat = st.selectbox(f"Category ({i})", cols, index=guess_column_index(cols, 'cat'), key=f"cat_{i}")
                    debit = st.selectbox(f"Debit Amt ({i})", cols, index=guess_column_index(cols, 'debit'), key=f"debit_{i}")
                    budget_col = st.selectbox(f"Budget Key ({i})", cols, index=guess_column_index(cols, 'budget'), key=f"budget_{i}")
                
                with c3:
                    gross = st.selectbox(f"Gross Margin ({i})", cols, index=guess_column_index(cols, 'gross'), key=f"gross_{i}")
                    net = st.selectbox(f"Net Margin ({i})", cols, index=guess_column_index(cols, 'net'), key=f"net_{i}")
                    wallet = st.selectbox(f"Wallet ({i})", cols, index=guess_column_index(cols, 'wallet'), key=f"wallet_{i}")
                
                fmt_opts = {
                    'Auto': 'Auto', 
                    'YYYY-MM-DDTHH:MM:SS (e.g. 2026-03-29T16:13:56)': '%Y-%m-%dT%H:%M:%S',
                    'YYYY-MM-DD HH:MM:SS (e.g. 2026-03-29 16:13:56)': '%Y-%m-%d %H:%M:%S',
                    'YYYY-MM-DD (e.g. 2026-03-29)': '%Y-%m-%d',
                    'DD/MM/YYYY (e.g. 29/03/2026)': '%d/%m/%Y',
                    'MM/DD/YYYY (e.g. 03/29/2026)': '%m/%d/%Y',
                    'Custom': 'Custom'
                }
                date_fmt_display = st.selectbox(f"Date Format ({i})", list(fmt_opts.keys()), key=f"dfmt_opt_{i}")
                date_fmt_opt = fmt_opts[date_fmt_display]
                date_fmt_custom = ""
                if date_fmt_opt == 'Custom':
                    date_fmt_custom = st.text_input(f"Custom Date Format", placeholder="e.g. %d-%m-%Y %H:%M", key=f"dfmt_custom_{i}")
                
                final_dfmt = date_fmt_custom if date_fmt_opt == 'Custom' else ('' if date_fmt_opt == 'Auto' else date_fmt_opt)
                
                # Assign mappings recursively across multiple selections
                file_mappings[file.name] = {
                    'seg': seg, 'name': name, 'cat': cat, 'debit': debit, 
                    'gross': gross, 'net': net, 'wallet': wallet, 'date': date_col, 'budget': budget_col, 'date_fmt': final_dfmt
                }

        # Sub-handling explicitly tied to Geospatial Zone attributes mapping cleanly 
        z_wallet_col, z_name_col = None, None
        if enable_zones and zone_file:
            st.divider()
            st.subheader("📍 SMB Zone File Mapping")
            try:
                z_header = pd.read_csv(zone_file, nrows=0) if zone_file.name.endswith('.csv') else pd.read_excel(zone_file, nrows=0)
                z_cols = z_header.columns.tolist()
                
                zc1, zc2 = st.columns(2)
                with zc1:
                    z_wallet_col = st.selectbox("SMB Wallet ID Column", z_cols, index=guess_column_index(z_cols, 'wallet'))
                with zc2:
                    z_name_col = st.selectbox("Zone/Region Column", z_cols, index=1 if len(z_cols) > 1 else 0)
            except:
                st.error("Could not read Zone file headers.")

        t_budget_col, t_month_col, t_vol_col, t_val_col, t_gross_col, t_net_col = None, None, None, None, None, None
        if enable_targets and target_file:
            st.divider()
            st.subheader("🎯 Target Mapping")
            try:
                t_header = pd.read_csv(target_file, nrows=0) if target_file.name.endswith('.csv') else pd.read_excel(target_file, nrows=0)
                t_cols = t_header.columns.tolist()
                
                tc1, tc2, tc3 = st.columns(3)
                with tc1:
                    t_budget_col = st.selectbox("Target Budget Key", t_cols, index=guess_column_index(t_cols, 'budget'))
                    # Auto-detect 'Month' column by looking for keyword in headers
                    month_guess = next((i for i, c in enumerate(t_cols) if 'month' in c.lower() or 'mon' in c.lower()), 0)
                    t_month_col = st.selectbox("Target Month", t_cols, index=month_guess)
                with tc2:
                    t_vol_col = st.selectbox("Target Volume", t_cols, index=0)
                    t_val_col = st.selectbox("Target Value", t_cols, index=1 if len(t_cols) > 1 else 0)
                with tc3:
                    t_gross_col = st.selectbox("Target Gross", t_cols, index=guess_column_index(t_cols, 'gross'))
                    t_net_col = st.selectbox("Target Net", t_cols, index=guess_column_index(t_cols, 'net'))
            except:
                st.error("Could not read Target file headers.")

        submit_btn = st.form_submit_button("🚀 Run Analysis")

    # Processing trigger cleanly tied to custom engine function
    if submit_btn:
        master_df = process_transaction_files(
            uploaded_files, file_mappings, enable_zones, zone_file, z_wallet_col, z_name_col
        )
        # Store securely to app session natively
        st.session_state['master_df'] = master_df
        
        if enable_targets and target_file:
            target_file.seek(0)
            t_df = pd.read_csv(target_file) if target_file.name.endswith('.csv') else pd.read_excel(target_file)
            t_df = t_df[[t_budget_col, t_month_col, t_vol_col, t_val_col, t_gross_col, t_net_col]].copy()
            t_df.columns = ['Budgetkey', 'Month', 'T_Volume', 'T_Value', 'T_Gross', 'T_Net']
            t_df['Budgetkey'] = t_df['Budgetkey'].astype(str).str.strip().str.lower()
            # Normalise Month to exactly 3-char title case to match strftime('%b') output
            t_df['Month'] = t_df['Month'].astype(str).str.strip().str[:3].str.title()
            st.session_state['target_df'] = t_df
        else:
            if 'target_df' in st.session_state:
                del st.session_state['target_df']

# =========================================================
# 📊 4. THE 6 PRIMARY DASHBOARD REPORTS
# =========================================================
if 'master_df' in st.session_state:
    df = st.session_state['master_df'].copy()

    st.divider()
    
    # Isolate valid transaction ranges filtering NaN safely
    valid_dates = df.dropna(subset=['Date'])
    if valid_dates.empty:
        st.warning("No valid dates found in the dataset. Please check your date mappings.")
        st.stop()
        
    min_date, max_date = valid_dates['Date'].min(), valid_dates['Date'].max()
    
    st.markdown("### 📅 Filtering Controls")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        # Always show a Date Input range picker (From... To...)
        date_res = st.date_input(
            "Picker (From - To)", 
            value=(min_date, max_date) if min_date != max_date else min_date,
            min_value=min_date,
            max_value=max_date
        )
        
    # Parse the picker native ranges
    if isinstance(date_res, tuple):
        d_start = date_res[0]
        d_end = date_res[1] if len(date_res) > 1 else date_res[0]
    else:
        d_start = d_end = date_res
        
    with c2:
        # Also render a Slider range (From... To...) that cleanly syncs to the picker!
        if min_date != max_date:
            d_start, d_end = st.select_slider(
                "Slider (From - To)", 
                options=list(pd.date_range(min_date, max_date).date), 
                value=(d_start, d_end)
            )
        else:
            st.info("Slider hidden because datasets only spans exactly 1 day natively.")
        
    # Execute native Pandas filtering leveraging dates explicitly
    df = df[(df['Date'] >= d_start) & (df['Date'] <= d_end)]

    # -------------------------------------------------------------
    # Render Master Level KPIs 
    # -------------------------------------------------------------
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Volume", f"{len(df):,}")
    m2.metric("Value", f"GH₵ {df['debit_amt'].sum():,.2f}")
    m3.metric("Gross", f"GH₵ {df['Gross_Margin'].sum():,.2f}")
    m4.metric("Net", f"GH₵ {df['Net_Margin'].sum():,.2f}")

    # Standard analytical dictionary tying features dynamically formatting the tables 
    agg_dict = {'debit_amt': ['count', 'sum'], 'Gross_Margin': 'sum', 'Net_Margin': 'sum'}

    # -------------------------------------------------------------
    # Deep Native Analytics Rendered Via Tabs 
    # -------------------------------------------------------------
    tabs = st.tabs(["Summary", "Corporate", "Retail", "SMB-Cat", "Zones", "Budget Summary", "Trends", "Budget Trend Analysis"])

    # TAB 1: High Level
    with tabs[0]:
        st.subheader("1. Master Summary")
        ms_rep = clean_report(df.groupby(['Biz_Seg', 'Category']).agg(agg_dict))
        if not ms_rep.empty:
            ms_rep.loc[('Grand Total', ''), :] = ms_rep.sum(numeric_only=True)
        st.dataframe(ms_rep, width='stretch')

    # TAB 2: Corporate Slice
    with tabs[1]:
        st.subheader("2. Corporate Analysis")
        corp = df[df['Biz_Seg'] == 'corporate']
        if not corp.empty:
            c_rep = clean_report(corp.groupby(['Category', 'Business_name']).agg(agg_dict))
            if not c_rep.empty:
                c_rep.loc[('Grand Total', ''), :] = c_rep.sum(numeric_only=True)
            st.dataframe(c_rep, width='stretch')
        else:
            st.warning("No Corporate data found.")

    # TAB 3: Retail Slice
    with tabs[2]:
        st.subheader("3. Retail Analysis")
        ret = df[df['Biz_Seg'] == 'retail']
        if not ret.empty:
            r_rep = clean_report(ret.groupby('Category').agg(agg_dict))
            if not r_rep.empty:
                r_rep.loc['Grand Total'] = r_rep.sum(numeric_only=True)
            st.dataframe(r_rep, width='stretch')
        else:
            st.warning("No Retail data found. Check your 'BizSegment' mapping for keywords like 'Individual' or 'Personal'.")

    # TAB 4: SMB-Cat Slice
    with tabs[3]:
        st.subheader("4. SMB-Cat Analysis")
        smb = df[df['Biz_Seg'] == 'smb']
        if not smb.empty:
            s_rep = clean_report(smb.groupby('Category').agg(agg_dict))
            if not s_rep.empty:
                s_rep.loc['Grand Total'] = s_rep.sum(numeric_only=True)
            st.dataframe(s_rep, width='stretch')
        else:
            st.warning("No SMB data found.")

    # TAB 5: Zone/Agent Slices
    with tabs[4]:
        st.subheader("5. Zone & Agent Analysis")
        # Ensure we don't render native errors if zone was bypassed cleanly
        if 'Zone_Name' in df.columns:
            # specifically filtering timeframe AND Segment
            zone_df = df[df['Biz_Seg'] == 'smb']
            if not zone_df.empty:
                z_rep = zone_df.groupby('Zone_Name').agg({
                    'debit_amt': ['count', 'sum'], 'Gross_Margin': 'sum', 'Net_Margin': 'sum', 'clean_wallet': 'nunique'
                })
                z_rep.columns = ['Volume', 'Value', 'Gross', 'Net', 'Agent_Counts']
                z_rep = z_rep.sort_values('Value', ascending=False)
                if not z_rep.empty:
                    z_rep.loc['Grand Total'] = z_rep.sum(numeric_only=True)
                st.dataframe(z_rep, width='stretch')
            else:
                st.warning("No SMB data found for Zone mapping.")

    # TAB 6: Budget Summary Slice
    with tabs[5]:
        st.subheader("6. Budget Summary")
        if 'target_df' in st.session_state and 'Budgetkey' in df.columns:
            act = df.groupby(['Budgetkey', 'Biz_Seg', 'Category']).agg({
                'debit_amt': ['count', 'sum'], 'Gross_Margin': 'sum', 'Net_Margin': 'sum'
            }).reset_index()
            act.columns = ['Budgetkey', 'Biz_Seg', 'Category', 'A_Volume', 'A_Value', 'A_Gross', 'A_Net']
            act['Budgetkey'] = act['Budgetkey'].astype(str).str.strip().str.lower()
            
            t_df = st.session_state['target_df'].copy()
            t_df = t_df.groupby('Budgetkey').sum(numeric_only=True).reset_index()
            
            # Left join: only keep actuals — target rows with no matching actual are excluded
            res = pd.merge(act, t_df, on='Budgetkey', how='left')
            
            num_cols = ['A_Volume', 'A_Value', 'A_Gross', 'A_Net', 'T_Volume', 'T_Value', 'T_Gross', 'T_Net']
            for c in num_cols:
                if c in res.columns:
                    res[c] = pd.to_numeric(res[c], errors='coerce').fillna(0)
                    
            res['Vol_Achv%'] = (res['A_Volume'] / res['T_Volume'].replace(0, pd.NA)) * 100
            res['Value_Achv%'] = (res['A_Value'] / res['T_Value'].replace(0, pd.NA)) * 100
            res['Gross_Achv%'] = (res['A_Gross'] / res['T_Gross'].replace(0, pd.NA)) * 100
            res['Net_Achv%'] = (res['A_Net'] / res['T_Net'].replace(0, pd.NA)) * 100
            
            res[['Vol_Achv%', 'Value_Achv%', 'Gross_Achv%', 'Net_Achv%']] = res[['Vol_Achv%', 'Value_Achv%', 'Gross_Achv%', 'Net_Achv%']].fillna(0)
            
            res = res[['Budgetkey', 'Biz_Seg', 'Category', 
                       'T_Volume', 'A_Volume', 'Vol_Achv%', 
                       'T_Value', 'A_Value', 'Value_Achv%',
                       'T_Gross', 'A_Gross', 'Gross_Achv%',
                       'T_Net', 'A_Net', 'Net_Achv%']]
                       
            res['Biz_Seg'] = res['Biz_Seg'].fillna('UnmappedTarget')
            res['Category'] = res['Category'].fillna('UnmappedTarget')
            res = res.sort_values('A_Value', ascending=False).set_index(['Budgetkey', 'Biz_Seg', 'Category'])
            
            if not res.empty:
                res.loc[('Grand Total', '', ''), :] = res.sum(numeric_only=True)
                gt = res.loc[('Grand Total', '', '')]
                res.loc[('Grand Total', '', ''), 'Vol_Achv%'] = (gt['A_Volume'] / gt['T_Volume'] * 100) if gt['T_Volume'] else 0
                res.loc[('Grand Total', '', ''), 'Value_Achv%'] = (gt['A_Value'] / gt['T_Value'] * 100) if gt['T_Value'] else 0
                res.loc[('Grand Total', '', ''), 'Gross_Achv%'] = (gt['A_Gross'] / gt['T_Gross'] * 100) if gt['T_Gross'] else 0
                res.loc[('Grand Total', '', ''), 'Net_Achv%'] = (gt['A_Net'] / gt['T_Net'] * 100) if gt['T_Net'] else 0
                
            achv_cols = ['Vol_Achv%', 'Value_Achv%', 'Gross_Achv%', 'Net_Achv%']
            other_cols = [c for c in res.columns if c not in achv_cols]
            fmt = {c: '{:,.0f}' for c in other_cols}
            fmt.update({c: '{:.0f}' for c in achv_cols})
            st.dataframe(
                res.style
                   .format(fmt)
                   .background_gradient(subset=achv_cols, cmap='RdYlGn', vmin=0, vmax=100),
                width='stretch'
            )
        else:
            st.info("Target data not mapped. Enable 'Process Target' and upload your file.")

    # TAB 7: Trend Tracking Slice 
    with tabs[6]:
        st.subheader("7. Trends")
        
        # Local UI segment filter
        t_segs = df['Biz_Seg'].unique().tolist()
        t_sel = st.multiselect("Filter by Business Segment (Trends)", t_segs, default=t_segs)
        t_df = df[df['Biz_Seg'].isin(t_sel)] if t_sel else df
        
        c1, c2 = st.columns(2)
        
        hourly = t_df.groupby('Hour').agg({
            'debit_amt': ['count', 'sum'], 'Gross_Margin': 'sum', 'Net_Margin': 'sum'
        })
        hourly.columns = ['Volume', 'Value', 'Gross', 'Net']
        
        c1.write("**1. Hourly Volume**")
        c1.bar_chart(hourly['Volume'])
        
        c1.write("**2. Hourly Value**")
        c1.line_chart(hourly['Value'])
        
        c2.write("**3. Hourly Gross**")
        c2.line_chart(hourly['Gross'])
        
        c2.write("**4. Hourly Net**")
        c2.line_chart(hourly['Net'])
        
        # Native output generator
        st.download_button("📥 Export CSV", df.to_csv(index=False).encode('utf-8'), "korba_data.csv", "text/csv")

    # TAB 8: Budget Trend Analysis Slice
    with tabs[7]:
        st.subheader("8. Budget Trend Analysis")
        bt_segs = df['Biz_Seg'].unique().tolist()
        bt_sel = st.multiselect("Filter by Business Segment (Budget Trends)", bt_segs, default=bt_segs)
        bt_df = df[df['Biz_Seg'].isin(bt_sel)] if bt_sel else df
        
        # Chart type toggle — 3D Clustered Column is default first choice
        chart_type = st.radio("Select Chart Type", ["Line Graph", "Clustered Column"], horizontal=True)
        
        bc1, bc2 = st.columns(2)
        
        if not bt_df.empty:
            bt_df = bt_df.copy()
            bt_df['Month'] = pd.to_datetime(bt_df['Date']).dt.strftime('%b')
            
            monthly_metrics = bt_df.groupby('Month').agg({
                'debit_amt': ['count', 'sum'], 'Gross_Margin': 'sum', 'Net_Margin': 'sum'
            })
            monthly_metrics.columns = ['Actual Volume', 'Actual Value', 'Actual Gross', 'Actual Net']
            
            t_df = st.session_state.get('target_df', pd.DataFrame())
            if not t_df.empty and 'Month' in t_df.columns:
                target_by_month = t_df.groupby('Month')[['T_Volume', 'T_Value', 'T_Gross', 'T_Net']].sum()
                target_by_month.columns = ['Target Volume', 'Target Value', 'Target Gross', 'Target Net']
                monthly_metrics = monthly_metrics.join(target_by_month, how='left').fillna(0)
            else:
                monthly_metrics['Target Volume'] = 0
                monthly_metrics['Target Value'] = 0
                monthly_metrics['Target Gross'] = 0
                monthly_metrics['Target Net'] = 0
                
            months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            monthly_metrics.index = pd.CategoricalIndex(monthly_metrics.index, categories=months_order, ordered=True)
            monthly_metrics = monthly_metrics.sort_index()
            months = monthly_metrics.index.astype(str).tolist()

            def make_3d_clustered(title, actual_col, target_col, container):
                """Render a clustered column chart using Plotly grouped bars."""
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Actual', x=months, y=monthly_metrics[actual_col],
                    marker=dict(color='#2196F3', opacity=0.92,
                                line=dict(color='#1565C0', width=1.2)),
                    width=0.35
                ))
                fig.add_trace(go.Bar(
                    name='Target', x=months, y=monthly_metrics[target_col],
                    marker=dict(color='#FF9800', opacity=0.85,
                                line=dict(color='#E65100', width=1.2)),
                    width=0.35
                ))
                fig.update_layout(
                    title=dict(text=title, font=dict(size=13)),
                    barmode='group', bargap=0.18, bargroupgap=0.06,
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                    plot_bgcolor='rgba(30,30,40,0.95)',
                    paper_bgcolor='rgba(30,30,40,0)',
                    font=dict(color='white'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.08)'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.08)'),
                    margin=dict(l=10, r=10, t=40, b=10),
                )
                container.plotly_chart(fig, use_container_width=True)

            def make_line(title, actual_col, target_col, container):
                """Render a line chart for Actuals vs Target."""
                container.write(f"**{title}**")
                container.line_chart(monthly_metrics[[actual_col, target_col]])

            if chart_type == "Clustered Column":
                make_3d_clustered("1. Monthly Volume: Actual vs Target", 'Actual Volume', 'Target Volume', bc1)
                make_3d_clustered("2. Monthly Value: Actual vs Target", 'Actual Value', 'Target Value', bc1)
                make_3d_clustered("3. Monthly Gross: Actual vs Target", 'Actual Gross', 'Target Gross', bc2)
                make_3d_clustered("4. Monthly Net: Actual vs Target", 'Actual Net', 'Target Net', bc2)
            else:
                make_line("1. Monthly Volume Actuals vs Target", 'Actual Volume', 'Target Volume', bc1)
                make_line("2. Monthly Value Actuals vs Target", 'Actual Value', 'Target Value', bc1)
                make_line("3. Monthly Gross Actuals vs Target", 'Actual Gross', 'Target Gross', bc2)
                make_line("4. Monthly Net Actuals vs Target", 'Actual Net', 'Target Net', bc2)
        else:
            st.warning("No data mapped for this segment in this timeframe.")