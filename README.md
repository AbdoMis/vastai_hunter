
# Vast.ai Auto-Renter (hunter)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)

An automated Python script designed to hunt down and rent the most cost-effective GPU instances on [Vast.ai](https://vast.ai/ "null"). It continuously searches the marketplace based on your specific criteria and automatically provisions the machine once a match is found.

## Features

* **Automated Searching:** Continuously scans the market for GPUs matching your price and hardware requirements.
* **Storage Calculation:** Automatically calculates hourly disk costs to prevent hidden storage fees.
* **Auto-Provisioning:** Rents the machine and injects the standard Vast.ai Jupyter UI environment automatically.
* **Health Monitoring:** Monitors the boot process and automatically destroys the instance if the host machine errors out, saving you money.
* **Ignore List:** Skip known bad or underperforming host IDs.

## Prerequisites

* Python 3.7+
* A [Vast.ai](https://vast.ai/ "null") account with billing configured.

## Installation

1. **Clone the repository:**
   ```
   git clone https://github.com/AbdoMis/vastai_hunter.git
   cd vastai_hunter
   ```
2. **Install the required Python packages:**
   ```
   pip install -r requirements.txt
   ```
3. **Set up your Vast.ai API Key:**
   To allow the script to search and rent on your behalf, you need to link it to your Vast.ai account.
   * Log in to the [Vast.ai Console](https://console.vast.ai/ "null").
   * Navigate to the **Account** tab on the left sidebar.
   * Scroll down to the **CLI / API Key** section.
   * Click the button to copy your API key.
   * Open your terminal/command prompt and run the following command (replace `YOUR_API_KEY` with the key you just copied):
     ```
     vastai set api-key YOUR_API_KEY
     ```
4. **Configure your environment:**
   * Copy the `.env.example` file and rename it to `.env`:
     ```
     cp .env.example .env
     ```
   * Open `.env` in a text editor and adjust the settings (Target Price, GPU Name, Disk Size, etc.) to match your needs.

## Usage

Run the script from your terminal:

```
python vastai_auto_renter.py
```

The script will begin searching the market. You can leave it running in the background. Once it finds a suitable machine, it will rent it, alert you, and begin monitoring the boot process until the Jupyter notebook is ready to open in your Vast.ai dashboard. Press `Ctrl+C` to stop the script at any time.
