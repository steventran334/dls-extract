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

# ---------------- Color Definitions ----------------
COLOR_OPTIONS = {
    "Blue": "#0000FF",
    "Green": "#008000",
    "Red": "#FF0000",
    "Orange": "#FFA500",
    "Purple": "#800080",
    "Cyan": "#00FFFF",
    "Magenta": "#FF00FF",
    "Black": "#000000",
    "Grey": "#808080",
    "Gold": "#FFD700"
}
COLOR_NAMES = list(COLOR_OPTIONS.keys())

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

def get_svg_buffer(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="svg", bbox_inches='tight')
    return buf.getvalue()

# ---------------- Main Logic ----------------
if dls_file:
    xls = pd.ExcelFile(dls_file)
    sheets = xls.sheet_names
    
    selected_sheets = st.multiselect("Select DLS conditions to overlay", sheets, default=[sheets[0]] if sheets else [])

    if not selected_sheets:
        st.warning("Please select at least one condition.")
    else:
        # --- Sidebar Color Customization ---
        st.sidebar.header("🎨 Color Customization")
        color_mode = st.sidebar.radio("Color Assignment Priority:", ["Color by Condition", "Color by Weighting"])
        
        assigned_colors = {}
        if color_mode == "Color by Condition":
            st.sidebar.info("Default cycle: Blue, Green, Red, Orange, Purple")
            for i, sheet in enumerate(selected_sheets):
                default_ix = i % 5 
                choice = st.sidebar.selectbox(f"Color for {sheet}", COLOR_NAMES, index=default_ix, key=f"color_{sheet}")
                assigned_colors[sheet] = COLOR_OPTIONS[choice]
        else:
            st.sidebar.info("Assign colors to weightings (Intensity, Number, Volume).")
            for i, weight in enumerate(["Intensity", "Number", "Volume"]):
                choice = st.sidebar.selectbox(f"Color for {weight}", COLOR_NAMES, index=i, key=f"color_w_{weight}")
                assigned_colors[weight] = COLOR_OPTIONS[choice]

        # Axis Controls
        st.subheader("Axis Settings")
        c1, c2, c3 = st.columns(3)
        with c1:
            weight_type = st.radio("Select Weighting for Individual Graphs", ["Intensity", "Number", "Volume"])
        with c2:
            bs_x_max = st.number_input("Back Scatter Max (nm)", value=1000, step=100)
        with c3:
            madls_x_max = st.number_input("MADLS Max (nm)", value=1000, step=100)
            
        multi_weight_selection = st.multiselect("Select Weightings for Multi-Weighting Overlay", ["Intensity", "Number", "Volume"], default=["Intensity"])

        all_csvs = []
        
        def plot_multi_conditions(block, weight_names, x_limit, normalized=True, is_multi_weight=False):
            fig, ax = plt.subplots(figsize=(10, 6))
            global_max_y = 0
            if isinstance(weight_names, str):
                weight_names = [weight_names]
            
            for sheet in selected_sheets:
                df = pd.read_excel(xls, sheet_name=sheet, header=[0, 1, 2], skiprows=[0, 1])
                block_cols = get_block_cols(df, block)
                size_col = find_col_in_block(block_cols, "size")
                
                for weight_name in weight_names:
                    weight_key = weight_name.lower()
                    dist_col = find_col_in_block(block_cols, weight_key)
                    
                    if size_col is not None and dist_col is not None:
                        x = pd.to_numeric(df[size_col], errors='coerce').values
                        y = pd.to_numeric(df[dist_col], errors='coerce').values
                        msk = ~np.isnan(x) & ~np.isnan(y)
                        x, y = x[msk], y[msk]
                        
                        if len(x) > 0:
                            if normalized:
                                max_val = y.max()
                                if max_val > 0: y = y / max_val
                            
                            current_max = y.max() if len(y) > 0 else 0
                            if current_max > global_max_y: global_max_y = current_max

                            # Color Logic
                            if color_mode == "Color by Condition":
                                current_color = assigned_colors.get(sheet, "#000000")
                            else:
                                current_color = assigned_colors.get(weight_name, "#000000")
                            
                            label = f"{sheet}" if not is_multi_weight else f"{sheet} ({weight_name})"
                            ax.plot(x, y, label=label, lw=2, color=current_color)
                            
                            all_csvs.append((f"{sheet}_{block}_{weight_name}.csv", pd.DataFrame({"Size": x, "Value": y}).to_csv(index=False)))
        
            ax.set_xlim([0, x_limit])
            ax.set_ylim(0, (1.05 if normalized else global_max_y * 1.05))
            ax.set_xlabel("Diameter (nm)")
            ax.set_ylabel("% (Normalized)" if normalized else "% (Raw)")
            display_name = "Back Scatter" if block == "back" else "MADLS"
            ax.set_title(f"{display_name} - Overlay")
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            return fig

        # --- Section 1: Individual Weighting ---
        st.divider()
        st.subheader("Individual Weighting Graphs")
        col_bs, col_madls = st.columns(2)
        
        with col_bs:
            fig_bs = plot_multi_conditions("back", weight_type, bs_x_max)
            st.pyplot(fig_bs)
            st.download_button("Download BS SVG", get_svg_buffer(fig_bs), "back_scatter.svg", "image/svg+xml")

        with col_madls:
            fig_ma = plot_multi_conditions("madls", weight_type, madls_x_max)
            st.pyplot(fig_ma)
            st.download_button("Download MADLS SVG", get_svg_buffer(fig_ma), "madls.svg", "image/svg+xml")

        # --- Section 2: Multi-Weighting ---
        st.divider()
        st.subheader("Multi-Weighting Overlay Graph")
        col_multi_bs, col_multi_madls = st.columns(2)
        
        with col_multi_bs:
            fig_mbs = plot_multi_conditions("back", multi_weight_selection, bs_x_max, is_multi_weight=True)
            st.pyplot(fig_mbs)
            st.download_button("Download Multi-Weight BS SVG", get_svg_buffer(fig_mbs), "multi_weight_bs.svg", "image/svg+xml")

        with col_multi_madls:
            fig_mma = plot_multi_conditions("madls", multi_weight_selection, madls_x_max, is_multi_weight=True)
            st.pyplot(fig_mma)
            st.download_button("Download Multi-Weight MADLS SVG", get_svg_buffer(fig_mma), "multi_weight_madls.svg", "image/svg+xml")

        st.divider()
        st.download_button("Download All Data (CSV ZIP)", data=make_zip(all_csvs), file_name="dls_data.zip", mime="application/zip")

else:
    st.info("Upload a DLS Excel file to begin.")
