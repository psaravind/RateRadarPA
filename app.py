import streamlit as st
import pandas as pd
import subprocess
import os
import glob
import time
from pathlib import Path

# Configure the Streamlit page
st.set_page_config(
    page_title="PA Energy Rate Finder",
    page_icon="⚡",
    layout="centered"
)

def setup_output_directory():
    """Create output directory if it doesn't exist."""
    Path("output").mkdir(exist_ok=True)

def get_latest_csv(zipcode: str, energy_type: str) -> str:
    """
    Find the most recent CSV file for the given zipcode and energy type.
    
    Args:
        zipcode (str): The ZIP code to search for
        energy_type (str): Either 'Electricity' or 'Gas'
    
    Returns:
        str: Path to the latest CSV file
    """
    prefix = "papowerswitch" if energy_type == "Electricity" else "pagasswitch"
    pattern = f"output/{prefix}_filtered_{zipcode}_*.csv"
    files = glob.glob(pattern)
    
    if not files:
        raise FileNotFoundError(f"No CSV files found for ZIP code {zipcode}")
    
    return max(files, key=os.path.getctime)

def run_scraper(zipcode: str, energy_type: str, headless: bool = True):
    """
    Run the appropriate scraper based on energy type.
    
    Args:
        zipcode (str): The ZIP code to scrape
        energy_type (str): Either 'Electricity' or 'Gas'
        headless (bool): Whether to run in headless mode
    """
    script = "papowerswitch_export_scraper.py" if energy_type == "Electricity" else "pagasswitch_export_scraper.py"
    cmd = ["python", script, "--zipcode", zipcode]
    
    if headless:
        cmd.append("--headless")
    
    subprocess.run(cmd, check=True)

def main():
    # Create output directory
    setup_output_directory()
    
    # App title and description
    st.title("⚡ PA Energy Rate Finder")
    st.markdown("""
    Find the best energy rates in Pennsylvania by entering your ZIP code below.
    Choose between electricity or gas rates, and we'll fetch the latest prices for you.
    """)
    
    # Input fields
    col1, col2 = st.columns(2)
    with col1:
        zipcode = st.text_input("Enter ZIP Code (PA only):", "")
    with col2:
        energy_type = st.radio("Select Energy Type:", ["Electricity", "Gas"])
    
    headless = st.checkbox("Run in headless mode", True)
    
    # Fetch rates button
    if st.button("Fetch Rates", type="primary"):
        if not zipcode.strip():
            st.warning("⚠️ Please enter a ZIP code.")
        else:
            try:
                with st.spinner("🔍 Scraping rates in progress..."):
                    # Run the scraper
                    run_scraper(zipcode, energy_type, headless)
                    
                    # Get and display results
                    latest_file = get_latest_csv(zipcode, energy_type)
                    df = pd.read_csv(latest_file)
                    
                    st.success("✅ Done! Here are the latest rates:")
                    
                    # Display the dataframe with some styling
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Add download button
                    st.download_button(
                        "📥 Download Results",
                        df.to_csv(index=False),
                        file_name=f"energy_rates_{zipcode}_{energy_type.lower()}.csv",
                        mime="text/csv"
                    )
                    
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                st.info("Please make sure you have the required scraper scripts installed and try again.")

if __name__ == "__main__":
    main() 