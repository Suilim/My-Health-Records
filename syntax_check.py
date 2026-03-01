try:
    from plot_utils import create_combined_chart
    print("plot_utils imported successfully")
except Exception as e:
    print(f"Error importing plot_utils: {e}")

try:
    import pages
    # Can't easily import pages/7... because of filename and streamlit context
    print("Skipping pages import check, relying on plot_utils check")
except:
    pass
