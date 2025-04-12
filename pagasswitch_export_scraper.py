#!/usr/bin/env python3
"""
Script to use the "Export Offer to CSV" feature on the pagasswitch.com website.
This script navigates to the website, enters a zip code, applies filters,
clicks the "Export Offer to CSV" button, and processes the downloaded file.
"""

import os
import sys
import time
import csv
import logging
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Create output directory if it doesn't exist
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(output_dir, "pagasswitch_export_scraper.log")),
        logging.StreamHandler(sys.stdout)
    ]
)

class PAGasSwitchExportScraper:
    def __init__(self, output_dir='output', headless=False, download_dir=None, max_retries=3, retry_delay=5):
        # URL for the shop page
        self.shop_url = "https://www.pagasswitch.com/shop-for-natural-gas"
        
        # Create output directory if it doesn't exist
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up download directory
        if download_dir is None:
            self.download_dir = os.path.join(os.getcwd(), self.output_dir)
        else:
            self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Timestamp for output files
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Retry settings
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Set up Selenium
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Window size and display settings
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Disable various features that might interfere
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # Set download preferences
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            # Disable PDF viewer
            "plugins.always_open_pdf_externally": True,
            # Disable save password prompt
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            # Disable notifications
            "profile.default_content_setting_values.notifications": 2,
            # Enable JavaScript
            "profile.default_content_settings.javascript": 1,
            # Enable images
            "profile.default_content_settings.images": 1,
            # Enable cookies
            "profile.default_content_settings.cookies": 1
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Exclude the "enable-automation" flag
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # Set up user agent to mimic a real browser
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
        
        # Initialize the Chrome driver
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Set page load timeout and script timeout
        self.driver.set_page_load_timeout(60)
        self.driver.set_script_timeout(60)
        
        # Set up WebDriverWait with a longer timeout
        self.wait = WebDriverWait(self.driver, 30)
        
        # Log initialization
        logging.info("Chrome browser initialized with the following options:")
        logging.info(f"Headless mode: {headless}")
        logging.info(f"Download directory: {self.download_dir}")
        logging.info(f"Output directory: {self.output_dir}")
        logging.info(f"Window size: 1920x1080")
        logging.info(f"Wait timeout: 30 seconds")
    
    def __del__(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except Exception as e:
            logging.error(f"Error closing browser: {e}")
    
    def navigate_to_shop_page(self):
        """Navigate to the shop page"""
        logging.info("Navigating to shop page")
        
        try:
            # Navigate to the shop page
            self.driver.get(self.shop_url)
            
            # Wait for the page to fully load
            time.sleep(5)  # Give the page more time to fully initialize
            
            # Wait for the page to load (look for the zip code input field)
            try:
                # Wait for the element to be present
                self.wait.until(EC.presence_of_element_located((By.ID, "edit-zipcode")))
                logging.info("Shop page loaded successfully (found zipcode field by ID)")
            except TimeoutException:
                # Try alternative selectors if the zipcode field isn't found
                try:
                    self.wait.until(EC.presence_of_element_located((By.NAME, "zipcode")))
                    logging.info("Shop page loaded successfully (found zipcode field by name)")
                except TimeoutException:
                    # Check if any form is present
                    self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
                    logging.info("Shop page loaded successfully (found form)")
            
            # Check if the page title contains expected text
            if "Shop for Natural Gas" in self.driver.title:
                logging.info(f"Page title confirms we're on the shop page: {self.driver.title}")
            else:
                logging.warning(f"Unexpected page title: {self.driver.title}")
            
            # Save screenshot for debugging
            self.save_screenshot("shop_page")
            
            # Save page source for debugging
            self.save_page_source("shop_page")
            
            # Check if we're on the correct page by looking for key elements
            try:
                # Look for elements that should be on the shop page
                page_heading = self.driver.find_element(By.XPATH, "//h1[contains(text(), 'Shop') and contains(text(), 'Natural Gas')]")
                logging.info(f"Found page heading: {page_heading.text}")
            except NoSuchElementException:
                logging.warning("Could not find expected page heading")
            
            return True
        except Exception as e:
            logging.error(f"Error navigating to shop page: {e}")
            self.save_screenshot("shop_page_error")
            self.save_page_source("shop_page_error")
            return False
    
    def enter_zipcode(self, zipcode):
        """Enter the zipcode and submit the form"""
        logging.info(f"Entering zipcode: {zipcode}")
        
        try:
            # Wait for the page to fully load
            time.sleep(3)  # Give the page a moment to fully initialize
            
            # Find the specific zipcode input field identified by the user
            try:
                # Wait for the element to be present
                self.wait.until(EC.presence_of_element_located((By.ID, "edit-zipcode")))
                logging.info("Zipcode input element is present in the DOM")
                
                # Wait for the element to be visible
                self.wait.until(EC.visibility_of_element_located((By.ID, "edit-zipcode")))
                logging.info("Zipcode input element is visible")
                
                # Wait for the element to be interactable
                self.wait.until(EC.element_to_be_clickable((By.ID, "edit-zipcode")))
                logging.info("Zipcode input element is clickable")
                
                # Get the element
                zipcode_input = self.driver.find_element(By.ID, "edit-zipcode")
                logging.info("Found zipcode input with ID 'edit-zipcode'")
            except (TimeoutException, NoSuchElementException) as e:
                logging.warning(f"Could not find zipcode input by ID: {e}")
                try:
                    # Try by XPath using the exact structure provided
                    self.wait.until(EC.presence_of_element_located((
                        By.XPATH, "//div[@id='edit-zipcode-wrapper']/input[@id='edit-zipcode' and @name='zipcode']"
                    )))
                    zipcode_input = self.driver.find_element(
                        By.XPATH, "//div[@id='edit-zipcode-wrapper']/input[@id='edit-zipcode' and @name='zipcode']"
                    )
                    logging.info("Found zipcode input by XPath with specific structure")
                except (TimeoutException, NoSuchElementException) as e:
                    logging.warning(f"Could not find zipcode input by XPath: {e}")
                    # Try by name as a fallback
                    try:
                        self.wait.until(EC.presence_of_element_located((By.NAME, "zipcode")))
                        zipcode_input = self.driver.find_element(By.NAME, "zipcode")
                        logging.info("Found zipcode input by name 'zipcode'")
                    except (TimeoutException, NoSuchElementException) as e:
                        logging.error(f"Could not find zipcode input field: {e}")
                        self.save_screenshot(f"zipcode_not_found_{zipcode}")
                        self.save_page_source(f"zipcode_not_found_{zipcode}")
                        return False
            
            # Try to scroll the element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", zipcode_input)
            time.sleep(1)  # Give time for scrolling
            
            # Try to focus the element
            self.driver.execute_script("arguments[0].focus();", zipcode_input)
            time.sleep(1)  # Give time for focus
            
            # Clear the field using JavaScript
            self.driver.execute_script("arguments[0].value = '';", zipcode_input)
            
            # Enter the zipcode using JavaScript
            self.driver.execute_script(f"arguments[0].value = '{zipcode}';", zipcode_input)
            logging.info(f"Entered zipcode {zipcode} using JavaScript")
            
            # Save screenshot after entering zipcode
            self.save_screenshot(f"zipcode_entered_{zipcode}")
            
            # Find and click the submit button
            try:
                # Look for the submit button by ID
                submit_button = self.driver.find_element(By.ID, "edit-submit-residential-rate-search2")
                logging.info("Found submit button by ID")
            except NoSuchElementException:
                try:
                    # Try to find a button within the same form
                    form = zipcode_input.find_element(By.XPATH, "./ancestor::form")
                    submit_button = form.find_element(By.XPATH, ".//input[@type='submit'] | .//button[@type='submit']")
                    logging.info("Found submit button within the same form")
                except NoSuchElementException:
                    try:
                        # Try to find any submit button on the page
                        submit_button = self.driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']")
                        logging.info("Found submit button on the page")
                    except NoSuchElementException:
                        logging.error("Could not find submit button")
                        self.save_screenshot(f"submit_button_not_found_{zipcode}")
                        self.save_page_source(f"submit_button_not_found_{zipcode}")
                        return False
            
            # Try to scroll the submit button into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            time.sleep(1)  # Give time for scrolling
            
            # Click the submit button using JavaScript
            try:
                self.driver.execute_script("arguments[0].click();", submit_button)
                logging.info("Clicked submit button using JavaScript")
            except Exception as e:
                logging.error(f"Failed to click submit button with JavaScript: {e}")
                return False
            
            # Wait for the results page to load
            try:
                # Wait for the export button to appear or any indication of results
                self.wait.until(EC.presence_of_element_located((
                    By.XPATH, "//button[contains(text(), 'Export') or contains(@class, 'export')]"
                )))
                logging.info("Results page loaded successfully (found export button)")
            except TimeoutException:
                try:
                    # Try looking for filter options which would indicate results page
                    self.wait.until(EC.presence_of_element_located((
                        By.XPATH, "//input[@type='radio' or @type='checkbox']"
                    )))
                    logging.info("Results page loaded successfully (found filter options)")
                except TimeoutException:
                    logging.error("Timeout waiting for results page to load")
                    self.save_screenshot(f"results_page_timeout_{zipcode}")
                    self.save_page_source(f"results_page_timeout_{zipcode}")
                    return False
            
            # Save screenshot of results page
            self.save_screenshot(f"results_page_{zipcode}")
            self.save_page_source(f"results_page_{zipcode}")
            
            return True
        except Exception as e:
            logging.error(f"Error entering zipcode: {e}")
            self.save_screenshot(f"zipcode_error_{zipcode}")
            self.save_page_source(f"zipcode_error_{zipcode}")
            return False
    
    def apply_filters(self):
        """Apply the specified filters to the results page"""
        logging.info("Applying filters to results page")
        
        try:
            # Wait for filters to be available
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='radio' or @type='checkbox']")))
            
            # 1. Select Fixed Price checkbox
            self._select_fixed_price()
            
            # 2. Select "Any" for Term Length (this might be default)
            self._select_term_length_any()
            
            # 3. Select Terms & Conditions checkboxes
            self._select_terms_conditions()
            
            # 4. Select "R - Regular Residential Service"
            self._select_regular_residential_service()
            
            # Save screenshot after applying filters
            self.save_screenshot("after_filters_applied")
            self.save_page_source("after_filters_applied")
            
            # Wait for results to update
            time.sleep(5)
            
            return True
        except Exception as e:
            logging.error(f"Error applying filters: {e}")
            self.save_screenshot("filter_error")
            self.save_page_source("filter_error")
            return False
    
    def _select_fixed_price(self):
        """Select the Fixed Price checkbox"""
        logging.info("Selecting Fixed Price checkbox")
        
        try:
            # Try different approaches to find the Fixed Price checkbox
            try:
                # Try by ID
                fixed_price_checkbox = self.driver.find_element(By.ID, "edit-field-type-value-fixed")
                logging.info("Found Fixed Price checkbox by ID")
            except NoSuchElementException:
                try:
                    # Try by label text
                    fixed_price_checkbox = self.driver.find_element(
                        By.XPATH, "//label[contains(text(), 'Fixed price')]/preceding-sibling::input[@type='checkbox'] | "
                                  "//label[contains(text(), 'Fixed price')]/following-sibling::input[@type='checkbox']"
                    )
                    logging.info("Found Fixed Price checkbox by label text")
                except NoSuchElementException:
                    try:
                        # Try by looking at all checkboxes
                        checkboxes = self.driver.find_elements(By.XPATH, "//input[@type='checkbox']")
                        fixed_price_checkbox = None
                        
                        for checkbox in checkboxes:
                            # Check the label or surrounding text
                            try:
                                label = checkbox.find_element(By.XPATH, "./following-sibling::label | ./preceding-sibling::label | ./parent::label")
                                if "fixed" in label.text.lower() and "price" in label.text.lower():
                                    fixed_price_checkbox = checkbox
                                    logging.info(f"Found Fixed Price checkbox by label content: {label.text}")
                                    break
                            except NoSuchElementException:
                                # If no label, check parent elements for text
                                parent = checkbox.find_element(By.XPATH, "./..")
                                if "fixed" in parent.text.lower() and "price" in parent.text.lower():
                                    fixed_price_checkbox = checkbox
                                    logging.info(f"Found Fixed Price checkbox by parent content: {parent.text}")
                                    break
                        
                        if not fixed_price_checkbox:
                            logging.warning("Could not find Fixed Price checkbox")
                            return
                    except Exception as e:
                        logging.warning(f"Error finding Fixed Price checkbox: {e}")
                        return
            
            # Check if already selected
            if not fixed_price_checkbox.is_selected():
                # Try to click with JavaScript if regular click doesn't work
                try:
                    fixed_price_checkbox.click()
                    logging.info("Selected Fixed Price checkbox with regular click")
                except Exception as e:
                    logging.warning(f"Regular click failed: {e}, trying JavaScript click")
                    self.driver.execute_script("arguments[0].click();", fixed_price_checkbox)
                    logging.info("Selected Fixed Price checkbox with JavaScript click")
                
                time.sleep(1)  # Small delay to let the page update
            else:
                logging.info("Fixed Price checkbox already selected")
        except Exception as e:
            logging.error(f"Error selecting Fixed Price checkbox: {e}")
    
    def _select_term_length_any(self):
        """Select 'Any' for Term Length"""
        logging.info("Selecting 'Any' for Term Length")
        
        try:
            # Try to find a dropdown for term length
            try:
                # Look for select elements
                selects = self.driver.find_elements(By.TAG_NAME, "select")
                term_length_select = None
                
                for select in selects:
                    # Check if this select is for term length
                    try:
                        label = select.find_element(By.XPATH, "./preceding-sibling::label | ./following-sibling::label | ./parent::*/preceding-sibling::label")
                        if "term" in label.text.lower() and "length" in label.text.lower():
                            term_length_select = select
                            logging.info(f"Found Term Length select by label: {label.text}")
                            break
                    except NoSuchElementException:
                        # If no label, check the options
                        options = select.find_elements(By.TAG_NAME, "option")
                        option_texts = [option.text.lower() for option in options]
                        if any("month" in text for text in option_texts):
                            term_length_select = select
                            logging.info("Found Term Length select by options containing 'month'")
                            break
                
                if term_length_select:
                    # Create Select object
                    select_obj = Select(term_length_select)
                    
                    # Try to select "Any" option
                    try:
                        select_obj.select_by_visible_text("Any")
                        logging.info("Selected 'Any' for Term Length")
                    except Exception:
                        try:
                            # Try selecting the first option (often "Any" or "All")
                            select_obj.select_by_index(0)
                            logging.info(f"Selected first option for Term Length: {select_obj.first_selected_option.text}")
                        except Exception as e:
                            logging.warning(f"Could not select option for Term Length: {e}")
                else:
                    # If no dropdown found, look for radio buttons for term length
                    term_length_radios = self.driver.find_elements(
                        By.XPATH, "//label[contains(text(), 'Any')]/input[@type='radio'] | "
                                  "//label[contains(text(), 'Any')]/preceding-sibling::input[@type='radio'] | "
                                  "//label[contains(text(), 'Any')]/following-sibling::input[@type='radio']"
                    )
                    
                    if term_length_radios:
                        # Click the "Any" radio button
                        try:
                            term_length_radios[0].click()
                            logging.info("Selected 'Any' radio button for Term Length")
                        except Exception as e:
                            logging.warning(f"Could not click 'Any' radio button: {e}")
                            try:
                                self.driver.execute_script("arguments[0].click();", term_length_radios[0])
                                logging.info("Selected 'Any' radio button for Term Length with JavaScript")
                            except Exception as e:
                                logging.warning(f"JavaScript click failed: {e}")
                    else:
                        logging.info("No Term Length selection found, assuming default is 'Any'")
            except Exception as e:
                logging.warning(f"Error finding Term Length selection: {e}")
        except Exception as e:
            logging.error(f"Error selecting Term Length: {e}")
    
    def _select_terms_conditions(self):
        """Select the Terms & Conditions checkboxes"""
        logging.info("Selecting Terms & Conditions checkboxes")
        
        # List of conditions to select
        conditions = [
            "No Cancellation Fee",
            "No Deposit Required",
            "No Monthly Fee"
        ]
        
        try:
            for condition in conditions:
                try:
                    # Try to find checkbox by label text
                    checkbox = self.driver.find_element(
                        By.XPATH, f"//label[contains(text(), '{condition}')]/input[@type='checkbox'] | "
                                  f"//label[contains(text(), '{condition}')]/preceding-sibling::input[@type='checkbox'] | "
                                  f"//label[contains(text(), '{condition}')]/following-sibling::input[@type='checkbox']"
                    )
                    
                    # Check if already selected
                    if not checkbox.is_selected():
                        # Try to click with JavaScript if regular click doesn't work
                        try:
                            checkbox.click()
                            logging.info(f"Selected checkbox: {condition}")
                        except Exception as e:
                            logging.warning(f"Regular click failed for {condition}: {e}, trying JavaScript click")
                            self.driver.execute_script("arguments[0].click();", checkbox)
                            logging.info(f"Selected checkbox: {condition} with JavaScript")
                        
                        time.sleep(1)  # Small delay to let the page update
                    else:
                        logging.info(f"Checkbox {condition} already selected")
                except NoSuchElementException:
                    logging.warning(f"Could not find checkbox for: {condition}")
                    
                    # Try a more general approach
                    try:
                        # Get all checkboxes
                        checkboxes = self.driver.find_elements(By.XPATH, "//input[@type='checkbox']")
                        
                        for checkbox in checkboxes:
                            # Check the label or surrounding text
                            try:
                                label = checkbox.find_element(By.XPATH, "./following-sibling::label | ./preceding-sibling::label | ./parent::label")
                                label_text = label.text.lower()
                                
                                condition_lower = condition.lower()
                                if all(word.lower() in label_text for word in condition_lower.split()):
                                    if not checkbox.is_selected():
                                        try:
                                            checkbox.click()
                                            logging.info(f"Selected checkbox with label: {label.text}")
                                        except Exception:
                                            self.driver.execute_script("arguments[0].click();", checkbox)
                                            logging.info(f"Selected checkbox with label: {label.text} using JavaScript")
                                        
                                        time.sleep(1)  # Small delay to let the page update
                                    else:
                                        logging.info(f"Checkbox with label: {label.text} already selected")
                                    break
                            except NoSuchElementException:
                                continue
                    except Exception as e:
                        logging.warning(f"Error in general checkbox search for {condition}: {e}")
        except Exception as e:
            logging.error(f"Error selecting Terms & Conditions checkboxes: {e}")
    
    def _select_regular_residential_service(self):
        """Select 'R - Regular Residential Service'"""
        logging.info("Selecting 'R - Regular Residential Service'")
        
        try:
            # Try to find a dropdown or radio buttons for rate schedule
            try:
                # Look for a select element for rate schedule
                rate_schedule_select = None
                
                # Try to find by label text
                selects = self.driver.find_elements(
                    By.XPATH, "//label[contains(text(), 'Rate Schedule') or contains(text(), 'Service Type')]/following-sibling::select | "
                              "//label[contains(text(), 'Rate Schedule') or contains(text(), 'Service Type')]/preceding-sibling::select"
                )
                
                if selects:
                    rate_schedule_select = selects[0]
                    logging.info("Found Rate Schedule select by label")
                else:
                    # Try to find any select with options containing "Residential Service"
                    selects = self.driver.find_elements(By.TAG_NAME, "select")
                    for select in selects:
                        options = select.find_elements(By.TAG_NAME, "option")
                        for option in options:
                            if "Regular Residential Service" in option.text:
                                rate_schedule_select = select
                                logging.info("Found Rate Schedule select by option text")
                                break
                        if rate_schedule_select:
                            break
                
                if rate_schedule_select:
                    # Create Select object
                    select_obj = Select(rate_schedule_select)
                    
                    # Try to select "R - Regular Residential Service"
                    try:
                        select_obj.select_by_visible_text("R - Regular Residential Service")
                        logging.info("Selected 'R - Regular Residential Service' by visible text")
                    except Exception:
                        try:
                            # Try selecting by partial text
                            options = select_obj.options
                            for i, option in enumerate(options):
                                if "Regular Residential Service" in option.text:
                                    select_obj.select_by_index(i)
                                    logging.info(f"Selected option: {option.text}")
                                    break
                        except Exception as e:
                            logging.warning(f"Could not select 'R - Regular Residential Service': {e}")
                else:
                    # Try to find radio buttons or checkboxes for rate schedule
                    rate_schedule_inputs = self.driver.find_elements(
                        By.XPATH, "//label[contains(text(), 'Regular Residential Service')]/preceding-sibling::input | "
                                  "//label[contains(text(), 'Regular Residential Service')]/following-sibling::input"
                    )
                    
                    if rate_schedule_inputs:
                        # Click the "R - Regular Residential Service" input
                        try:
                            rate_schedule_inputs[0].click()
                            logging.info("Selected 'R - Regular Residential Service' input")
                        except Exception as e:
                            logging.warning(f"Could not click 'R - Regular Residential Service' input: {e}")
                            try:
                                self.driver.execute_script("arguments[0].click();", rate_schedule_inputs[0])
                                logging.info("Selected 'R - Regular Residential Service' input with JavaScript")
                            except Exception as e:
                                logging.warning(f"JavaScript click failed: {e}")
                    else:
                        logging.warning("Could not find 'R - Regular Residential Service' selection")
            except Exception as e:
                logging.warning(f"Error finding Rate Schedule selection: {e}")
        except Exception as e:
            logging.error(f"Error selecting 'R - Regular Residential Service': {e}")
    
    def click_export_button(self):
        """Click the Export Offer to CSV button and wait for the download"""
        logging.info("Clicking Export Offer to CSV button")
        
        try:
            # Find the Export button
            try:
                # Try to find by text content
                export_button = self.driver.find_element(
                    By.XPATH, "//a[contains(text(), 'Export') and contains(text(), 'CSV')] | "
                              "//button[contains(text(), 'Export') and contains(text(), 'CSV')]"
                )
                logging.info("Found Export button by text")
            except NoSuchElementException:
                try:
                    # Try to find by class or ID
                    export_button = self.driver.find_element(
                        By.XPATH, "//a[contains(@class, 'export') or contains(@id, 'export')] | "
                                  "//button[contains(@class, 'export') or contains(@id, 'export')]"
                    )
                    logging.info("Found Export button by class/ID")
                except NoSuchElementException:
                    # Try to find any link with "csv" in the URL
                    export_button = self.driver.find_element(
                        By.XPATH, "//a[contains(@href, 'csv') or contains(@href, 'CSV')]"
                    )
                    logging.info("Found Export button by href")
            
            # Try to scroll the button into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
            time.sleep(1)  # Give time for scrolling
            
            # Click the button
            try:
                export_button.click()
                logging.info("Clicked Export button")
            except Exception as e:
                logging.warning(f"Regular click failed: {e}, trying JavaScript click")
                self.driver.execute_script("arguments[0].click();", export_button)
                logging.info("Clicked Export button with JavaScript")
            
            # Wait for the download to complete
            time.sleep(5)  # Give time for the download to start and complete
            
            # Check if a CSV file was downloaded
            csv_files = [f for f in os.listdir(self.download_dir) if f.endswith('.csv')]
            
            if not csv_files:
                logging.error("No CSV files found after clicking Export button")
                self.save_screenshot("export_error_no_csv")
                self.save_page_source("export_error_no_csv")
                return False
            
            # Sort by modification time (newest first)
            csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.download_dir, x)), reverse=True)
            
            # Get the most recent CSV file
            latest_csv = csv_files[0]
            csv_path = os.path.join(self.download_dir, latest_csv)
            
            logging.info(f"CSV file downloaded: {csv_path}")
            
            return True
        except Exception as e:
            logging.error(f"Error clicking Export button: {e}")
            self.save_screenshot("export_error")
            self.save_page_source("export_error")
            return False
    
    def process_csv_file(self, zipcode):
        """Process the downloaded CSV file"""
        logging.info(f"Processing CSV file for zipcode: {zipcode}")
        
        try:
            # Look for the downloaded CSV file
            csv_files = [f for f in os.listdir(self.download_dir) if f.endswith('.csv')]
            
            if not csv_files:
                logging.error("No CSV files found in download directory")
                return False
            
            # Sort by modification time (newest first)
            csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.download_dir, x)), reverse=True)
            
            # Get the most recent CSV file
            latest_csv = csv_files[0]
            csv_path = os.path.join(self.download_dir, latest_csv)
            
            logging.info(f"Found CSV file: {csv_path}")
            
            # Copy the file with a timestamp
            output_filename = f"pagasswitch_export_{self.timestamp}.csv"
            output_path = os.path.join(self.output_dir, output_filename)
            
            import shutil
            shutil.copy2(csv_path, output_path)
            logging.info(f"CSV file copied to: {output_path}")
            
            # Read the CSV file
            try:
                df = pd.read_csv(csv_path)
                logging.info(f"CSV file read successfully with {len(df)} rows")
                
                # Store the original row count
                original_count = len(df)
                
                # Apply filters based on specified criteria
                filtered_df = df.copy()
                
                # Filter 1: Service Type = 'Residential'
                if 'Service Type' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['Service Type'] == 'Residential']
                    logging.info(f"Filtered to {len(filtered_df)} rows with Service Type = 'Residential'")
                else:
                    logging.warning("No 'Service Type' column found, skipping this filter")
                
                # Filter 2: Type = 'Fixed'
                if 'Type' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['Type'] == 'Fixed']
                    logging.info(f"Filtered to {len(filtered_df)} rows with Type = 'Fixed'")
                else:
                    logging.warning("No 'Type' column found, skipping this filter")
                
                # Filter 3: Monthly Fee = 'No'
                if 'Monthly Fee' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['Monthly Fee'] == 'No']
                    logging.info(f"Filtered to {len(filtered_df)} rows with Monthly Fee = 'No'")
                else:
                    logging.warning("No 'Monthly Fee' column found, skipping this filter")
                
                # Filter 4: Cancellation Fee is blank or NaN
                if 'Cancellation Fee' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['Cancellation Fee'].isna() | 
                                             (filtered_df['Cancellation Fee'] == '') | 
                                             (filtered_df['Cancellation Fee'].astype(str) == 'nan')]
                    logging.info(f"Filtered to {len(filtered_df)} rows with blank Cancellation Fee")
                else:
                    logging.warning("No 'Cancellation Fee' column found, skipping this filter")
                
                # Filter 5: Discounts/Incentives Available = 'No'
                if 'Discounts/Incentives Available' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['Discounts/Incentives Available'] == 'No']
                    logging.info(f"Filtered to {len(filtered_df)} rows with Discounts/Incentives Available = 'No'")
                else:
                    logging.warning("No 'Discounts/Incentives Available' column found, skipping this filter")
                
                # Sort by Price (ascending)
                if 'Price' in filtered_df.columns:
                    # Convert Price to numeric, coercing errors to NaN
                    filtered_df['Price'] = pd.to_numeric(filtered_df['Price'], errors='coerce')
                    # Sort by Price
                    filtered_df = filtered_df.sort_values(by='Price')
                    logging.info("Sorted results by Price (ascending)")
                else:
                    logging.warning("No 'Price' column found, skipping sorting")
                
                # Remove unwanted columns
                columns_to_remove = []
                
                # Store 'More info' column if it exists (instead of removing it)
                more_info_col = None
                if 'More info' in filtered_df.columns:
                    more_info_col = filtered_df['More info'].copy()
                    columns_to_remove.append('More info')
                    logging.info("Temporarily storing 'More info' column to move it to the end")
                
                # Remove 'Cancellation Fee' column
                if 'Cancellation Fee' in filtered_df.columns:
                    columns_to_remove.append('Cancellation Fee')
                    logging.info("Removing 'Cancellation Fee' column")
                
                # Remove any 'Unnamed' columns
                unnamed_columns = [col for col in filtered_df.columns if 'Unnamed' in col]
                if unnamed_columns:
                    columns_to_remove.extend(unnamed_columns)
                    logging.info(f"Removing {len(unnamed_columns)} 'Unnamed' columns")
                
                # Drop the unwanted columns
                if columns_to_remove:
                    filtered_df = filtered_df.drop(columns=columns_to_remove)
                    logging.info(f"Removed {len(columns_to_remove)} columns")
                
                # Reorder columns: Supplier, Price, Term Length, then the rest
                if all(col in filtered_df.columns for col in ['Supplier', 'Price', 'Term Length']):
                    # Get all columns except the ones we want to reorder
                    other_columns = [col for col in filtered_df.columns if col not in ['Supplier', 'Price', 'Term Length']]
                    # Create the new column order
                    new_column_order = ['Supplier', 'Price', 'Term Length'] + other_columns
                    # Reorder the columns
                    filtered_df = filtered_df[new_column_order]
                    logging.info("Reordered columns: Supplier, Price, Term Length, then others")
                else:
                    logging.warning("Could not reorder columns as requested - one or more columns not found")
                
                # Add "New Customers only" column and add back "More info" column at the end
                if more_info_col is not None:
                    # Create "New Customers only" column
                    filtered_df['New Customers only'] = 'No'
                    
                    # Fill the column with 'Yes' if "More info" contains "for new customers"
                    more_info_col = more_info_col.fillna('')
                    mask = more_info_col.str.lower().str.contains('for new customers', na=False)
                    filtered_df.loc[mask, 'New Customers only'] = 'Yes'
                    
                    # Count how many rows were marked as 'Yes'
                    yes_count = mask.sum()
                    logging.info(f"Added 'New Customers only' column: {yes_count} offers marked as for new customers only")
                    
                    # Add "More info" column back at the end
                    filtered_df['More info'] = more_info_col
                    logging.info("Added 'More info' column as the last column")
                
                # Save the filtered data
                filtered_output = f"pagasswitch_filtered_{zipcode}_{self.timestamp}.csv"
                filtered_path = os.path.join(self.output_dir, filtered_output)
                filtered_df.to_csv(filtered_path, index=False)
                logging.info(f"Filtered data saved to: {filtered_path}")
                
                # Print a summary
                print("\nNatural Gas Rate Data Summary:")
                print("==============================")
                print(f"Zipcode: {zipcode}")
                print(f"Total records: {original_count}")
                print(f"Filtered records: {len(filtered_df)}")
                print("\nFilters applied:")
                print("- Service Type = 'Residential'")
                print("- Type = 'Fixed'")
                print("- Monthly Fee = 'No'")
                print("- Cancellation Fee is blank")
                print("- Discounts/Incentives Available = 'No'")
                print("\nSorted by:")
                print("- Price (ascending)")
                print("\nColumns removed:")
                for col in columns_to_remove:
                    if col != 'More info':  # Don't list More info as removed since we added it back
                        print(f"- {col}")
                print("\nColumns added/modified:")
                print("- Added 'New Customers only' column (Yes/No based on 'for new customers' text in More info)")
                print("- Moved 'More info' column to the end")
                print("\nColumns reordered:")
                print("- Supplier (first)")
                print("- Price (second)")
                print("- Term Length (third)")
                print(f"\nOriginal CSV: {output_path}")
                print(f"Filtered CSV: {filtered_path}")
                
                # Print the first few rows of the filtered data
                if not filtered_df.empty:
                    print("\nFirst few rows of filtered data:")
                    print(filtered_df.head().to_string())
                else:
                    print("\nNo records match the filter criteria.")
                
                return True
            except Exception as e:
                logging.error(f"Error reading CSV file: {e}")
                return False
        except Exception as e:
            logging.error(f"Error processing CSV file: {e}")
            return False
    
    def save_screenshot(self, name):
        """Save a screenshot for debugging"""
        filename = f"{name}_{self.timestamp}.png"
        filepath = os.path.join(self.output_dir, filename)
        self.driver.save_screenshot(filepath)
        logging.info(f"Saved screenshot to {filepath}")
    
    def save_page_source(self, name):
        """Save the page source for debugging"""
        filename = f"{name}_{self.timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        
        logging.info(f"Saved page source to {filepath}")

    def run(self, zipcode):
        """Run the scraper with the specified zipcode"""
        success = False
        retry_count = 0
        
        while retry_count < self.max_retries and not success:
            if retry_count > 0:
                logging.info(f"Retry attempt {retry_count} of {self.max_retries}")
                time.sleep(self.retry_delay)
            
            try:
                # Step 1: Navigate to the shop page
                if not self.navigate_to_shop_page():
                    logging.error("Failed to navigate to shop page")
                    retry_count += 1
                    continue
                
                # Step 2: Enter zipcode and navigate to results page
                if not self.enter_zipcode(zipcode):
                    logging.error("Failed to enter zipcode and navigate to results page")
                    retry_count += 1
                    continue
                
                # Step 3: Apply filters
                if not self.apply_filters():
                    logging.error("Failed to apply filters")
                    retry_count += 1
                    continue
                
                # Step 4: Click export button and download CSV
                if not self.click_export_button():
                    logging.error("Failed to click export button and download CSV")
                    retry_count += 1
                    continue
                
                # Step 5: Process the downloaded CSV file
                if not self.process_csv_file(zipcode):
                    logging.error("Failed to process CSV file")
                    retry_count += 1
                    continue
                
                # If we got here, all steps were successful
                success = True
                logging.info("Successfully exported and processed data")
            
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                retry_count += 1
            
            finally:
                # Clean up resources
                try:
                    self.driver.quit()
                    logging.info("Browser closed")
                except Exception as e:
                    logging.error(f"Error closing browser: {e}")
        
        if not success:
            logging.error(f"Failed to export and process data after {self.max_retries} attempts")
        
        return success

