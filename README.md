# PA Energy Rate Finder

A Streamlit-based web application that helps Pennsylvania residents find and compare the best energy rates for electricity and gas services. This tool automates the process of gathering rate information from PA Power Switch and PA Gas Switch websites, making it easy to find competitive energy rates in your area.

## Features

- 🔍 Search energy rates by ZIP code
- ⚡ Support for both electricity and gas rates
- 📊 Interactive data visualization and comparison
- 📥 Automatic CSV export and data processing
- 🎯 User-friendly interface with real-time updates
- 🔄 Automatic retry mechanism for reliable scraping
- 📝 Detailed logging for troubleshooting
- 🖥️ Configurable headless mode for background operation

## Key Capabilities

### Electricity Rate Search
- Scrapes rates from PA Power Switch website
- Filters for residential service
- Supports fixed-rate plans
- Excludes plans with cancellation fees
- Sorts by estimated annual cost
- Exports data in CSV format

### Gas Rate Search
- Scrapes rates from PA Gas Switch website
- Focuses on residential natural gas service
- Filters for fixed-rate plans
- Excludes plans with hidden fees
- Provides rate comparison data
- Exports results in CSV format

### Data Processing
- Automatic CSV file management
- Latest data tracking
- Rate comparison features
- Historical data preservation
- Clean data formatting

## Project Structure

```
PAEnergyRateScraper/
├── app.py                              # Streamlit web application
├── papowerswitch_export_scraper.py    # Electricity rate scraper
├── pagasswitch_export_scraper.py      # Gas rate scraper
├── output/                            # Generated output files
│   ├── *.csv                         # Rate data files
│   └── *.log                         # Scraper logs
├── requirements.txt                   # Python dependencies
└── README.md                         # Documentation
```

### File Descriptions

- `app.py`: Main Streamlit application that provides the web interface and orchestrates the scraping process
- `papowerswitch_export_scraper.py`: Handles electricity rate scraping from PA Power Switch
- `pagasswitch_export_scraper.py`: Manages gas rate scraping from PA Gas Switch
- `requirements.txt`: Lists all Python package dependencies
- `output/`: Directory containing generated CSV files and logs

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Google Chrome browser
- Stable internet connection

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd PAEnergyRateScraper
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to:
```
http://localhost:8501
```

3. Enter a Pennsylvania ZIP code and select the energy type (Electricity or Gas)

4. Click "Fetch Rates" to get the latest energy rates

## Advanced Features

### Scraper Configuration
- Configurable retry attempts
- Adjustable retry delay
- Headless mode toggle
- Custom output directory
- Detailed logging options

### Data Management
- Automatic file organization
- Latest data tracking
- Historical data preservation
- CSV export functionality
- Rate comparison tools

## Troubleshooting

- If you encounter scraping issues:
  - Ensure Chrome is up to date
  - Check your internet connection
  - Try disabling headless mode
  - Review the log files in the output directory
- For installation issues:
  - Verify Python version (3.8+)
  - Ensure all dependencies are installed
  - Check virtual environment activation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. When contributing:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 