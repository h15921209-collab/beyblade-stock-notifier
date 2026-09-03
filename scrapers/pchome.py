import re
import json
import logging
from typing import Optional
from .base import BaseScraper, ProductInfo, StockStatus

logger = logging.getLogger(__name__)

class PChomeScraper(BaseScraper):
    name = "PChome 24h 購物"

    def can_handle(self, url: str) -> bool:
        return "pchome.com.tw" in url.lower()

    def _extract_prod_id(self, url: str) -> Optional[str]:
        # 例如 https://24h.pchome.com.tw/prod/DEASR1-B900H2BID
        match = re.search(r'/prod/([a-zA-Z0-9_\-]+)', url)
        if match:
            return match.group(1)
        # 支援直接傳入商品編號
        if re.match(r'^[a-zA-Z0-9_\-]+$', url.strip()):
            return url.strip()
        return None

    def check_stock(self, url: str, custom_config: Optional[dict] = None) -> ProductInfo:
        prod_id = self._extract_prod_id(url)
        if not prod_id:
            return ProductInfo(
                url=url,
                platform_name=self.name,
                title="無效的 PChome 網址",
                status=StockStatus.ERROR,
                error_msg="無法從網址解析商品編號 (Prod ID)"
            )

        clean_buy_url = f"https://24h.pchome.com.tw/prod/{prod_id}"
        api_url = f"https://ecapi.pchome.com.tw/ecshop/prodapi/v2/prod/{prod_id}&fields=Name,Price,Qty,Store&_callback=jsonp_prod"

        try:
            resp = self.session.get(
                api_url,
                headers=self.get_headers({
                    "Referer": "https://24h.pchome.com.tw/",
                    "Accept": "*/*"
                }),
                timeout=self.timeout
            )
            resp.raise_for_status()
            text = resp.text

            # 解析 JSONP: try{jsonp_prod({...});}catch(e)...
            match = re.search(r'jsonp_prod\((.*?)\);', text)
            if not match:
                return ProductInfo(
                    url=url,
                    platform_name=self.name,
                    title=f"PChome 商品 ({prod_id})",
                    status=StockStatus.OUT_OF_STOCK,
                    direct_buy_url=clean_buy_url,
                    error_msg="無法取得商品 JSONP 資料（可能已售完下架）"
                )

            data = json.loads(match.group(1))
            # 回傳格式為 key: {DEASR1-B900H2BID-000: {...}}
            prod_info = None
            for k, v in data.items():
                if isinstance(v, dict):
                    prod_info = v
                    break

            if not prod_info:
                return ProductInfo(
                    url=url,
                    platform_name=self.name,
                    title="PChome 商品",
                    status=StockStatus.OUT_OF_STOCK,
                    direct_buy_url=clean_buy_url
                )

            title = prod_info.get("Name", "戰鬥陀螺X商品 (PChome 24h)")
            
            # 價格解析
            price = None
            price_obj = prod_info.get("Price", {})
            if isinstance(price_obj, dict):
                price = price_obj.get("P") or price_obj.get("M")
            elif isinstance(price_obj, (int, float)):
                price = float(price_obj)

            # 庫存數量
            qty = prod_info.get("Qty", 0)
            try:
                qty = int(qty)
            except (ValueError, TypeError):
                qty = 0

            in_stock = qty > 0

            return ProductInfo(
                url=url,
                platform_name=self.name,
                title=title,
                price=float(price) if price is not None else None,
                status=StockStatus.IN_STOCK if in_stock else StockStatus.OUT_OF_STOCK,
                stock_qty=qty if in_stock else 0,
                direct_buy_url=clean_buy_url
            )

        except Exception as e:
            logger.error(f"[PChome] 抓取失敗 ({url}): {e}")
            return ProductInfo(
                url=url,
                platform_name=self.name,
                title="PChome 24h 商品",
                status=StockStatus.ERROR,
                direct_buy_url=clean_buy_url,
                error_msg=str(e)
            )