def main():
    """Main function to run the scraper"""
    parser = argparse.ArgumentParser(description='Scrape PA Gas Switch website for natural gas offers')
    parser.add_argument('--zipcode', type=str, required=True, help='Zip code to search for')
    parser.add_argument('--output-dir', type=str, default='output', help='Directory to save output files')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum number of retry attempts')
    parser.add_argument('--retry-delay', type=int, default=5, help='Delay between retry attempts in seconds')
    args = parser.parse_args()
    
    logging.info(f"Starting PA Gas Export Scraper for zipcode: {args.zipcode}")
    logging.info(f"Output directory: {args.output_dir}")
    logging.info(f"Headless mode: {args.headless}")
    logging.info(f"Max retries: {args.max_retries}")
    logging.info(f"Retry delay: {args.retry_delay} seconds")
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize retry counter
    retry_count = 0
    success = False
    
    while retry_count < args.max_retries and not success:
        if retry_count > 0:
            logging.info(f"Retry attempt {retry_count} of {args.max_retries}")
            time.sleep(args.retry_delay)
        
        # Create a new scraper instance for each attempt
        scraper = None
        try:
            scraper = PAGasSwitchExportScraper(output_dir=args.output_dir, headless=args.headless, max_retries=args.max_retries, retry_delay=args.retry_delay)
            
            # Run the scraper with the specified zipcode
            if not scraper.run(args.zipcode):
                logging.error("Failed to run the scraper")
                retry_count += 1
                continue
            
            # If we got here, all steps were successful
            success = True
            logging.info("Successfully exported and processed data")
        
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            retry_count += 1
        
        finally:
            # Clean up resources
            if scraper:
                try:
                    scraper.driver.quit()
                    logging.info("Browser closed")
                except Exception as e:
                    logging.error(f"Error closing browser: {e}")
    
    if not success:
        logging.error(f"Failed to export and process data after {args.max_retries} attempts")
        sys.exit(1)
    
    logging.info("Script completed successfully")
    sys.exit(0)

if __name__ == "__main__":
    main() 