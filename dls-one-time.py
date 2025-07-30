return col
return None

    def get_plot_and_csvs(main_types, title_prefix, x_min, x_max):
        plot_titles = [
            f"{title_prefix} - Intensity",
            f"{title_prefix} - Number",
            f"{title_prefix} - Volume",
        ]
    def get_overlay_plot_and_csvs(main_type, title_prefix, x_min, x_max):
weights = ["intensity", "number", "volume"]
        figs = []
        colors = ["black", "red", "blue"]
        labels = ["Intensity", "Number", "Volume"]
csv_files = []
        for main, weight, title in zip(main_types, weights, plot_titles):
            size_col = find_col(dls, main, "size")
            dist_col = find_col(dls, main, weight)
        fig, ax = plt.subplots(figsize=(7, 5))
        for weight, color, label in zip(weights, colors, labels):
            size_col = find_col(dls, main_type, "size")
            dist_col = find_col(dls, main_type, weight)
if size_col is None or dist_col is None:
continue
x = dls[size_col].astype(float).values
@@ -96,27 +93,23 @@ def get_plot_and_csvs(main_types, title_prefix, x_min, x_max):
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
            fname_base = f"{sheet_selected}_{title_prefix}_{label}"
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
        ax.set_title(title_prefix)
        ax.legend()
        plt.tight_layout()
        return fig, csv_files

def make_zip(name_pairs):
zip_buffer = io.BytesIO()
@@ -127,39 +120,19 @@ def make_zip(name_pairs):

# --- BACK SCATTER PREVIEW & DOWNLOAD ---
st.markdown(f"### Condition: `{back_title}`")
    st.subheader("Back Scatter Distributions")
    back_figs, back_csv_files = get_plot_and_csvs(["back"]*3, "Back Scatter", bs_x_min, bs_x_max)
    if back_figs:
        fig, axs = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
        fig.suptitle(f"{back_title}", fontsize=20, y=1.08)
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
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        st.pyplot(fig)
        # SVG download (as 1x3 panel)
    st.subheader("Back Scatter Distributions (Overlayed)")
    back_fig, back_csv_files = get_overlay_plot_and_csvs("back", back_title, bs_x_min, bs_x_max)
    if back_fig:
        st.pyplot(back_fig)
svg_buf = io.StringIO()
        fig.savefig(svg_buf, format="svg", bbox_inches='tight')
        back_fig.savefig(svg_buf, format="svg", bbox_inches='tight')
st.download_button(
            label="Download Back Scatter (1x3 SVG)",
            label="Download Back Scatter Overlay (SVG)",
data=svg_buf.getvalue(),
            file_name=f"{back_title}_BackScatter_1x3.svg",
            file_name=f"{back_title}_BackScatter_Overlay.svg",
mime="image/svg+xml"
)
        plt.close(fig)
        plt.close(back_fig)
st.download_button(
label="Download All Back Scatter CSVs (ZIP)",
data=make_zip(back_csv_files),
@@ -169,39 +142,19 @@ def make_zip(name_pairs):

# --- MADLS PREVIEW & DOWNLOAD ---
st.markdown(f"### Condition: `{madls_title}`")
    st.subheader("MADLS Distributions")
    madls_figs, madls_csv_files = get_plot_and_csvs(["madls"]*3, "MADLS", madls_x_min, madls_x_max)
    if madls_figs:
        fig, axs = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
        fig.suptitle(f"{madls_title}", fontsize=20, y=1.08)
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
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        st.pyplot(fig)
        # SVG download (as 1x3 panel)
    st.subheader("MADLS Distributions (Overlayed)")
    madls_fig, madls_csv_files = get_overlay_plot_and_csvs("madls", madls_title, madls_x_min, madls_x_max)
    if madls_fig:
        st.pyplot(madls_fig)
svg_buf = io.StringIO()
        fig.savefig(svg_buf, format="svg", bbox_inches='tight')
        madls_fig.savefig(svg_buf, format="svg", bbox_inches='tight')
st.download_button(
            label="Download MADLS (1x3 SVG)",
            label="Download MADLS Overlay (SVG)",
data=svg_buf.getvalue(),
            file_name=f"{madls_title}_MADLS_1x3.svg",
            file_name=f"{madls_title}_MADLS_Overlay.svg",
mime="image/svg+xml"
)
        plt.close(fig)
        plt.close(madls_fig)
st.download_button(
label="Download All MADLS CSVs (ZIP)",
data=make_zip(madls_csv_files),
