import logging
from typing import List, Optional, Type
from .base import BaseScraper, ProductInfo, StockStatus
from .funbox import FunboxScraper
from .pchome import PChomeScraper
from .toysrus import ToysrusScraper
from .momo import MomoScraper
from .shopee import ShopeeFunboxScraper
from .kubi import KubiScraper
from .eslite import EsliteScraper

logger = logging.getLogger(__name__)

class ScraperDispatcher:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.scrapers: List[BaseScraper] = [
            FunboxScraper(timeout=timeout),
            PChomeScraper(timeout=timeout),
            ToysrusScraper(timeout=timeout),
            MomoScraper(timeout=timeout),
            ShopeeFunboxScraper(timeout=timeout),
            KubiScraper(timeout=timeout),
            EsliteScraper(timeout=timeout),
        ]

    def get_scraper(self, url: str) -> Optional[BaseScraper]:
        for scraper in self.scrapers:
            if scraper.can_handle(url):
                return scraper
        return None

    def check(self, target: dict) -> ProductInfo:
        url = target.get("url", "").strip()
        if not url:
            return ProductInfo(
                url="",
                platform_name="未知",
                title="網址為空",
                status=StockStatus.ERROR,
                error_msg="Target URL is empty"
            )

        scraper = self.get_scraper(url)
        if not scraper:
            logger.warning(f"找不到對應的 Scraper 適配器: {url}")
            return ProductInfo(
                url=url,
                platform_name="未支援平台",
                title="未支援的網址格式",
                status=StockStatus.UNKNOWN,
                error_msg=f"尚未支援該平台網址: {url}"
            )

        # 執行庫存檢查
        info = scraper.check_stock(url, custom_config=target)

        # 覆寫自訂名稱或自訂價格限制
        custom_name = target.get("name")
        if custom_name:
            info.title = f"[{custom_name}] {info.title}"

        return info
