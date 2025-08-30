This project is a command-line tool that calculates implied betting odds based on the current prices of IBIT (iShares Bitcoin Trust) and Bitcoin (BTC). It fetches the current prices from Yahoo Finance and Kraken Futures (with
CoinGecko as a fallback), calculates a strike price table, and displays the results in a formatted table in the terminal.

Optionally, it can also update a Google Sheets spreadsheet with the calculated strike price data.

## Features

*   Fetches the current price of IBIT from Yahoo Finance.
*   Fetches the current price of Bitcoin from Kraken Futures (or CoinGecko as a fallback).
*   Calculates a table of strike prices and corresponding BTC hedge levels.
*   Displays the calculated data in a user-friendly table in the terminal.
*   Optionally updates a Google Sheets spreadsheet with the calculated data.

## Usage

1.  **Install dependencies:**

    ```bash
    pip install requests python-dotenv gspread google-auth
    ```

2.  **Configure Google Sheets integration (optional):**

    *   Set up a Google Cloud project and enable the Google Sheets API.
    *   Create a service account and download the credentials file (service-account-key.json).
    *   Set the following environment variables:
        *   `GOOGLE_CREDENTIALS_FILE`: Path to the service account key file.
        *   `GOOGLE_SHEET_ID`: ID of the Google Sheet.
        *   `GOOGLE_WORKSHEET_ID`: ID of the worksheet to update.

3.  **Run the script:**

    ```bash
    python ibit_calculator.py
    ```

## Environment Variables

The following environment variables can be configured:

*   `GOOGLE_CREDENTIALS_FILE`: Path to the Google service account key file (default: `service-account-key.json`).
*   `GOOGLE_SHEET_ID`: ID of the Google Sheet (default: `your_google_sheet_id`).
*   `GOOGLE_WORKSHEET_ID`: ID of the Google Worksheet (default: `worksheet_id`).



## A service-account-key.json file is a JSON file that contains the credentials for a Google Cloud service account. It typically includes the following fields:

* type:  The type of credential, which is usually "service_account".
* project_id: The ID of the Google Cloud project.
* private_key_id: A unique identifier for the private key.
* private_key: The private key itself (a very long string).  This is the most sensitive part of the file.
* client_email: The email address of the service account.
* client_id: The client ID of the service account.
* auth_uri: The URI for authentication.
* token_uri: The URI for obtaining access tokens.
* auth_provider_x509_cert_url: The URL for the authentication provider's X.509 certificate.
* client_x509_cert_url: The URL for the service account's X.509 certificate.

## Dependencies

*   `requests`: For making HTTP requests to fetch market data.
*   `python-dotenv`: For loading environment variables from a `.env` file.
*   `gspread`: For interacting with the Google Sheets API.
*   `google-auth`: For authenticating with Google Cloud services.