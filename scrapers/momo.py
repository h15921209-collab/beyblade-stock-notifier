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

        try:
            # Momo 桌面版採用 Next.js SSR，速度快且不易觸發行動版 Akamai 挑戰驗證
            headers = self.get_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Referer": "https://www.momoshop.com.tw/",
                "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            })
            resp = self.session.get(clean_buy_url, headers=headers, timeout=self.timeout)
            
            # 若 404 或下架
            if resp.status_code == 404:
                return ProductInfo(
                    url=url,
                    platform_name=self.name,
                    title=f"Momo 商品已下架 (i_code: {icode})",
                    status=StockStatus.OUT_OF_STOCK,
                    direct_buy_url=clean_buy_url
                )

            resp.raise_for_status()
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            # 0. 檢查下架/無展售訊息
            if "商品目前無展售" in html or "網頁不存在" in html or "Mobile管理訊息" in html:
                return ProductInfo(
                    url=url,
                    platform_name=self.name,
                    title=f"Momo 商品無展售/已下架 (i_code: {icode})",
                    status=StockStatus.OUT_OF_STOCK,
                    direct_buy_url=clean_buy_url
                )

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
                price_match = re.search(r'["\'](?:salePrice|specialPrice|goodsPrice|price)["\']\s*:\s*["\']?(\d+)["\']?', html)
                if price_match:
                    price = float(price_match.group(1))

            # 3. 檢查是否遇到防爬蟲驗證頁面 (Challenge Validation)
            if "Challenge Validation" in html or (title and "Challenge Validation" in title):
                logger.warning(f"[Momo] 遇到防爬蟲驗證頁面 ({url})")
                return ProductInfo(
                    url=url,
                    platform_name=self.name,
                    title="Momo 購物網 (觸發驗證頁面)",
                    status=StockStatus.UNKNOWN,
                    direct_buy_url=clean_buy_url,
                    error_msg="Momo anti-bot challenge validation triggered"
                )

            # 4. 判斷庫存 (優先從 Next.js 結構化欄位判斷)
            in_stock = False

            # (A) 檢查 Next.js 串流資料內的 goodsStock
            stock_match = re.search(r'["\']goodsStock["\']\s*:\s*["\']?(\d+)["\']?', html)
            if stock_match:
                goods_stock = int(stock_match.group(1))
                in_stock = goods_stock > 0
            else:
                # (B) 檢查 Schema.org availability
                schema_match = re.search(r'["\'](?:availability|content)["\']\s*:\s*["\'](?:https?://schema.org/)?(InStock|OutOfStock|in stock|out of stock)["\']', html, re.I)
                if schema_match:
                    in_stock = "instock" in schema_match.group(1).lower()
                else:
                    # (C) 檢查頁面關鍵字特徵
                    out_of_stock_keywords = [
                        "已售完", "補貨中", "完售", "售完補貨中", "暫時下架", "此商品已下架", "下架", "商品已無庫存"
                    ]
                    in_stock = True
                    for kw in out_of_stock_keywords:
                        if kw in html:
                            in_stock = False
                            break

                    if not in_stock and any(btn_kw in html for btn_kw in ["直接購買", "加入購物車", "立即購買"]):
                        if not any(sold_kw in html for sold_kw in ["已售完", "售完補貨中"]):
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
