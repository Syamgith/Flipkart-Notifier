# Flipkart Stock Notifier

A Python script that monitors Flipkart product stock and sends notifications via Telegram when a product comes in stock.

## Features

- Real-time stock monitoring for Flipkart products
- Instant Telegram notifications when products come in stock
- Configurable check intervals
- Detailed logging
- Error handling and recovery

## Prerequisites

- Python 3.7 or higher
- A Telegram account
- A Telegram bot token (obtained from @BotFather)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/syamgith/flipkart-notifier.git
cd flipkart-notifier
```

2. Install the required packages:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up your Telegram bot:

   - Message @BotFather on Telegram
   - Create a new bot using the `/newbot` command
   - Get your bot token
   - Start a chat with your bot
   - Get your chat ID (you can use @userinfobot to get your chat ID)

4. Create your environment file:

   - create .env file in the root

```bash
touch .env
```

5. Edit the `.env` file with your configuration:
   You can configure the following in your `.env` file:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID
- `FLIPKART_PRODUCT_URL`: The URL of the Flipkart product to monitor
- `CHECK_INTERVAL`: Time between checks in seconds (default: 60)

## Usage

Run the script:

```bash
python src/main.py
```

The script will:

- Start monitoring the specified Flipkart product
- Send you a Telegram notification when the product comes in stock
- Log all activities to the console

To stop the script, press Ctrl+C.

## Troubleshooting

1. If you're not receiving notifications:

   - Make sure you've started a chat with your bot
   - Verify your chat ID is correct
   - Check if your bot token is valid

2. If the script stops working:
   - Check the logs for error messages
   - Verify your internet connection
   - Make sure the product URL is valid

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.
