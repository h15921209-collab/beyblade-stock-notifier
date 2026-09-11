import re
import urllib.parse
import logging
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

from scrapers.base import ProductInfo, StockStatus
from scrapers.pchome import PChomeScraper
from scrapers.momo import MomoScraper
from scrapers.toysrus import ToysrusScraper
from scrapers.funbox import FunboxScraper
from core.msrp import get_official_price_and_limit
from core.smart_finder import is_authentic_beyblade_product

logger = logging.getLogger("DynamicScanner")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}

def scan_pchome_dynamic(limit: int = 30) -> List[ProductInfo]:
    """
    動態掃蕩 PChome 24h 官方專區最新上架商品
    直接過濾正版戰鬥陀螺且售價 <= MSRP 原價上限
    """
    results = []
    seen_urls = set()
    scraper = PChomeScraper(timeout=8)
    queries = ["BEYBLADE", "戰鬥陀螺X", "戰鬥陀螺 UX", "戰鬥陀螺 BX"]

    for q in queries:
        if len(results) >= limit:
            break
        url = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={urllib.parse.quote(q)}&page=1&sort=sale/dc"
        try:
            r = requests.get(url, headers=HEADERS, timeout=6)
            if r.status_code != 200:
                continue
            data = r.json()
            prods = data.get("prods", [])
            for p in prods:
                if len(results) >= limit:
                    break
                pid = p.get("Id")
                name = p.get("name", "")
                price = float(p.get("price", 0))
                prod_url = f"https://24h.pchome.com.tw/prod/{pid}"

                if not pid or prod_url in seen_urls:
                    continue

                # 1. 三重鋼鐵過濾機制
                if not is_authentic_beyblade_product(name):
                    continue

                # 2. 官方原價上限檢驗 (MSRP Guard)
                off_p, max_p = get_official_price_and_limit(name, fallback_price=price)
                if price <= 0 or price > max_p:
                    logger.debug(f"[PChome動態] 價格 NT${price} 超過原價上限 NT${max_p}，排除: {name}")
                    continue

                seen_urls.add(prod_url)

                # 3. 快速驗證庫存
                try:
                    info = scraper.check_stock(prod_url)
                    if info.status == StockStatus.IN_STOCK:
                        results.append(info)
                except Exception as e:
                    logger.debug(f"[PChome動態] 庫存驗證失敗 ({prod_url}): {e}")

        except Exception as e:
            logger.warning(f"[PChome動態] 掃蕩查詢 {q} 異常: {e}")

    logger.info(f"⚡ PChome 24h 動態掃蕩完成，捕獲 {len(results)} 款原價現貨！")
    return results

def scan_momo_dynamic(limit: int = 30) -> List[ProductInfo]:
    """
    動態掃蕩 Momo 購物網官方正版專區最新上架商品
    直接過濾正版戰鬥陀螺且售價 <= MSRP 原價上限
    """
    results = []
    seen_urls = set()
    scraper = MomoScraper(timeout=8)
    queries = ["TAKARA TOMY 戰鬥陀螺", "戰鬥陀螺X", "戰鬥陀螺 UX", "戰鬥陀螺 BX"]

    for q in queries:
        if len(results) >= limit:
            break
        url = f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={urllib.parse.quote(q)}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=6)
            if r.status_code != 200:
                continue

            pushes = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', r.text, re.DOTALL)
            joined = "".join(pushes)

            pattern = re.compile(
                r'\\"goodsCode\\":\\"(\d+)\\",\\"goodsName\\":\\"([^"\\]+)\\"',
                re.DOTALL
            )
            for match in pattern.finditer(joined):
                if len(results) >= limit:
                    break
                gcode = match.group(1)
                raw_name = match.group(2)
                name = raw_name.encode('utf-8').decode('unicode_escape', errors='ignore') if '\\u' in raw_name else raw_name

                # 擷取商品價格
                start = match.start()
                snippet = joined[start:start + 400]
                price_m = re.search(r'\\"goodsPrice\\":\\"([^\"]+)\\"', snippet)
                raw_price = price_m.group(1) if price_m else "0"
                price_digits = re.sub(r'[^\d]', '', raw_price)
                price = float(price_digits) if price_digits else 0

                prod_url = f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={gcode}"
                if not gcode or prod_url in seen_urls:
                    continue

                # 1. 三重鋼鐵過濾機制
                if not is_authentic_beyblade_product(name):
                    continue

                # 2. 官方原價上限檢驗 (MSRP Guard)
                off_p, max_p = get_official_price_and_limit(name, fallback_price=price if price > 0 else 9999)
                if price <= 0 or price > max_p:
                    logger.debug(f"[Momo動態] 價格 NT${price} 超過原價上限 NT${max_p}，排除: {name}")
                    continue

                seen_urls.add(prod_url)

                # 3. 驗證現貨狀態 (透過 MomoScraper)
                try:
                    info = scraper.check_stock(prod_url)
                    if info.status == StockStatus.IN_STOCK:
                        results.append(info)
                except Exception as e:
                    logger.debug(f"[Momo動態] 庫存驗證失敗 ({prod_url}): {e}")

        except Exception as e:
            logger.warning(f"[Momo動態] 掃蕩查詢 {q} 異常: {e}")

    logger.info(f"⚡ Momo 購物網動態掃蕩完成，捕獲 {len(results)} 款原價現貨！")
    return results

