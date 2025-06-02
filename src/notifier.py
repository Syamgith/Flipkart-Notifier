import requests
import time
import telegram
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FlipkartStockNotifier:
    def __init__(self, telegram_token, chat_id):
        """
        Initialize the Flipkart Stock Notifier
        :param telegram_token: Telegram bot token
        :param chat_id: Telegram chat ID for notifications
        """
        self.telegram_bot = telegram.Bot(token=telegram_token)
        self.chat_id = chat_id
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def check_stock(self, product_url):
        """
        Check if a product is in stock on Flipkart
        :param product_url: URL of the Flipkart product
        :return: Tuple of (is_in_stock, product_name)
        """
        try:
            # Extract product ID from URL
            product_id = product_url.split('/')[-1].split('?')[0]
            
            # Construct API URL
            api_url = f"https://www.flipkart.com/api/3/page/dynamic/product-reviews?pid={product_id}"
            
            response = requests.get(api_url, headers=self.headers)
            data = response.json()
            
            # Check if product is in stock
            if 'productDetails' in data:
                product_details = data['productDetails']
                if product_details.get('inStock', False):
                    return True, product_details.get('title', 'Product')
            return False, None
            
        except Exception as e:
            logging.error(f"Error checking stock: {str(e)}")
            return False, None

    async def send_telegram_notification(self, product_name, product_url):
        """
        Send a notification via Telegram
        :param product_name: Name of the product
        :param product_url: URL of the product
        """
        message = f"🚨 STOCK ALERT! 🚨\n\n{product_name} is now in stock!\n\nBuy it here: {product_url}"
        try:
            await self.telegram_bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logging.info(f"Notification sent for {product_name}")
        except Exception as e:
            logging.error(f"Error sending notification: {str(e)}")

    async def monitor_product(self, product_url, check_interval=60):
        """
        Monitor a product for stock availability
        :param product_url: Flipkart product URL
        :param check_interval: Time between checks in seconds
        """
        logging.info(f"Starting to monitor product: {product_url}")
        
        while True:
            in_stock, product_name = self.check_stock(product_url)
            
            if in_stock:
                await self.send_telegram_notification(product_name, product_url)
                logging.info(f"Product {product_name} is in stock!")
            else:
                logging.info(f"Product not in stock. Checking again in {check_interval} seconds...")
            
            time.sleep(check_interval) 