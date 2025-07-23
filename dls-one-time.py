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

        # MADLS: A = Diameter (nm), B-G = conditions (index 0–6)
        diameter_madls = df.iloc[:, 0]
        madls_conditions = df.columns[1:7]  # B-G
        # Back Scatter: J = Diameter (nm), K-P = conditions (index 9–15)
        diameter_back = df.iloc[:, 9]
        back_conditions = df.columns[10:16]  # K-P

        # Plot MADLS
        ax_madls = axes[1, col_idx]
        for cond in madls_conditions:
            y = df[cond]
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
            y = df[cond]
            ax_back.plot(diameter_back, y, label=cond)
        ax_back.set_title(f"Back Scatter - {weighting}")
        ax_back.set_xlim(0, 1000)
        ax_back.set_xlabel("Diameter (nm)")
        if col_idx == 0:
            ax_back.set_ylabel("Value")
        ax_back.legend(fontsize=7)

    st.pyplot(fig)
