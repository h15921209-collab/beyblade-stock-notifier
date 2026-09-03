import re
import json
import logging
from typing import Optional
from bs4 import BeautifulSoup
from .base import BaseScraper, ProductInfo, StockStatus

logger = logging.getLogger(__name__)

class EsliteScraper(BaseScraper):
    name = "誠品線上"

    def can_handle(self, url: str) -> bool:
        return "eslite.com" in url.lower()

    def check_stock(self, url: str, custom_config: Optional[dict] = None) -> ProductInfo:
        clean_buy_url = url

        try:
            headers = self.get_headers({
                "Referer": "https://www.eslite.com/",
            })
            resp = self.session.get(url, headers=headers, timeout=self.timeout)
            if resp.status_code == 404:
                return ProductInfo(
                    url=url,
                    platform_name=self.name,
                    title="商品不存在或已下架",
                    status=StockStatus.OUT_OF_STOCK,
                    direct_buy_url=clean_buy_url,
                    error_msg="404 Not Found"
                )

            resp.raise_for_status()
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            # 1. 抓取標題
            title = None
            title_meta = soup.find("meta", property="og:title")
            if title_meta and title_meta.get("content"):
                title = title_meta.get("content").strip()
            elif soup.title:
                title = soup.title.string.replace("| 誠品線上", "").strip()

            # 2. 抓取價格
            price = None
            price_meta = soup.find("meta", property="product:price:amount")
            if price_meta and price_meta.get("content"):
                try:
                    price = float(price_meta.get("content"))
                except ValueError:
                    pass

            if not price:
                price_match = re.search(r'NT\$\s*([0-9,]+)', html)
                if price_match:
                    price = float(price_match.group(1).replace(",", ""))

            # 3. 判斷庫存
            # Next.js hydration data if present
            in_stock = True
            next_data_script = soup.find("script", id="__NEXT_DATA__")
            if next_data_script and next_data_script.string:
                try:
                    nd = json.loads(next_data_script.string)
                    props = nd.get("props", {}).get("pageProps", {})
                    # 搜尋 product 物件
                    product_obj = props.get("product") or props.get("productData")
                    if isinstance(product_obj, dict):
                        if not title:
                            title = product_obj.get("name")
                        if not price:
                            price = product_obj.get("retail_price") or product_obj.get("final_price")
                        # 庫存判斷欄位
                        is_active = product_obj.get("is_active", True)
                        stock_qty = product_obj.get("stock", 1)
                        can_buy = product_obj.get("can_buy", True)
                        if not is_active or stock_qty <= 0 or not can_buy:
                            in_stock = False
                except Exception:
                    pass

            # 關鍵字備援檢查
            out_of_stock_kws = ["缺貨中", "已售完", "補貨中", "售完", "無庫存", "商品已下架"]
            for kw in out_of_stock_kws:
                if kw in html:
                    in_stock = False
                    break

            if ("放入購物車" in html or "直接購買" in html) and "已售完" not in html:
                in_stock = True

            image_url = None
            img_meta = soup.find("meta", property="og:image")
            if img_meta and img_meta.get("content"):
                image_url = img_meta.get("content")

            return ProductInfo(
                url=url,
                platform_name=self.name,
                title=title or "戰鬥陀螺X (誠品線上)",
                price=price,
                status=StockStatus.IN_STOCK if in_stock else StockStatus.OUT_OF_STOCK,
                image_url=image_url,
                direct_buy_url=clean_buy_url
            )

        except Exception as e:
            logger.error(f"[Eslite] 抓取失敗 ({url}): {e}")
            return ProductInfo(
                url=url,
                platform_name=self.name,
                title="誠品線上商品",
                status=StockStatus.ERROR,
                direct_buy_url=clean_buy_url,
                error_msg=str(e)
            )
