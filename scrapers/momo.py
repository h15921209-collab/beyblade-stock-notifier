import re
import logging
from typing import Optional
from bs4 import BeautifulSoup
from .base import BaseScraper, ProductInfo, StockStatus

logger = logging.getLogger(__name__)

class MomoScraper(BaseScraper):
    name = "Momo 購物網 Funbox 館"

    def can_handle(self, url: str) -> bool:
        return "momoshop.com.tw" in url.lower()

    def _extract_icode(self, url: str) -> Optional[str]:
        match = re.search(r'i_code=(\d+)', url)
        if match:
            return match.group(1)
        # 支援純數字
        if re.match(r'^\d+$', url.strip()):
            return url.strip()
        return None

    def check_stock(self, url: str, custom_config: Optional[dict] = None) -> ProductInfo:
        icode = self._extract_icode(url)
        if not icode:
            return ProductInfo(
                url=url,
                platform_name=self.name,
                title="無效的 Momo 網址",
                status=StockStatus.ERROR,
                error_msg="無法從網址取得商品代碼 (i_code)"
            )

        clean_buy_url = f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={icode}"
        mobile_url = f"https://m.momoshop.com.tw/goods.momo?i_code={icode}"

        try:
            # Momo 行動版頁面結構較乾淨且輕量
            headers = self.get_headers({
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
                "Referer": "https://m.momoshop.com.tw/",
            })
            resp = self.session.get(mobile_url, headers=headers, timeout=self.timeout)
            
            # 若行動版有跳轉或異常，嘗試桌面版
            if resp.status_code != 200:
                desktop_headers = self.get_headers({
                    "Referer": "https://www.momoshop.com.tw/",
                })
                resp = self.session.get(clean_buy_url, headers=desktop_headers, timeout=self.timeout)

            resp.raise_for_status()
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            # 1. 抓取品名
            title = None
            title_meta = soup.find("meta", property="og:title")
            if title_meta and title_meta.get("content"):
                title = title_meta.get("content").strip()
            elif soup.title:
                title = soup.title.string.replace("- momo 購物網", "").replace("-momo購物網", "").strip()

            # 2. 抓取價格
            price = None
            price_meta = soup.find("meta", property="product:price:amount")
            if price_meta and price_meta.get("content"):
                try:
                    price = float(price_meta.get("content"))
                except ValueError:
                    pass

            if not price:
                price_match = re.search(r'["\']salePrice["\']\s*:\s*["\']?(\d+)["\']?', html)
                if price_match:
                    price = float(price_match.group(1))

            # 0. 檢查是否遇到 Momo 防爬蟲驗證頁面 (Challenge Validation)
            if "Challenge Validation" in html or "robot" in html.lower() or (title and "Challenge Validation" in title):
                logger.warning(f"[Momo] 遇到防爬蟲驗證頁面 ({url})")
                return ProductInfo(
                    url=url,
                    platform_name=self.name,
                    title="Momo 購物網 (觸發驗證頁面)",
                    status=StockStatus.UNKNOWN,
                    direct_buy_url=clean_buy_url,
                    error_msg="Momo anti-bot challenge validation triggered"
                )

            # 3. 判斷庫存
            # Momo 頁面常見缺貨關鍵字
            out_of_stock_keywords = [
                "已售完", "補貨中", "完售", "售完補貨中", "暫時下架", "此商品已下架", "下架", "商品已無庫存"
            ]
            in_stock = True
            
            # 檢查按鈕或文字
            for kw in out_of_stock_keywords:
                if kw in html:
                    # 進一步確認是否在核心購物按鈕區塊
                    in_stock = False
                    break

            # 額外檢查是否有「立即購買」或「加入購物車」文字
            if ("立即購買" in html or "直接購買" in html or "加入購物車" in html) and not any(kw in html for kw in ["已售完", "售完補貨中"]):
                in_stock = True

            image_url = None
            img_meta = soup.find("meta", property="og:image")
            if img_meta and img_meta.get("content"):
                image_url = img_meta.get("content")

            return ProductInfo(
                url=url,
                platform_name=self.name,
                title=title or f"戰鬥陀螺X (Momo i_code: {icode})",
                price=price,
                status=StockStatus.IN_STOCK if in_stock else StockStatus.OUT_OF_STOCK,
                image_url=image_url,
                direct_buy_url=clean_buy_url
            )

        except Exception as e:
            logger.error(f"[Momo] 抓取失敗 ({url}): {e}")
            return ProductInfo(
                url=url,
                platform_name=self.name,
                title="Momo 購物網商品",
                status=StockStatus.ERROR,
                direct_buy_url=clean_buy_url,
                error_msg=str(e)
            )
