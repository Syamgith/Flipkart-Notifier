import asyncio
import os
from dotenv import load_dotenv
from notifier import FlipkartStockNotifier
import logging

# Load environment variables
load_dotenv('.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    # Get configuration from environment variables
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    product_url = os.getenv('FLIPKART_PRODUCT_URL')
    check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
    scraperapi_key = os.getenv('SCRAPERAPI_KEY') # Get ScraperAPI key

    if not all([telegram_token, chat_id, product_url]):
        logging.error("Missing required environment variables (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, FLIPKART_PRODUCT_URL). Please check your .env file.")
        return

    # Initialize and run the notifier
    notifier = FlipkartStockNotifier(telegram_token, chat_id, scraperapi_key=scraperapi_key)
    await notifier.monitor_product(product_url, check_interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Program stopped by user")
    except Exception as e:
        logging.error(f"An unexpected error occurred in main: {str(e)}", exc_info=True) 