import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("DLS Data 2x3 Plotter")

uploaded_file = st.file_uploader("Upload your DLS Excel file", type=["xlsx"])
weightings = ["intensity", "number", "volume"]
dls_types = ["MADLS", "Back Scatter"]  # For reference in grid

if uploaded_file is not None:
    # Read all sheets at once
    sheets = pd.read_excel(uploaded_file, sheet_name=None)

    # Sheet order: intensity, number, volume
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True)
    plt.subplots_adjust(hspace=0.3, wspace=0.2)

    for col_idx, weighting in enumerate(weightings):
        df = sheets[weighting]
        
        # MADLS: Columns A-G (first 7 columns, index 0-6)
        madls_df = df.iloc[:, 0:7]
        # Back Scatter: Columns J-P (10-16)
        back_df = df.iloc[:, 9:16]

        # The first column is diameter (nm)
        diameter_madls = madls_df.iloc[:, 0]
        diameter_back = back_df.iloc[:, 0]

        # Experiment/condition names (skip diameter column)
        madls_conditions = madls_df.columns[1:]
        back_conditions = back_df.columns[1:]

        # Plot MADLS
        ax_madls = axes[1, col_idx]
        for cond in madls_conditions:
            y = madls_df[cond]
            ax_madls.plot(diameter_madls, y, label=cond)
        ax_madls.set_title(f"MADLS - {weighting.title()}")
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
        ax_back.set_title(f"Back Scatter - {weighting.title()}")
        ax_back.set_xlim(0, 1000)
        ax_back.set_xlabel("Diameter (nm)")
        if col_idx == 0:
            ax_back.set_ylabel("Value")
        ax_back.legend(fontsize=7)

    st.pyplot(fig)
