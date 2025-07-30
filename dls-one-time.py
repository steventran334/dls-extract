import streamlit as st
import pandas as pd
import numpy as np
import io

st.title("DLS Number-Weighted Data Exporter")

st.markdown("""
Upload your DLS Excel file and select the condition (sheet).  
This tool will export the number-weighted data for both Back scatter and MADLS, including normalized columns.
""")

dls_file = st.file_uploader("Upload DLS Excel file", type=["xlsx"])
sheet_selected = None

if dls_file:
    xls = pd.ExcelFile(dls_file)
    sheets = xls.sheet_names
    sheet_selected = st.selectbox("Select DLS condition (sheet)", sheets)
    dls = pd.read_excel(xls, sheet_name=sheet_selected, header=[0,1,2], skiprows=[0,1])

    # --- Extract correct columns by index (from your file structure) ---
    # Back scatter number-weighted
    back_size_col = dls.columns[7]
    back_number_col = dls.columns[10]
    back_size = dls[back_size_col].astype(float)
    back_number = dls[back_number_col].astype(float)
    back_max = back_number.max()
    back_norm = back_number / back_max if back_max > 0 else back_number

    # MADLS number-weighted
    madls_size_col = dls.columns[9]
    madls_number_col = dls.columns[12]
    madls_size = dls[madls_size_col].astype(float)
    madls_number = dls[madls_number_col].astype(float)
    madls_max = madls_number.max()
    madls_norm = madls_number / madls_max if madls_max > 0 else madls_number

    # --- Combine into one DataFrame for export ---
    out = pd.DataFrame({
        "Back Size (d.nm)": back_size,
        "Back Number (Percent)": back_number,
        "Back Number (Normalized)": back_norm,
        "MADLS Size (d.nm)": madls_size,
        "MADLS Number (Percent)": madls_number,
        "MADLS Number (Normalized)": madls_norm,
    })

    st.dataframe(out)

    # --- Download as CSV ---
    csv_buf = io.StringIO()
    out.to_csv(csv_buf, index=False)
    st.download_button(
        label="Download Number-Weighted Data (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"{sheet_selected}_number_weighted_normalized.csv",
        mime="text/csv"
    )
else:
    st.info("Upload a DLS Excel file and select a condition (sheet) to export number-weighted data.")
