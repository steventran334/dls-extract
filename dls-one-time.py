import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("DLS Data 2x3 Plotter")

uploaded_file = st.file_uploader("Upload your DLS Excel file", type=["xlsx"])
weightings = ["Intensity", "Number", "Volume"]

if uploaded_file is not None:
    sheets = pd.read_excel(uploaded_file, sheet_name=None)
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True)
    plt.subplots_adjust(hspace=0.3, wspace=0.2)

    for col_idx, weighting in enumerate(weightings):
        df = sheets[weighting]

        # MADLS columns: A-G ("Diameter (nm)", then 6 conditions)
        madls_cols = [col for col in df.columns[:7] if "Diameter" in col or "MB" in col or "NB" in col or "Stock" in col]
        madls_df = df[madls_cols].dropna(subset=[madls_cols[0]])
        diameter_madls = madls_df.iloc[:, 0]
        madls_conditions = madls_df.columns[1:]

        # Back Scatter columns: J-P (columns 9 to 15, zero-indexed)
        back_cols = [col for col in df.columns[9:16] if "Diameter" in col or "MB" in col or "NB" in col or "Stock" in col]
        back_df = df[back_cols].dropna(subset=[back_cols[0]])
        diameter_back = back_df.iloc[:, 0]
        back_conditions = back_df.columns[1:]

        # Plot MADLS
        ax_madls = axes[1, col_idx]
        for cond in madls_conditions:
            y = madls_df[cond]
            ax_madls.plot(diameter_madls, y, label=cond)
        ax_madls.set_title(f"MADLS - {weighting}")
        ax_madls.set_xlim(0, 1000)
        ax_madls.set_xlabel("Diameter (nm)")
        if col_idx == 0:
            ax_madls.set_ylabel("Value")
        ax_madls.legend(fontsize=7)

        # Plot Back Scatter
        ax_back = axes[0, col_idx]
        for cond in back_conditions:
            y = back_df[cond]
            ax_back.plot(diameter_back, y, label=cond)
        ax_back.set_title(f"Back Scatter - {weighting}")
        ax_back.set_xlim(0, 1000)
        ax_back.set_xlabel("Diameter (nm)")
        if col_idx == 0:
            ax_back.set_ylabel("Value")
        ax_back.legend(fontsize=7)

    st.pyplot(fig)
