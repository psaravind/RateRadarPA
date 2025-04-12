#!/usr/bin/env python3
"""
PA Power Switch Export Scraper

This script automates the process of retrieving electricity rates from the PA Power Switch website
by using Selenium to navigate to the website, enter a zipcode, and click the "Export to CSV" button.
It then processes the downloaded CSV file to extract and filter the relevant data.
"""

import os
import sys
import time
import glob
import shutil
import logging
import argparse
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager

# Create output directory if it doesn't exist
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(output_dir, "papowerswitch_export_scraper.log")),
        logging.StreamHandler(sys.stdout)
    ]
)

class PAPowerSwitchExportScraper:
    def __init__(self, output_dir='output', headless=True, max_retries=3, retry_delay=5, zipcode='19348'):
        """Initialize the scraper with configuration options"""
        # Base URL with all parameters pre-set for direct navigation
        self.base_url = f"https://www.papowerswitch.com/shop-for-rates-results?zip={zipcode}&distributor=1182&distributorrate=R%20-%20Regular%20Residential%20Service&servicetype=residential&usage=700&min-price=&max-price=&ratePreferences%5B%5D=fixed&offerPreferences%5B%5D=no_cancellation&offerPreferences%5B%5D=no_enrollment&offerPreferences%5B%5D=no_monthly&offerPreferences%5B%5D=introductory_prices&sortby=est_a"
        self.output_dir = output_dir
        self.headless = headless
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.zipcode = zipcode
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up Chrome options
        self.chrome_options = Options()
        if self.headless:
            self.chrome_options.add_argument("--headless=new")
        
        # Add additional options for stability
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-notifications")
        self.chrome_options.add_argument("--disable-infobars")
        self.chrome_options.add_argument("--start-maximized")
        
        # Set download directory to output directory
        prefs = {
            "download.default_directory": os.path.abspath(self.output_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False
        }
        self.chrome_options.add_experimental_option("prefs", prefs)
        
        # Initialize driver to None (will be set up later)
        self.driver = None
        
        logging.info("PA Power Switch Export Scraper initialized")
        logging.info(f"Output directory: {self.output_dir}")
        logging.info(f"Headless mode: {self.headless}")
        logging.info(f"Max retries: {self.max_retries}")
        logging.info(f"Retry delay: {self.retry_delay} seconds")
        logging.info(f"Zipcode: {self.zipcode}")
    
    def setup_driver(self):
        """Set up the Chrome WebDriver"""
        try:
            # Use a different approach for macOS
            import platform
            if platform.system() == 'Darwin':  # macOS
                # Try to use the system Chrome directly
                self.chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
                driver = webdriver.Chrome(options=self.chrome_options)
            else:
                # Use webdriver-manager for other platforms
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            driver.set_page_load_timeout(60)
            driver.set_script_timeout(60)
            
            logging.info("Chrome WebDriver set up successfully")
            return driver
        except Exception as e:
            logging.error(f"Error setting up Chrome WebDriver: {e}")
            return None
    
    def take_screenshot(self, name):
        """Take a screenshot for debugging purposes"""
        if self.driver:
            screenshot_path = os.path.join(self.output_dir, f"{name}_{self.timestamp}.png")
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
    
    def save_page_source(self, name):
        """Save the page source for debugging purposes"""
        if self.driver:
            source_path = os.path.join(self.output_dir, f"{name}_{self.timestamp}.html")
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logging.info(f"Page source saved to {source_path}")
    
    def navigate_to_website(self):
        """Navigate directly to the results page with all filters applied"""
        try:
            logging.info(f"Navigating directly to results page with URL: {self.base_url}")
            self.driver.get(self.base_url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for the results to load
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".supplier-offer, .offer, .rate-card, table"))
            )
            
            logging.info("Successfully navigated to the results page")
            self.take_screenshot("results_page")
            self.save_page_source("results_page")
            return True
        except Exception as e:
            logging.error(f"Error navigating to results page: {e}")
            self.take_screenshot("navigation_error")
            return False
    
    def click_export_button(self):
        """Click the 'Export to CSV' button"""
        try:
            logging.info("Looking for Export to CSV button")
            
            # Wait for the page to be fully loaded
            time.sleep(3)
            
            # Try multiple approaches to find the Export to CSV button
            export_button = None
            
            # Approach 1: Look for text "Export to CSV" near "Print Results"
            try:
                # First find the Print Results button
                print_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Print Results')] | //a[contains(text(), 'Print Results')]"))
                )
                
                # Then find the Export to CSV button which should be nearby
                export_button = self.driver.find_element(By.XPATH, 
                    "//button[contains(text(), 'Export to CSV')] | //a[contains(text(), 'Export to CSV')]")
                
                logging.info("Found Export to CSV button using text search near Print Results")
            except Exception as e:
                logging.warning(f"Could not find Export button near Print Results: {e}")
            
            # Approach 2: Direct XPath search
            if not export_button:
                try:
                    export_button = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, 
                            "//button[contains(text(), 'Export to CSV')] | //a[contains(text(), 'Export to CSV')]"))
                    )
                    logging.info("Found Export to CSV button using direct XPath search")
                except Exception as e:
                    logging.warning(f"Could not find Export button with direct XPath: {e}")
            
            # Approach 3: Look for any element containing "Export" and "CSV"
            if not export_button:
                try:
                    export_button = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, 
                            "//*[contains(text(), 'Export') and contains(text(), 'CSV')]"))
                    )
                    logging.info("Found Export to CSV button using partial text search")
                except Exception as e:
                    logging.warning(f"Could not find Export button with partial text: {e}")
            
            if export_button:
                # Scroll to the export button to make sure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
                
                # Take a screenshot before clicking
                self.take_screenshot("before_export_click")
                
                # Try to click directly
                try:
                    export_button.click()
                    logging.info("Clicked Export to CSV button")
                except Exception as click_error:
                    logging.warning(f"Direct click failed: {click_error}")
                    # If direct click fails, try JavaScript click
                    try:
                        self.driver.execute_script("arguments[0].click();", export_button)
                        logging.info("Clicked Export to CSV button using JavaScript")
                    except Exception as js_error:
                        logging.error(f"JavaScript click also failed: {js_error}")
                        return False
                
                # Wait for the download to complete
                time.sleep(10)
                
                logging.info("Export to CSV button clicked successfully")
                return True
            else:
                logging.error("Export to CSV button not found")
                self.take_screenshot("export_button_not_found")
                self.save_page_source("export_button_not_found")
                return False
        except Exception as e:
            logging.error(f"Error clicking Export to CSV button: {e}")
            self.take_screenshot("export_button_error")
            return False
    
    def find_latest_csv_file(self):
        """Find the most recently downloaded CSV file in the output directory"""
        try:
            # Look for CSV files in the output directory
            csv_files = glob.glob(os.path.join(self.output_dir, "*.csv"))
            
            if not csv_files:
                logging.error("No CSV files found in the output directory")
                return None
            
            # Get the most recently modified file
            latest_file = max(csv_files, key=os.path.getmtime)
            
            # Check if the file was created/modified in the last minute
            file_mtime = os.path.getmtime(latest_file)
            current_time = time.time()
            
            if current_time - file_mtime > 60:
                logging.warning(f"Latest CSV file ({latest_file}) is older than 1 minute")
            
            logging.info(f"Found latest CSV file: {latest_file}")
            return latest_file
        except Exception as e:
            logging.error(f"Error finding latest CSV file: {e}")
            return None
    
    def process_csv_file(self, csv_file, zipcode):
        """Process the downloaded CSV file"""
        try:
            if not csv_file or not os.path.exists(csv_file):
                logging.error("CSV file not found")
                return False
            
            logging.info(f"Processing CSV file: {csv_file}")
            
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Store the original row count
            original_row_count = len(df)
            logging.info(f"Original CSV file has {original_row_count} rows")
            
            # Copy the original file with timestamp
            export_filename = f"papowerswitch_export_{self.timestamp}.csv"
            export_path = os.path.join(self.output_dir, export_filename)
            shutil.copy2(csv_file, export_path)
            logging.info(f"Original CSV file copied to: {export_path}")
            
            # Remove specified columns if they exist
            columns_to_remove = ['PA Wind', 'Renewable Energy', 'Contact Phone Number']
            removed_columns = []
            for col in columns_to_remove:
                if col in df.columns:
                    df = df.drop(columns=[col])
                    removed_columns.append(col)
            
            if removed_columns:
                logging.info(f"Removed columns: {', '.join(removed_columns)}")
            
            # Apply filters
            if 'Service Type' in df.columns:
                df = df[df['Service Type'] == 'Residential']
                logging.info("Filtered for Residential service type")
            
            if 'Type' in df.columns:
                df = df[df['Type'] == 'Fixed']
                logging.info("Filtered for Fixed rate type")
            
            if 'Monthly Fee' in df.columns:
                df = df[df['Monthly Fee'] == 'No']
                logging.info("Filtered for No monthly fee")
            
            # Convert Price to numeric for sorting, handling non-numeric values
            if 'Price' in df.columns:
                df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
                df = df.sort_values(by='Price').reset_index(drop=True)
                logging.info("Sorted data by Price (ascending)")
            
            # Rearrange columns to put Supplier, Price, Term Length first
            all_columns = df.columns.tolist()
            priority_columns = ['Supplier', 'Price', 'Term Length']
            
            # Filter out priority columns that actually exist in the DataFrame
            existing_priority_columns = [col for col in priority_columns if col in all_columns]
            
            # Get remaining columns (excluding priority columns)
            remaining_columns = [col for col in all_columns if col not in existing_priority_columns]
            
            # Reorder columns
            df = df[existing_priority_columns + remaining_columns]
            logging.info(f"Rearranged columns with priority: {', '.join(existing_priority_columns)}")
            
            # Save the filtered data to a new CSV file
            filtered_filename = f"papowerswitch_filtered_{zipcode}_{self.timestamp}.csv"
            filtered_path = os.path.join(self.output_dir, filtered_filename)
            df.to_csv(filtered_path, index=False)
            
            logging.info(f"Filtered CSV file saved to: {filtered_path}")
            logging.info(f"Original row count: {original_row_count}, Filtered row count: {len(df)}")
            
            return True
        except Exception as e:
            logging.error(f"Error processing CSV file: {e}")
            return False
    
    def run(self, zipcode):
        """Run the scraper with the specified zipcode"""
        success = False
        
        # Update the base URL with the provided zipcode
        self.zipcode = zipcode
        self.base_url = f"https://www.papowerswitch.com/shop-for-rates-results?zip={zipcode}&distributor=1182&distributorrate=R%20-%20Regular%20Residential%20Service&servicetype=residential&usage=700&min-price=&max-price=&ratePreferences%5B%5D=fixed&offerPreferences%5B%5D=no_cancellation&offerPreferences%5B%5D=no_enrollment&offerPreferences%5B%5D=no_monthly&offerPreferences%5B%5D=introductory_prices&sortby=est_a"
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logging.info(f"Attempt {attempt} of {self.max_retries}")
                
                # Set up the driver
                self.driver = self.setup_driver()
                if not self.driver:
                    logging.error("Failed to set up WebDriver")
                    continue
                
                # Navigate directly to the results page
                if not self.navigate_to_website():
                    logging.error("Failed to navigate to results page")
                    continue
                
                # Click the export button
                if not self.click_export_button():
                    logging.error("Failed to click export button")
                    continue
                
                # Find the latest CSV file
                csv_file = self.find_latest_csv_file()
                if not csv_file:
                    logging.error("Failed to find CSV file")
                    continue
                
                # Process the CSV file
                if not self.process_csv_file(csv_file, zipcode):
                    logging.error("Failed to process CSV file")
                    continue
                
                # If we got here, everything was successful
                success = True
                logging.info("Scraper completed successfully")
                break
            
            except Exception as e:
                logging.error(f"Error during scraping: {e}")
                self.take_screenshot(f"error_attempt_{attempt}")
                self.save_page_source(f"error_attempt_{attempt}")
            
            finally:
                # Close the driver
                if self.driver:
                    self.driver.quit()
                    self.driver = None
            
            # Wait before retrying
            if attempt < self.max_retries and not success:
                logging.info(f"Waiting {self.retry_delay} seconds before retrying...")
                time.sleep(self.retry_delay)
        
        return success

