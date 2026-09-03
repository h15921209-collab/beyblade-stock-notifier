import random
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import requests

class StockStatus(str, Enum):
    IN_STOCK = "IN_STOCK"          # 有現貨 / 可購買
    OUT_OF_STOCK = "OUT_OF_STOCK"  # 缺貨 / 售完 / 補貨中
    UNKNOWN = "UNKNOWN"            # 無法判斷
    ERROR = "ERROR"                # 連線異常或頁面解析失敗

@dataclass
class ProductInfo:
    url: str
    platform_name: str
    title: str
    price: Optional[float] = None
    status: StockStatus = StockStatus.UNKNOWN
    stock_qty: Optional[int] = None
    image_url: Optional[str] = None
    direct_buy_url: str = ""
    error_msg: Optional[str] = None

    def __post_init__(self):
        if not self.direct_buy_url:
            self.direct_buy_url = self.url

class BaseScraper:
    name: str = "Base"
    
    # 常用瀏覽器 User-Agent 池，模擬真實瀏覽行為
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    ]

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()

    def get_headers(self, extra: Optional[dict] = None) -> dict:
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        if extra:
            headers.update(extra)
        return headers

    def can_handle(self, url: str) -> bool:
        """判斷本 Scraper 是否能處理該商品網址"""
        raise NotImplementedError

    def check_stock(self, url: str, custom_config: Optional[dict] = None) -> ProductInfo:
        """抓取並解析商品庫存狀態"""
        raise NotImplementedError
