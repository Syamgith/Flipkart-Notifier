import requests
import time
import telegram
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import re # Added for regex-based title extraction

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
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.flipkart.com/",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1"
        }


    def check_stock(self, product_url):
        """
        Check if a product is in stock on Flipkart by scraping the product page.
        :param product_url: URL of the Flipkart product
        :return: Tuple of (is_in_stock, product_name)
        """
        try:
            logging.info(f"Fetching product page: {product_url}")
            # Increased timeout from 10 to 20 seconds
            response = requests.get(product_url, headers=self.headers, timeout=20)
            response.raise_for_status()  # Raise an exception for bad status codes
            html_content = response.text

            product_name = "Unknown Product"
            # Try to extract product name from title tag
            title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
            if title_match:
                full_title = title_match.group(1).strip()
                # Clean up the title (e.g., remove " - Flipkart.com")
                product_name = full_title.split(' - ')[0].split('|')[0].strip()
                if "flipkart.com" in product_name.lower() or not product_name: # if title is generic
                     # Fallback: Try to find a more specific product name using a common span class
                    name_match_specific = re.search(r'<span class="B_NuCI">(.*?)</span>', html_content, re.IGNORECASE | re.DOTALL)
                    if name_match_specific:
                        product_name = name_match_specific.group(1).strip()
                    else: # if still not found, use a generic name or part of url
                        product_name = product_url.split('/')[-2].replace('-', ' ').title() if product_url.count('/') > 3 else "Product"


            # Check for "inStock" in JSON-LD script tag if available
            json_ld_stock_match = re.search(r'"availability"\s*:\s*"http://schema.org/InStock"', html_content, re.IGNORECASE)
            if json_ld_stock_match:
                logging.info(f"Product '{product_name}' found in stock via JSON-LD.")
                return True, product_name

            # Fallback to button text/class search
            # Check for Buy Now or Add to Cart buttons (often within specific classes)
            buy_now_button_present = re.search(r'>BUY NOW<|<button[^>]*class="[^"]*(?:_2U9uOA|_2KpZ6l|_2ihvCB|_3AWRsL)[^"]*"[^>]*>\s*(?:<span>)?\s*(BUY NOW|ADD TO CART)\s*(?:</span>)?\s*</button>', html_content, re.IGNORECASE)

            if buy_now_button_present:
                logging.info(f"Product '{product_name}' found in stock (Buy Now / Add to Cart button found).")
                return True, product_name

            # Check for out of stock indicators
            sold_out_present = re.search(r'>SOLD OUT<|>NOTIFY ME<', html_content, re.IGNORECASE)
            json_ld_out_of_stock_match = re.search(r'"availability"\s*:\s*"http://schema.org/OutOfStock"', html_content, re.IGNORECASE)

            if sold_out_present or json_ld_out_of_stock_match:
                logging.info(f"Product '{product_name}' is out of stock (Sold Out / Notify Me indicator found).")
                return False, product_name # Return product name even if out of stock for logging consistency

            # If none of the above are found, it's ambiguous. Default to out of stock to be safe.
            # Flipkart pages can be complex and change. This is a best-effort approach.
            logging.warning(f"Stock status for '{product_name}' is ambiguous. Assuming out of stock. Page URL: {product_url}")
            return False, product_name

        except requests.exceptions.Timeout as e:
            logging.error(f"Timeout error fetching product page {product_url}: {str(e)}")
            return False, "Error fetching product (Timeout)"
        except requests.exceptions.RequestException as e: # Catches other request-related errors like connection errors
            logging.error(f"Request error fetching product page {product_url}: {str(e)}")
            return False, "Error fetching product (Request Error)"
        except Exception as e:
            logging.error(f"Error parsing stock status for {product_url}: {str(e)}")
            return False, "Error parsing product data"

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
                # Optional: Stop monitoring after first notification or wait longer
                logging.info(f"Product {product_name} is IN STOCK! Notification sent.")
                # Consider adding a longer sleep here, or exiting if only one notification is needed.
                # For continuous monitoring of re-stock, keep the interval.
            else:
                logging.info(f"Product '{product_name}' not in stock. Checking again in {check_interval} seconds...")
            
            time.sleep(check_interval) 