def scan_toysrus_dynamic(limit: int = 30) -> List[ProductInfo]:
    """
    動態掃蕩玩具反斗城台灣官網
    """
    results = []
    seen_urls = set()
    scraper = ToysrusScraper(timeout=8)
    url = "https://www.toysrus.com.tw/search?q=BEYBLADE"

    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                if len(results) >= limit:
                    break
                href = a["href"]
                if ".html" in href and "search" not in href:
                    title = a.text.strip()
                    full_url = href if href.startswith("http") else f"https://www.toysrus.com.tw{href}"
                    if not title or len(title) < 5 or full_url in seen_urls:
                        continue

                    # 1. 三重鋼鐵過濾
                    if not is_authentic_beyblade_product(title):
                        continue

                    seen_urls.add(full_url)

                    # 2. 庫存與價格檢驗
                    try:
                        info = scraper.check_stock(full_url)
                        if info.status == StockStatus.IN_STOCK:
                            off_p, max_p = get_official_price_and_limit(title, fallback_price=info.price or 1500)
                            if info.price is None or info.price <= max_p:
                                results.append(info)
                    except Exception as e:
                        logger.debug(f"[玩具反斗城動態] 檢查失敗 ({full_url}): {e}")

    except Exception as e:
        logger.warning(f"[玩具反斗城動態] 掃蕩異常: {e}")

    logger.info(f"⚡ 玩具反斗城動態掃蕩完成，捕獲 {len(results)} 款原價現貨！")
    return results

def scan_funbox_dynamic(limit: int = 30) -> List[ProductInfo]:
    """
    動態掃蕩麗嬰國際官方商城 (台灣總代理)
    """
    results = []
    seen_urls = set()
    scraper = FunboxScraper(timeout=8)
    url = "https://shop.funbox.com.tw/products?query=%E6%88%B0%E9%AC%A5%E9%99%80%E8%9E%BA"

    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                if len(results) >= limit:
                    break
                href = a["href"]
                if "/products/" in href and not href.endswith("/products"):
                    clean_path = href.split("?")[0]
                    full_url = f"https://shop.funbox.com.tw{clean_path}" if clean_path.startswith("/") else clean_path
                    title = a.text.strip()
                    if not title or len(title) < 5 or full_url in seen_urls:
                        continue

                    # 1. 三重鋼鐵過濾
                    if not is_authentic_beyblade_product(title):
                        continue

                    seen_urls.add(full_url)

                    # 2. 庫存與價格檢驗
                    try:
                        info = scraper.check_stock(full_url)
                        if info.status == StockStatus.IN_STOCK:
                            off_p, max_p = get_official_price_and_limit(title, fallback_price=info.price or 1500)
                            if info.price is None or info.price <= max_p:
                                results.append(info)
                    except Exception as e:
                        logger.debug(f"[麗嬰國際動態] 檢查失敗 ({full_url}): {e}")

    except Exception as e:
        logger.warning(f"[麗嬰國際動態] 掃蕩異常: {e}")

    logger.info(f"⚡ 麗嬰國際動態掃蕩完成，捕獲 {len(results)} 款原價現貨！")
    return results

def scan_all_dynamic_channels(limit_per_channel: int = 30) -> List[ProductInfo]:
    """
    動態無名單即時捕獲器：
    每輪掃蕩四大官方授權專區（PChome 24h、Momo 購物網、玩具反斗城、麗嬰國際）
    自動套用「三重鋼鐵過濾」與「MSRP 原價守門」，回傳所有符合資格的原價現貨！
    """
    logger.info("🚀 啟動全網動態無名單即時捕獲掃蕩...")
    all_in_stock = []
    seen_urls = set()

    # 依序掃描四大官方通路
    channels = [
        ("PChome 24h", scan_pchome_dynamic),
        ("Momo 購物網", scan_momo_dynamic),
        ("玩具反斗城", scan_toysrus_dynamic),
        ("麗嬰國際", scan_funbox_dynamic),
    ]

    for name, scan_func in channels:
        try:
            items = scan_func(limit=limit_per_channel)
            for item in items:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    all_in_stock.append(item)
        except Exception as e:
            logger.error(f"[{name}] 動態掃描失敗: {e}")

    logger.info(f"🎉 全網動態掃蕩完成！共捕獲 {len(all_in_stock)} 款官方原價現貨！")
    return all_in_stock
