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


# --------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------
def get_block_cols(dls, block):
    """Return the column block for back scatter or MADLS."""
    if block == "back":
        return dls.columns[:6]
    elif block == "madls":
        return dls.columns[7:13]
    else:
        raise ValueError("block must be 'back' or 'madls'")


def find_col_in_block(dls, block_cols, keyword):
    """Find a column in the block that contains a keyword."""
    for col in block_cols:
        col_str = ' '.join(str(c).lower() for c in col)
        if keyword in col_str:
            return col
    return None


# --------------------------------------------------------------------
# Main app
# --------------------------------------------------------------------
if dls_file:
    xls = pd.ExcelFile(dls_file)
    sheets = xls.sheet_names
    sheet_selected = st.selectbox("Select DLS condition (sheet)", sheets)
    dls = pd.read_excel(xls, sheet_name=sheet_selected, header=[0, 1, 2], skiprows=[0, 1])

    # --- X-Axis Range Numeric Inputs ---
    st.subheader("X-Axis Ranges (Diameter in nm)")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Back Scatter X-Axis Limits**")
        bs_x_min = st.number_input("Back Scatter Min (nm)", min_value=0, max_value=5000, value=0, step=10, key="bs_xmin")
        bs_x_max = st.number_input("Back Scatter Max (nm)", min_value=0, max_value=5000, value=1000, step=10, key="bs_xmax")

    with col2:
        st.markdown("**MADLS X-Axis Limits**")
        madls_x_min = st.number_input("MADLS Min (nm)", min_value=0, max_value=5000, value=0, step=10, key="madls_xmin")
        madls_x_max = st.number_input("MADLS Max (nm)", min_value=0, max_value=5000, value=1000, step=10, key="madls_xmax")

    # ----------------------------------------------------------------
    # Editable titles for each plot group (auto-reset when sheet changes)
    # ----------------------------------------------------------------
    st.subheader("Custom Titles (Optional)")

    if "last_sheet" not in st.session_state:
        st.session_state.last_sheet = None
    if st.session_state.last_sheet != sheet_selected:
        st.session_state.back_title = sheet_selected
        st.session_state.madls_title = sheet_selected
        st.session_state.last_sheet = sheet_selected

    col3, col4 = st.columns(2)
    with col3:
        back_title = st.text_input(
            "Back Scatter Plot Title",
            value=st.session_state.get("back_title", sheet_selected),
            key="back_title_input"
        )
        st.session_state.back_title = back_title

    with col4:
        madls_title = st.text_input(
            "MADLS Plot Title",
            value=st.session_state.get("madls_title", sheet_selected),
            key="madls_title_input"
        )
        st.session_state.madls_title = madls_title

    # ----------------------------------------------------------------
    # Plot generation functions
    # ----------------------------------------------------------------
    def get_overlay_plot_and_csvs(block, title_prefix, x_min, x_max):
        weights = ["intensity", "number", "volume"]
        colors = ["black", "red", "blue"]
        labels = ["Intensity", "Number", "Volume"]
        csv_files = []
        fig, ax = plt.subplots(figsize=(7, 5))
        block_cols = get_block_cols(dls, block)

        for weight, color, label in zip(weights, colors, labels):
            size_col = find_col_in_block(dls, block_cols, "size")
            dist_col = find_col_in_block(dls, block_cols, weight)
            if size_col is None or dist_col is None:
                st.warning(f"Could not find {weight} column for {block}.")
                continue
            x = dls[size_col].astype(float).values
            y = dls[dist_col].astype(float).values
            msk = ~np.isnan(x) & ~np.isnan(y)
            x, y = x[msk], y[msk]
            max_y = y.max()
            y_norm = y / max_y if max_y > 0 else y

            # CSV Output
            df_csv = pd.DataFrame({
                "DLS Diameter (nm)": x,
                f"DLS {weight.capitalize()} (%)": y,
                f"DLS {weight.capitalize()} (normalized by max)": y_norm
            })
            fname_base = f"{title_prefix}_{block}_{label}"
            csv_files.append((f"{fname_base}.csv", df_csv.to_csv(index=False)))

            # Overlay plot
            ax.plot(x, y_norm, label=label, color=color, lw=2)

        ax.set_xlim([x_min, x_max])
        n_ticks = 6
        xticks = np.linspace(x_min, x_max, n_ticks)
        ax.set_xticks(xticks)
        ax.set_xticklabels([str(int(t)) for t in xticks])
        ax.set_xlabel("Diameter (nm)")
        ax.set_ylabel("% (normalized)")
        ax.set_title(title_prefix + " (Normalized)")
        ax.legend()
        plt.tight_layout()
        return fig, csv_files


    def get_overlay_plot_and_csvs_raw(block, title_prefix, x_min, x_max):
        weights = ["intensity", "number", "volume"]
        colors = ["black", "red", "blue"]
        labels = ["Intensity", "Number", "Volume"]
        fig, ax = plt.subplots(figsize=(7, 5))
        block_cols = get_block_cols(dls, block)
        for weight, color, label in zip(weights, colors, labels):
            size_col = find_col_in_block(dls, block_cols, "size")
            dist_col = find_col_in_block(dls, block_cols, weight)
            if size_col is None or dist_col is None:
                st.warning(f"Could not find {weight} column for {block}.")
                continue
            x = dls[size_col].astype(float).values
            y = dls[dist_col].astype(float).values
            msk = ~np.isnan(x) & ~np.isnan(y)
            x, y = x[msk], y[msk]
            ax.plot(x, y, label=label, color=color, lw=2)
        ax.set_xlim([x_min, x_max])
        n_ticks = 6
        xticks = np.linspace(x_min, x_max, n_ticks)
        ax.set_xticks(xticks)
        ax.set_xticklabels([str(int(t)) for t in xticks])
        ax.set_xlabel("Diameter (nm)")
        ax.set_ylabel("% (raw)")
        ax.set_title(title_prefix + " (Raw Data)")
        ax.legend()
        plt.tight_layout()
        return fig


    def make_zip(name_pairs):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for fname, data in name_pairs:
                zf.writestr(fname, data)
        return zip_buffer.getvalue()

    # ----------------------------------------------------------------
    # BACK SCATTER PREVIEW & DOWNLOAD
    # ----------------------------------------------------------------
    st.markdown(f"### Condition: `{back_title}`")
    st.subheader("Back Scatter Distributions (Overlayed, Normalized)")
    back_fig, back_csv_files = get_overlay_plot_and_csvs("back", back_title, bs_x_min, bs_x_max)
    if back_fig:
        st.pyplot(back_fig)
        svg_buf = io.StringIO()
        back_fig.savefig(svg_buf, format="svg", bbox_inches='tight')
        st.download_button(
            label="Download Back Scatter Overlay (SVG)",
            data=svg_buf.getvalue(),
            file_name=f"{back_title}_BackScatter_Overlay.svg",
            mime="image/svg+xml"
        )
        plt.close(back_fig)
        st.download_button(
            label="Download All Back Scatter CSVs (ZIP)",
            data=make_zip(back_csv_files),
            file_name=f"{back_title}_BackScatter_CSVs.zip",
            mime="application/zip"
        )

    # --- BACK SCATTER RAW PLOT ---
    st.subheader("Back Scatter Distributions (Overlayed, Raw Data)")
    back_fig_raw = get_overlay_plot_and_csvs_raw("back", back_title, bs_x_min, bs_x_max)
    if back_fig_raw:
        st.pyplot(back_fig_raw)
        svg_buf_raw = io.StringIO()
        back_fig_raw.savefig(svg_buf_raw, format="svg", bbox_inches='tight')
        st.download_button(
            label="Download Back Scatter Overlay (Raw, SVG)",
            data=svg_buf_raw.getvalue(),
            file_name=f"{back_title}_BackScatter_Overlay_RAW.svg",
            mime="image/svg+xml"
        )
        plt.close(back_fig_raw)

    # ----------------------------------------------------------------
    # MADLS PREVIEW & DOWNLOAD
    # ----------------------------------------------------------------
    st.markdown(f"### Condition: `{madls_title}`")
    st.subheader("MADLS Distributions (Overlayed, Normalized)")
    madls_fig, madls_csv_files = get_overlay_plot_and_csvs("madls", madls_title, madls_x_min, madls_x_max)
    if madls_fig:
        st.pyplot(madls_fig)
        svg_buf = io.StringIO()
        madls_fig.savefig(svg_buf, format="svg", bbox_inches='tight')
        st.download_button(
            label="Download MADLS Overlay (SVG)",
            data=svg_buf.getvalue(),
            file_name=f"{madls_title}_MADLS_Overlay.svg",
            mime="image/svg+xml"
        )
        plt.close(madls_fig)
        st.download_button(
            label="Download All MADLS CSVs (ZIP)",
            data=make_zip(madls_csv_files),
            file_name=f"{madls_title}_MADLS_CSVs.zip",
            mime="application/zip"
        )

    # --- MADLS RAW PLOT ---
    st.subheader("MADLS Distributions (Overlayed, Raw Data)")
    madls_fig_raw = get_overlay_plot_and_csvs_raw("madls", madls_title, madls_x_min, madls_x_max)
    if madls_fig_raw:
        st.pyplot(madls_fig_raw)
        svg_buf_raw = io.StringIO()
        madls_fig_raw.savefig(svg_buf_raw, format="svg", bbox_inches='tight')
        st.download_button(
            label="Download MADLS Overlay (Raw, SVG)",
            data=svg_buf_raw.getvalue(),
            file_name=f"{madls_title}_MADLS_Overlay_RAW.svg",
            mime="image/svg+xml"
        )
        plt.close(madls_fig_raw)

else:
    st.info("Upload a DLS Excel file and select a condition (sheet) to view plots and downloads.")
