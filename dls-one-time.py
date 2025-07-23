import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import zipfile

st.title("DLS Distributions Preview & Export")

st.markdown("""
<div style="background-color:#E8F0FE;padding:16px 24px 16px 24px;border-radius:14px;margin-bottom:20px;">
<b>Instructions:</b><br>
<b>DLS graphs must be formatted exactly:</b>
<ul style="margin-top:0;margin-bottom:0;">
<li>Sheet name: name of experiment (e.g. stock of NBs)</li>
<li>Back scatter data: in columns starting at column A</li>
<li>MADLS data: in columns starting at column H</li>
<li>Each contains intensity, number, and volume weighted distributions</li>
</ul>
Drop your file below.
</div>
""", unsafe_allow_html=True)

st.image("dls_example.png", caption="Example DLS spreadsheet format", use_container_width=True)

dls_file = st.file_uploader("Upload DLS Excel file", type=["xlsx"])
sheet_selected = None

if dls_file:
    xls = pd.ExcelFile(dls_file)
    sheets = xls.sheet_names
    sheet_selected = st.selectbox("Select DLS condition (sheet)", sheets)
    dls = pd.read_excel(xls, sheet_name=sheet_selected, header=[0,1,2], skiprows=[0,1])

    # --- X-Axis Range Selectors ---
    st.subheader("X-Axis Ranges (Diameter in nm)")

    bs_x_min, bs_x_max = st.slider(
        "Back Scatter: Set the x-axis (diameter) range",
        min_value=0, max_value=5000, value=(0, 1000), step=10, key="bs_slider"
    )

    madls_x_min, madls_x_max = st.slider(
        "MADLS: Set the x-axis (diameter) range",
        min_value=0, max_value=5000, value=(0, 1000), step=10, key="madls_slider"
    )

    def find_col(dls, type_main, weight):
        for col in dls.columns:
            col_str = ' '.join(str(c).lower() for c in col)
            if type_main in col_str and weight in col_str:
                return col
        return None

    def get_plot_and_csvs(main_types, title_prefix, x_min, x_max):
        plot_titles = [
            f"{title_prefix} - Intensity",
            f"{title_prefix} - Number",
            f"{title_prefix} - Volume",
        ]
        weights = ["intensity", "number", "volume"]
        figs = []
        csv_files = []
        for main, weight, title in zip(main_types, weights, plot_titles):
            size_col = find_col(dls, main, "size")
            dist_col = find_col(dls, main, weight)
            if size_col is None or dist_col is None:
                continue
            x = dls[size_col].astype(float).values
            y = dls[dist_col].astype(float).values
            msk = ~np.isnan(x) & ~np.isnan(y)
            x, y = x[msk], y[msk]
            y_norm = y / np.max(y) if np.max(y) > 0 else y

            # CSV Output
            df_csv = pd.DataFrame({
                "DLS Diameter (nm)": x,
                f"DLS {weight.capitalize()} (%)": y,
                f"DLS {weight.capitalize()} (normalized by max)": y_norm
            })

            # Plot
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.plot(x, y_norm, label="DLS", color='black', lw=2)
            ax.set_xlim([x_min, x_max])
            n_ticks = 6
            xticks = np.linspace(x_min, x_max, n_ticks)
            ax.set_xticks(xticks)
            ax.set_xticklabels([str(int(t)) for t in xticks])
            ax.set_xlabel("Diameter (nm)")
            ax.set_ylabel("%")
            ax.set_title(title)
            ax.legend()
            figs.append(fig)

            # Save CSV in memory for zipping
            csv_data = df_csv.to_csv(index=False)
            fname_base = f"{sheet_selected}_{title.replace(' ','_')}"
            csv_files.append((f"{fname_base}.csv", csv_data))
            plt.close(fig)
        return figs, csv_files

    def make_zip(name_pairs):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for fname, data in name_pairs:
                zf.writestr(fname, data)
        return zip_buffer.getvalue()

    # --- BACK SCATTER PREVIEW & DOWNLOAD ---
    st.subheader("Back Scatter Distributions")
    back_figs, back_csv_files = get_plot_and_csvs(["back"]*3, "Back Scatter", bs_x_min, bs_x_max)
    if back_figs:
        fig, axs = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
        for i, f in enumerate(back_figs):
            ax = axs[i]
            tmp = f.axes[0]
            for line in tmp.lines:
                ax.plot(line.get_xdata(), line.get_ydata(),
                        label=line.get_label(), color=line.get_color(),
                        lw=line.get_linewidth(), linestyle=line.get_linestyle())
            ax.set_xlim(tmp.get_xlim())
            ax.set_ylim(tmp.get_ylim())
            ax.set_xticks(tmp.get_xticks())
            ax.set_xticklabels(tmp.get_xticklabels())
            ax.set_xlabel(tmp.get_xlabel())
            ax.set_title(tmp.get_title())
            if i == 0:
                ax.set_ylabel(tmp.get_ylabel())
            ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
        # SVG download (as 1x3 panel)
        svg_buf = io.StringIO()
        fig.savefig(svg_buf, format="svg", bbox_inches='tight')
        st.download_button(
            label="Download Back Scatter (1x3 SVG)",
            data=svg_buf.getvalue(),
            file_name=f"{sheet_selected}_BackScatter_1x3.svg",
            mime="image/svg+xml"
        )
        plt.close(fig)
        st.download_button(
            label="Download All Back Scatter CSVs (ZIP)",
            data=make_zip(back_csv_files),
            file_name=f"{sheet_selected}_BackScatter_CSVs.zip",
            mime="application/zip"
        )

    # --- MADLS PREVIEW & DOWNLOAD ---
    st.subheader("MADLS Distributions")
    madls_figs, madls_csv_files = get_plot_and_csvs(["madls"]*3, "MADLS", madls_x_min, madls_x_max)
    if madls_figs:
        fig, axs = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
        for i, f in enumerate(madls_figs):
            ax = axs[i]
            tmp = f.axes[0]
            for line in tmp.lines:
                ax.plot(line.get_xdata(), line.get_ydata(),
                        label=line.get_label(), color=line.get_color(),
                        lw=line.get_linewidth(), linestyle=line.get_linestyle())
            ax.set_xlim(tmp.get_xlim())
            ax.set_ylim(tmp.get_ylim())
            ax.set_xticks(tmp.get_xticks())
            ax.set_xticklabels(tmp.get_xticklabels())
            ax.set_xlabel(tmp.get_xlabel())
            ax.set_title(tmp.get_title())
            if i == 0:
                ax.set_ylabel(tmp.get_ylabel())
            ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
        # SVG download (as 1x3 panel)
        svg_buf = io.StringIO()
        fig.savefig(svg_buf, format="svg", bbox_inches='tight')
        st.download_button(
            label="Download MADLS (1x3 SVG)",
            data=svg_buf.getvalue(),
            file_name=f"{sheet_selected}_MADLS_1x3.svg",
            mime="image/svg+xml"
        )
        plt.close(fig)
        st.download_button(
            label="Download All MADLS CSVs (ZIP)",
            data=make_zip(madls_csv_files),
            file_name=f"{sheet_selected}_MADLS_CSVs.zip",
            mime="application/zip"
        )

else:
    st.info("Upload a DLS Excel file and select a condition (sheet) to view plots and downloads.")
