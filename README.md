# Flipkart Stock Notifier

A Python script that monitors Flipkart product stock and sends notifications via Telegram when a product comes in stock.

## Features

- Real-time stock monitoring for Flipkart products
- Instant Telegram notifications when products come in stock
- Configurable check intervals
- Detailed logging
- Error handling and recovery
- Optional: Proxy support via ScraperAPI to reduce chances of getting blocked.

## Prerequisites

- Python 3.7 or higher
- A Telegram account
- A Telegram bot token (obtained from @BotFather)

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/Syamgith/Flipkart-Stock-Notifier.git # Replace with your repo URL if forked
   cd flipkart-notifier
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up your Telegram bot:

   - Message `@BotFather` on Telegram.
   - Create a new bot using the `/newbot` command.
   - Note down the bot token you receive.
   - Start a chat with your newly created bot.
   - Get your chat ID (you can message `@userinfobot` on Telegram, send it a message, and it will reply with your chat ID).

4. Create your environment file(.env) in root folder:
   - Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   - **Important**: Edit `.env` with your actual details.

## Configuration (`.env`)

Open the created `.env` and fill in the following details:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID.
- `FLIPKART_PRODUCT_URL`: The full URL of the Flipkart product you want to monitor.
- `CHECK_INTERVAL`: Time in seconds between stock checks (e.g., `60` for 1 minute, `900` for 15 minutes).
  _Be respectful to Flipkart's servers; very frequent checks (e.g., less than a minute) can lead to your IP being temporarily or permanently blocked._

### Optional: Using ScraperAPI (Recommended for Reliability)

Flipkart might block direct requests if they detect scraping activity. To improve reliability and reduce the chances of being blocked, this script supports using [ScraperAPI](https://www.scraperapi.com/). They offer a free tier that is usually sufficient for personal use.

1.  **Sign up** at [ScraperAPI](https://www.scraperapi.com/) to get your free API key.
2.  Add your ScraperAPI key to your `.env` file:
    `env
SCRAPERAPI_KEY=your_scraperapi_key_here
`
    If `SCRAPERAPI_KEY` is set, the script will automatically route its requests through ScraperAPI. If it's left blank, the script will attempt to make direct requests to Flipkart (which may sometimes encounter blocks).

## Usage

Run the script from the project's root directory:

```bash
python src/main.py
```

The script will:

- Start monitoring the specified Flipkart product.
- Use ScraperAPI if a key is provided, otherwise make direct requests.
- Send you a Telegram notification when the product comes in stock.
- Log all activities to the console.

To stop the script, press `Ctrl+C`.

## Troubleshooting

- **No notifications?**
  - Double-check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`.
  - Ensure you have started a chat with your bot on Telegram.
  - Check the script's console output for any error messages.
- **Script errors out or product always shows as "Error fetching product"?**
  - **If not using ScraperAPI:** Your IP might be temporarily blocked by Flipkart.
    - Try increasing `CHECK_INTERVAL` significantly (e.g., to `900` or `1800`).
    - Consider using ScraperAPI (see section above).
  - **If using ScraperAPI:** Ensure your ScraperAPI key is correct and your account has available credits.
  - Verify the `FLIPKART_PRODUCT_URL` is correct and accessible in a browser.
  - Check for network connectivity issues.
- **"Read timed out" errors:**
  - The script has a timeout for requests. If Flipkart's pages are loading very slowly, this can occur. Using ScraperAPI can often help mitigate this as it has more robust infrastructure.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests!

## License

This project is licensed under the MIT License. See the `LICENSE` file for details (if one is created).
