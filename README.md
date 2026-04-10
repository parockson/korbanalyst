🚀 KorbaAnalyst
KorbaAnalyst is a high-performance Streamlit dashboard designed for the Korba reconciliation team. It automates the processing of monthly transaction CSVs, allowing for individual column mapping, data cleaning (including SMB category corrections), and the generation of detailed segment-based financial reports.

✨ Key Features
Multi-File Processing: Upload and merge multiple monthly CSV files (e.g., Oct, Nov, Dec) in one go.

Flexible Schema Mapping: Manually match headers for each file individually to handle inconsistent naming conventions (e.g., "Name" vs "Business_Name").

Automated Data Cleaning:

Automatically fixes the SMB "Disbursement 2" to "Data Purchase" mapping.

Handles missing business names and cleans hidden spaces in headers.

Robust numeric conversion for Debit and Margin columns.

Segmented Reporting:

Master Summary: BizSegment & Category-level aggregation.

Corporate: Deep dive by Category and Business Name.

Retail: Aggregation by Category.

SMB: Analysis by Category and Sender Wallet (Zone) analysis.

One-Click Export: Download all generated reports into a single, multi-sheet Excel workbook.

🛠️ Installation & Setup
1. Clone or Download
Ensure you have the following files in your project folder:

app.py

requirements.txt

2. Create and Activate Virtual Environment
Open your terminal (PowerShell recommended) and run:

PowerShell
# Create the environment
python -m venv .venv

# Activate the environment
.\.venv\Scripts\activate
3. Install Dependencies
With the environment active, install the required libraries:

PowerShell
pip install -r requirements.txt
🚀 How to Run
To launch the dashboard locally, run:

PowerShell
streamlit run app.py
The app will automatically open in your default web browser (usually at http://localhost:8501).

📖 Usage Guide
Upload: Drag and drop your transaction CSVs into the uploader.

Map: For each file, expand the mapping section and ensure the dropdowns match the headers in your file (the app will try to auto-detect them).

Process: Click "Process & Generate Reports".

Analyze: View the interactive tables and metrics on the dashboard.

Export: Scroll to the bottom and click "Download All Reports as Excel" for your final documentation.

📁 Project Structure
Plaintext
korbanalyst/
├── .venv/               # Virtual environment (hidden)
├── app.py               # Main Streamlit application logic
├── requirements.txt     # List of Python dependencies
└── README.md            # Project documentation