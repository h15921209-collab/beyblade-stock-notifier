import re
import logging
from typing import Optional, Tuple
from bs4 import BeautifulSoup
from .base import BaseScraper, ProductInfo, StockStatus

logger = logging.getLogger(__name__)

class ShopeeFunboxScraper(BaseScraper):
    name = "蝦皮商城 麗嬰國際官方旗艦店"

    def can_handle(self, url: str) -> bool:
        return "shopee.tw" in url.lower()

    def _extract_ids(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """解析 shopid 與 itemid"""
        # 格式 1: /product/123456/78901234
        m1 = re.search(r'/product/(\d+)/(\d+)', url)
        if m1:
            return m1.group(1), m1.group(2)

        # 格式 2: /something-i.123456.78901234
        m2 = re.search(r'-i\.(\d+)\.(\d+)', url)
        if m2:
            return m2.group(1), m2.group(2)

        return None, None

    def check_stock(self, url: str, custom_config: Optional[dict] = None) -> ProductInfo:
        shop_id, item_id = self._extract_ids(url)
        clean_buy_url = f"https://shopee.tw/product/{shop_id}/{item_id}" if (shop_id and item_id) else url

        # 若未提供 ID，嘗試直接造訪網址
        if not item_id:
            return ProductInfo(
                url=url,
                platform_name=self.name,
                title="無效的蝦皮網址",
                status=StockStatus.ERROR,
                direct_buy_url=clean_buy_url,
                error_msg="無法從網址提取 shop_id 與 item_id"
            )

        # 檢查設定檔中是否有使用者提供的 Cookie (例如 SPC_EC)
        user_cookies = {}
        if custom_config and "shopee_cookie" in custom_config:
            user_cookies["cookie"] = custom_config["shopee_cookie"]

        api_url = f"https://shopee.tw/api/v4/item/get?itemid={item_id}&shopid={shop_id}"
        
        headers = self.get_headers({
            "Referer": clean_buy_url,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
            "X-Shopee-Language": "zh-Hant",
        })
        if "cookie" in user_cookies:
            headers["Cookie"] = user_cookies["cookie"]

        try:
            resp = self.session.get(api_url, headers=headers, timeout=self.timeout)
            
            # 若 API 成功
            if resp.status_code == 200:
                data = resp.json().get("data")
                if data:
                    title = data.get("name", "戰鬥陀螺X商品 (蝦皮商城)")
                    # 蝦皮價格通常除以 100000
                    raw_price = data.get("price", 0)
                    price = float(raw_price) / 100000.0 if raw_price > 10000 else float(raw_price)
                    
                    stock = data.get("stock", 0)
                    in_stock = int(stock) > 0

                    image_url = None
                    images = data.get("images", [])
                    if images:
                        image_url = f"https://cf.shopee.tw/file/{images[0]}"

                    return ProductInfo(
                        url=url,
                        platform_name=self.name,
                        title=title,
                        price=price,
                        status=StockStatus.IN_STOCK if in_stock else StockStatus.OUT_OF_STOCK,
                        stock_qty=int(stock),
                        image_url=image_url,
                        direct_buy_url=clean_buy_url
                    )

            # 若 API 被 Cloudflare / 403 攔截，嘗試 HTML 備援
            html_headers = self.get_headers({"Referer": "https://shopee.tw/"})
            html_resp = self.session.get(clean_buy_url, headers=html_headers, timeout=self.timeout)
            if html_resp.status_code == 200:
                soup = BeautifulSoup(html_resp.text, "html.parser")
                title_meta = soup.find("meta", property="og:title")
                title = title_meta["content"] if title_meta else "蝦皮商城商品"
                
                # 簡單檢查頁面文字
                in_stock = True
                if "已售完" in html_resp.text or "此商品已售完" in html_resp.text or "0 件在庫" in html_resp.text:
                    in_stock = False

                return ProductInfo(
                    url=url,
                    platform_name=self.name,
                    title=title,
                    status=StockStatus.IN_STOCK if in_stock else StockStatus.OUT_OF_STOCK,
                    direct_buy_url=clean_buy_url
                )

            # 若皆失敗
            return ProductInfo(
                url=url,
                platform_name=self.name,
                title="蝦皮商城商品",
                status=StockStatus.UNKNOWN,
                direct_buy_url=clean_buy_url,
                error_msg=f"蝦皮防爬機制限制 (HTTP {resp.status_code})"
            )

        except Exception as e:
            logger.error(f"[Shopee] 抓取失敗 ({url}): {e}")
            return ProductInfo(
                url=url,
                platform_name=self.name,
                title="蝦皮商城商品",
                status=StockStatus.ERROR,
                direct_buy_url=clean_buy_url,
                error_msg=str(e)
            )
