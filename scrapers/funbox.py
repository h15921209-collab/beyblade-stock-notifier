import re
import logging
from typing import Optional
from .base import BaseScraper, ProductInfo, StockStatus

logger = logging.getLogger(__name__)

class FunboxScraper(BaseScraper):
    name = "麗嬰國際官方購物網"

    def can_handle(self, url: str) -> bool:
        return "shop.funbox.com.tw" in url.lower() or "funbox.com.tw" in url.lower()

    def check_stock(self, url: str, custom_config: Optional[dict] = None) -> ProductInfo:
        # 提取商品 handle (例如 /products/tm07984)
        match = re.search(r'/products/([a-zA-Z0-9_\-]+)', url)
        if not match:
            # 支援若直接傳入 handle
            handle = url.strip().split('/')[-1].replace('.json', '')
        else:
            handle = match.group(1)

        api_url = f"https://shop.funbox.com.tw/products/{handle}.json"
        clean_buy_url = f"https://shop.funbox.com.tw/products/{handle}"

        try:
            resp = self.session.get(
                api_url,
                headers=self.get_headers({"Accept": "application/json"}),
                timeout=self.timeout
            )
            if resp.status_code == 404:
                return ProductInfo(
                    url=url,
                    platform_name=self.name,
                    title="商品未上架或已下架",
                    status=StockStatus.OUT_OF_STOCK,
                    direct_buy_url=clean_buy_url,
                    error_msg="404 Not Found"
                )

            resp.raise_for_status()
            data = resp.json()

            title = data.get("title", "戰鬥陀螺X商品 (麗嬰國際)")
            price = data.get("price")
            if price is not None:
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    price = None

            # 判斷庫存
            is_available = bool(data.get("available", False))
            
            # 若有 variants，檢查是否有任一規格可買
            variants = data.get("variants", [])
            has_variant_stock = False
            for v in variants:
                if v.get("available") is True:
                    has_variant_stock = True
                    break

            final_in_stock = is_available or has_variant_stock

            # 圖片
            image_url = data.get("featured_image")
            if not image_url:
                photos = data.get("photos", [])
                if photos:
                    image_url = photos[0]

            return ProductInfo(
                url=url,
                platform_name=self.name,
                title=title,
                price=price,
                status=StockStatus.IN_STOCK if final_in_stock else StockStatus.OUT_OF_STOCK,
                image_url=image_url,
                direct_buy_url=clean_buy_url
            )

        except Exception as e:
            logger.error(f"[Funbox] 抓取失敗 ({url}): {e}")
            return ProductInfo(
                url=url,
                platform_name=self.name,
                title="麗嬰國際商品",
                status=StockStatus.ERROR,
                direct_buy_url=clean_buy_url,
                error_msg=str(e)
            )
