import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import zipfile

st.set_page_config(page_title="DLS Multi-Condition Overlay", layout="wide")
st.title("DLS Distributions Preview & Export")

st.markdown("""
<div style="background-color:#E8F0FE;padding:16px 24px 16px 24px;border-radius:14px;margin-bottom:20px;">
<b>Instructions:</b><br>
Select multiple conditions to overlay them on the same graph. 
<ul style="margin-top:0;margin-bottom:0;">
<li><b>Back scatter:</b> Columns A-F</li>
<li><b>MADLS:</b> Columns H-M</li>
</ul>
</div>
""", unsafe_allow_html=True)

dls_file = st.file_uploader("Upload DLS Excel file", type=["xlsx"])

# ---------------- Helper functions ----------------
def get_block_cols(df, block):
    if block == "back":
        return df.columns[:6]
    elif block == "madls":
        return df.columns[7:13]
    return None

def find_col_in_block(block_cols, keyword):
    for col in block_cols:
        col_str = ' '.join(str(c).lower() for c in col)
        if keyword in col_str:
            return col
    return None

def make_zip(name_pairs):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for fname, data in name_pairs:
            zf.writestr(fname, data)
    return zip_buffer.getvalue()

# ---------------- Main Logic ----------------
if dls_file:
    xls = pd.ExcelFile(dls_file)
    sheets = xls.sheet_names
    
    # Feature: Multi-select conditions
    selected_sheets = st.multiselect("Select DLS conditions to overlay", sheets, default=[sheets[0]] if sheets else [])

    if not selected_sheets:
        st.warning("Please select at least one condition.")
    else:
        # X-Axis Global Controls
        st.subheader("Axis Settings")
        c1, c2, c3 = st.columns(3)
        with c1:
            weight_type = st.radio("Select Weighting to Display", ["Intensity", "Number", "Volume"])
        with c2:
            bs_x_max = st.number_input("Back Scatter Max (nm)", value=1000, step=100)
        with c3:
            madls_x_max = st.number_input("MADLS Max (nm)", value=1000, step=100)

        # Storage for ZIP files
        all_csvs = []
        
        def plot_multi_conditions(block, weight_name, x_limit, normalized=True):
            fig, ax = plt.subplots(figsize=(10, 6))
            weight_key = weight_name.lower()
            
            for sheet in selected_sheets:
                df = pd.read_excel(xls, sheet_name=sheet, header=[0, 1, 2], skiprows=[0, 1])
                block_cols = get_block_cols(df, block)
                
                size_col = find_col_in_block(block_cols, "size")
                dist_col = find_col_in_block(block_cols, weight_key)
                
                if size_col is not None and dist_col is not None:
                    x = df[size_col].astype(float).values
                    y = df[dist_col].astype(float).values
                    msk = ~np.isnan(x) & ~np.isnan(y)
                    x, y = x[msk], y[msk]
                    
                    if normalized:
                        max_y = y.max()
                        y = y / max_y if max_y > 0 else y
                    
                    ax.plot(x, y, label=f"{sheet}", lw=2)
                    
                    df_csv = pd.DataFrame({"Diameter (nm)": x, f"{weight_name} (%)": y})
                    all_csvs.append((f"{sheet}_{block}_{weight_name}_{'norm' if normalized else 'raw'}.csv", df_csv.to_csv(index=False)))
        
            ax.set_xlim([0, x_limit])
            ax.set_xlabel("Diameter (nm)")
            ax.set_ylabel("% (Normalized)" if normalized else "% (Raw)")
            
            # Updated Title Logic
            display_name = "Back Scatter" if block == "back" else "MADLS"
            ax.set_title(f"{display_name} - {weight_name} Overlay")
            
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            return fig

        # Display Sections
        col_bs, col_madls = st.columns(2)

        with col_bs:
            st.subheader("Back Scatter")
            fig_bs = plot_multi_conditions("back", weight_type, bs_x_max, normalized=True)
            st.pyplot(fig_bs)
            
            buf_bs = io.StringIO()
            fig_bs.savefig(buf_bs, format="svg")
            st.download_button("Download BS SVG", buf_bs.getvalue(), "back_scatter_overlay.svg", "image/svg+xml")

        with col_madls:
            st.subheader("MADLS")
            fig_ma = plot_multi_conditions("madls", weight_type, madls_x_max, normalized=True)
            st.pyplot(fig_ma)
            
            buf_ma = io.StringIO()
            fig_ma.savefig(buf_ma, format="svg")
            st.download_button("Download MADLS SVG", buf_ma.getvalue(), "madls_overlay.svg", "image/svg+xml")

        st.divider()
        st.download_button("Download All Selected Data (CSV ZIP)", 
                           data=make_zip(all_csvs), 
                           file_name="dls_overlay_data.zip", 
                           mime="application/zip")

else:
    st.info("Upload a DLS Excel file to begin.")
