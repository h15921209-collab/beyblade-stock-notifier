import re
import logging
from typing import Optional
from bs4 import BeautifulSoup
from .base import BaseScraper, ProductInfo, StockStatus

logger = logging.getLogger(__name__)

class KubiScraper(BaseScraper):
    name = "酷比樂玩具商城"

    def can_handle(self, url: str) -> bool:
        low = url.lower()
        return "kubi.com.tw" in low or "amuzinc.com" in low

    def check_stock(self, url: str, custom_config: Optional[dict] = None) -> ProductInfo:
        clean_buy_url = url

        try:
            resp = self.session.get(
                url,
                headers=self.get_headers({"Referer": "https://preorder.amuzinc.com/"}),
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

            # 1. 抓取標題
            title = None
            title_meta = soup.find("meta", property="og:title")
            if title_meta and title_meta.get("content"):
                title = title_meta.get("content").strip()
            elif soup.title:
                title = soup.title.string.replace("酷比樂", "").strip()

            # 2. 抓取價格
            price = None
            price_meta = soup.find("meta", property="product:price:amount")
            if price_meta and price_meta.get("content"):
                try:
                    price = float(price_meta.get("content"))
                except ValueError:
                    pass

            if not price:
                price_match = re.search(r'NT\$?\s*([0-9,]+)', resp.text)
                if price_match:
                    price = float(price_match.group(1).replace(",", ""))

            # 3. 判斷庫存狀態
            in_stock = True
            text_lower = resp.text.lower()
            out_of_stock_kws = ["缺貨", "售完", "已售完", "暫無庫存", "補貨中", "庫存不足", "out of stock"]
            for kw in out_of_stock_kws:
                if kw in resp.text:
                    in_stock = False
                    break

            # 檢查購買按鈕
            buy_btn = soup.find(lambda tag: tag.name in ["button", "a", "input"] and any(w in tag.text for w in ["加入購物車", "立即購買", "直接購買"]))
            if buy_btn:
                disabled = buy_btn.get("disabled") is not None or "disabled" in buy_btn.get("class", [])
                if not disabled and in_stock:
                    in_stock = True

            image_url = None
            img_meta = soup.find("meta", property="og:image")
            if img_meta and img_meta.get("content"):
                image_url = img_meta.get("content")

            return ProductInfo(
                url=url,
                platform_name=self.name,
                title=title or "戰鬥陀螺X (酷比樂玩具)",
                price=price,
                status=StockStatus.IN_STOCK if in_stock else StockStatus.OUT_OF_STOCK,
                image_url=image_url,
                direct_buy_url=clean_buy_url
            )

        except Exception as e:
            logger.error(f"[Kubi] 抓取失敗 ({url}): {e}")
            return ProductInfo(
                url=url,
                platform_name=self.name,
                title="酷比樂玩具商品",
                status=StockStatus.ERROR,
                direct_buy_url=clean_buy_url,
                error_msg=str(e)
            )