def main():
    """Main function to run the scraper"""
    parser = argparse.ArgumentParser(description='Scrape PA Power Switch website for electricity offers using Export to CSV')
    parser.add_argument('--zipcode', type=str, required=True, help='Zip code to search for')
    parser.add_argument('--output-dir', type=str, default='output', help='Directory to save output files')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (no browser UI)')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum number of retry attempts')
    parser.add_argument('--retry-delay', type=int, default=5, help='Delay between retry attempts in seconds')
    args = parser.parse_args()
    
    logging.info(f"Starting PA Power Switch Export Scraper for zipcode: {args.zipcode}")
    
    # Initialize and run the scraper
    scraper = PAPowerSwitchExportScraper(
        output_dir=args.output_dir,
        headless=args.headless,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay
    )
    
    success = scraper.run(args.zipcode)
    
    if success:
        print("\nElectricity Rate Data Summary:")
        print("==============================")
        print(f"Zipcode: {args.zipcode}")
        print(f"Data successfully exported and processed")
        print(f"\nResults saved to: {os.path.join(args.output_dir, f'papowerswitch_filtered_{args.zipcode}_{scraper.timestamp}.csv')}")
        print(f"Original export saved to: {os.path.join(args.output_dir, f'papowerswitch_export_{scraper.timestamp}.csv')}")
        sys.exit(0)
    else:
        print("\nError: Failed to scrape electricity rate data")
        sys.exit(1)

if __name__ == "__main__":
    main() 