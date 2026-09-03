import json
import logging
from typing import Optional
from bs4 import BeautifulSoup
from .base import BaseScraper, ProductInfo, StockStatus

logger = logging.getLogger(__name__)

class ToysrusScraper(BaseScraper):
    name = "玩具反斗城台灣官網"

    def can_handle(self, url: str) -> bool:
        return "toysrus.com.tw" in url.lower()

    def check_stock(self, url: str, custom_config: Optional[dict] = None) -> ProductInfo:
        clean_buy_url = url

        try:
            resp = self.session.get(
                url,
                headers=self.get_headers({
                    "Referer": "https://www.toysrus.com.tw/",
                }),
                timeout=self.timeout
            )
            if resp.status_code == 404:
                return ProductInfo(
                    url=url,
                    platform_name=self.name,
                    title="商品頁面不存在或已下架",
                    status=StockStatus.OUT_OF_STOCK,
                    direct_buy_url=clean_buy_url,
                    error_msg="404 Not Found"
                )

            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # 1. 優先嘗試從 Schema.org JSON-LD 讀取結構化資料
            product_data = None
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get("@type") == "Product":
                        product_data = data
                        break
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get("@type") == "Product":
                                product_data = item
                                break
                except Exception:
                    continue

            title = None
            price = None
            in_stock = False

            if product_data:
                title = product_data.get("name")
                offers = product_data.get("offers", {})
                if isinstance(offers, dict):
                    price_val = offers.get("price")
                    if price_val:
                        try:
                            price = float(price_val)
                        except (ValueError, TypeError):
                            pass
                    avail = str(offers.get("availability", "")).lower()
                    if "instock" in avail:
                        in_stock = True
                    elif "outofstock" in avail:
                        in_stock = False

            # 2. DOM 備援解析
            if not title:
                h1 = soup.find("h1", class_="product-name") or soup.find("h1")
                if h1:
                    title = h1.text.strip()
                else:
                    title = soup.title.string.strip() if soup.title else "戰鬥陀螺X (玩具反斗城)"

            if not price:
                price_el = soup.find(class_=lambda c: c and ("price" in c or "sales" in c))
                if price_el:
                    import re
                    match = re.search(r'(\d[\d,]*)', price_el.text)
                    if match:
                        price = float(match.group(1).replace(",", ""))

            # 檢查加入購物車按鈕
            add_cart_btn = soup.find("button", class_=lambda c: c and "add-to-cart" in c)
            if add_cart_btn:
                disabled = add_cart_btn.get("disabled") is not None or "disabled" in add_cart_btn.get("class", [])
                btn_text = add_cart_btn.text.strip()
                if "售完" in btn_text or "缺貨" in btn_text:
                    in_stock = False
                elif not disabled and ("加入" in btn_text or "購買" in btn_text or "立即" in btn_text):
                    in_stock = True

            return ProductInfo(
                url=url,
                platform_name=self.name,
                title=title or "戰鬥陀螺X商品 (玩具反斗城)",
                price=price,
                status=StockStatus.IN_STOCK if in_stock else StockStatus.OUT_OF_STOCK,
                direct_buy_url=clean_buy_url
            )

        except Exception as e:
            logger.error(f"[Toysrus] 抓取失敗 ({url}): {e}")
            return ProductInfo(
                url=url,
                platform_name=self.name,
                title="玩具反斗城商品",
                status=StockStatus.ERROR,
                direct_buy_url=clean_buy_url,
                error_msg=str(e)
            )
