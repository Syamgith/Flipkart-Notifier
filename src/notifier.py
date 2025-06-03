import requests
import time
import telegram
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import re # Added for regex-based title extraction
from urllib.parse import urlparse # Added for URL parsing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FlipkartStockNotifier:
    def __init__(self, telegram_token, chat_id, scraperapi_key=None):
        """
        Initialize the Flipkart Stock Notifier
        :param telegram_token: Telegram bot token
        :param chat_id: Telegram chat ID for notifications
        :param scraperapi_key: Optional ScraperAPI key
        """
        self.telegram_bot = telegram.Bot(token=telegram_token)
        self.chat_id = chat_id
        self.scraperapi_key = scraperapi_key
        self.post_code = os.getenv('POST_CODE') # Load POST_CODE from .env

        self.direct_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.flipkart.com/",
            "DNT": "1", # Do Not Track
            "Upgrade-Insecure-Requests": "1"
        }
        self.api_headers = {
            "accept": "*/*",
            "accept-language": "en-GB,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.flipkart.com",
            # Referer will be set dynamically per product
            "sec-ch-ua": '"Chromium";v="125", "Google Chrome";v="125", "Not.A/Brand";v="24"',
            "sec-ch-ua-mobile": "?0", # Assuming desktop context
            "sec-ch-ua-platform": '"macOS"', # Assuming desktop context
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "X-User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 FKUA/website/42/website/Desktop"
            # User-Agent will be set to X-User-Agent value
        }
        self.api_headers["User-Agent"] = self.api_headers["X-User-Agent"]

    def check_stock_with_pincode(self, product_url):
        """
        Check if a product is in stock for a given pincode using Flipkart's internal API.
        Uses ScraperAPI for the API call if scraperapi_key is available.
        If the API check fails or essential data is missing, it falls back to check_stock().
        :param product_url: URL of the Flipkart product
        :return: Tuple of (is_in_stock, product_name)
        """
        flipkart_api_url = "https://1.rome.api.flipkart.com/api/4/page/fetch"
        parsed_url = urlparse(product_url)
        page_uri = parsed_url.path
        if parsed_url.query:
            page_uri += "?" + parsed_url.query

        flipkart_payload = {
            "pageUri": page_uri,
            "locationContext": {"pincode": self.post_code},
            "isReloadRequest": True
        }
        
        # Default product name if API extraction fails but API call itself is okay
        product_name_api = product_url.split('/')[-2].replace('-', ' ').title() if product_url.count('/') > 3 else "Product via API"

        try:
            if self.scraperapi_key:
                scraperapi_url = 'http://api.scraperapi.com'
                scraper_params = {
                    "api_key": self.scraperapi_key,
                    "url": flipkart_api_url, # Flipkart API URL goes into params for ScraperAPI
                    "keep_headers": True   # Tell ScraperAPI to forward our headers
                }
                
                # Headers intended for the TARGET (Flipkart API), to be forwarded by ScraperAPI
                headers_for_target = self.api_headers.copy()
                headers_for_target["referer"] = product_url
                # self.api_headers already contains 'Content-Type': 'application/json',
                # 'X-User-Agent', 'Origin', etc., which are needed by the Flipkart API.

                logging.info(f"Fetching product page via ScraperAPI (keep_headers=True) to Flipkart API for pincode {self.post_code}: {product_url} (target: {flipkart_api_url})")
                response = requests.post(
                    scraperapi_url,
                    params=scraper_params,      # ScraperAPI key, target URL, and keep_headers flag
                    json=flipkart_payload,      # Flipkart's JSON payload (body for the target)
                    headers=headers_for_target, # Headers to be forwarded to the Flipkart API
                    timeout=60                  # Generous timeout for ScraperAPI
                )
            else:
                # Direct call to Flipkart API
                direct_api_headers = self.api_headers.copy()
                direct_api_headers["referer"] = product_url
                logging.info(f"Fetching product page via direct API call for pincode {self.post_code}: {product_url}")
                response = requests.post(
                    flipkart_api_url,
                    headers=direct_api_headers,
                    json=flipkart_payload,
                    timeout=30
                )
            
            response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses
            data = response.json()       # Raises JSONDecodeError if not JSON

            # logging.info(f"The dataaaa is {data}") # User's commented out log
            # Extract product name from API
            try:
                product_name_api = data['RESPONSE']['pageData']['pageContext']['titles']['title']
            except (KeyError, TypeError) as e_name:
                logging.warning(f"Could not extract product name from API response for {product_url}. Error: {e_name}. Using default: {product_name_api}")

            # Check stock status from API
            try:
                availability_status = data['RESPONSE']['pageData']['pageContext']['fdpEventTracking']['events']['psi']['pls']['availabilityStatus']
                is_available = data['RESPONSE']['pageData']['pageContext']['fdpEventTracking']['events']['psi']['pls']['isAvailable']
                # is_serviceable = data['RESPONSE']['pageData']['pageContext']['fdpEventTracking']['events']['psi']['pls']['isServiceablee'] # Original
                is_serviceable = data['RESPONSE']['pageData']['pageContext']['trackingDataV2']['serviceable'] # updated

                if availability_status == "IN_STOCK" and is_available and is_serviceable:
                    logging.info(f"Product '{product_name_api}' found IN STOCK for pincode {self.post_code} via API.")
                    return True, product_name_api
                else:
                    logging.info(f"Product '{product_name_api}' is OUT OF STOCK or not serviceable for pincode {self.post_code} via API. Status: {availability_status}, Available: {is_available}, Serviceable: {is_serviceable}")
                    return False, product_name_api # API successfully determined out of stock, no fallback needed.

            except (KeyError, TypeError) as e_stock:
                # This means API call was successful (200 OK, JSON response), but specific keys for stock status were missing/wrong.
                logging.warning(f"Error parsing stock status keys from successful API response for '{product_name_api}' at {product_url}. Error: {e_stock}. Response snippet: {str(data)[:200]}. Falling back to HTML scraping.")
                return self.check_stock(product_url)

        except requests.exceptions.Timeout as e_timeout:
            logging.warning(f"Timeout error fetching product page via API for {product_url}: {str(e_timeout)}. Falling back to HTML scraping.")
            return self.check_stock(product_url)
        except requests.exceptions.HTTPError as e_http:
            logging.warning(f"HTTP error fetching product page via API for {product_url} (Status: {e_http.response.status_code}): {str(e_http)}. Response: {e_http.response.text[:200]}. Falling back to HTML scraping.")
            return self.check_stock(product_url)
        except requests.exceptions.RequestException as e_req: # Catches other request-related errors
            logging.warning(f"Request error fetching product page via API for {product_url}: {str(e_req)}. Falling back to HTML scraping.")
            return self.check_stock(product_url)
        except Exception as e_generic: # Catch other potential errors like JSONDecodeError or unexpected issues
            logging.warning(f"Generic error or unexpected response during API stock check for {product_url}: {str(e_generic)}. Falling back to HTML scraping.")
            return self.check_stock(product_url)

    def check_stock(self, product_url):
        """
        Check if a product is in stock on Flipkart by scraping the product page.
        :param product_url: URL of the Flipkart product
        :return: Tuple of (is_in_stock, product_name)
        """
        try:
            html_content = ""
            if self.scraperapi_key:
                scraperapi_url = f'http://api.scraperapi.com?api_key={self.scraperapi_key}&url={product_url.replace("&", "%26")}' # URL encode ampersands for ScraperAPI
                logging.info(f"Fetching product page via ScraperAPI: {product_url}")
                # When using ScraperAPI, it's often better to let them handle headers, including User-Agent.
                # Timeout should be generous for ScraperAPI as it might be retrying on its end.
                response = requests.get(scraperapi_url, timeout=60) # Increased timeout for ScraperAPI
            else:
                logging.info(f"Fetching product page directly: {product_url}")
                response = requests.get(product_url, headers=self.direct_headers, timeout=20)
            
            response.raise_for_status()
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
            logging.error(f"Request error fetching product page {product_url} (Status: {e.response.status_code if e.response else 'N/A'}): {str(e)}")
            return False, f"Error fetching product (HTTP {e.response.status_code if e.response else 'Error'})"
        except Exception as e:
            logging.error(f"Generic error parsing stock status for {product_url}: {str(e)}")
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
        if self.post_code:
            logging.info(f"POST_CODE '{self.post_code}' found. Will use API for stock checks (with HTML fallback on API error).")
        elif self.scraperapi_key:
            logging.info(f"No POST_CODE. ScraperAPI key found, will use ScraperAPI for HTML scraping.")
        else:
            logging.info("No POST_CODE and no ScraperAPI key. Will use direct HTML scraping.")
        
        while True:
            in_stock = False
            # Initialize with a generic name, it will be updated by the check methods
            product_name = f"Unknown Product ({product_url})" 

            if self.post_code:
                # check_stock_with_pincode will internally fall back to check_stock if API fails
                in_stock, product_name = self.check_stock_with_pincode(product_url)
            else:
                # No post_code, so use the original check_stock directly
                in_stock, product_name = self.check_stock(product_url)
            
            if in_stock:
                await self.send_telegram_notification(product_name, product_url)
                logging.info(f"Product '{product_name}' is IN STOCK! Notification sent for {product_url}.")
            else:
                # If product_name contains "Error", it indicates the final method used (API, its fallback HTML, or direct HTML) ultimately failed.
                if "Error" in product_name:
                     logging.error(f"Stock check ultimately failed for {product_url}. Last error reported: {product_name}")
                else:
                    # Product is confirmed out of stock by the successful method (or its fallback)
                    logging.info(f"Product '{product_name}' not in stock for {product_url}. Checking again in {check_interval} seconds...")
            
            time.sleep(check_interval) 