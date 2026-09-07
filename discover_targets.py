import os
import re
import json
import logging
import requests
import yaml
from bs4 import BeautifulSoup
from scrapers import PChomeScraper, ToysrusScraper, FunboxScraper
from core.msrp import get_official_price_and_limit
from core.smart_finder import is_authentic_beyblade_product

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AutoDiscover")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}

def search_pchome_beyblade() -> list:
    """從 PChome 24h 官方授權專區自動搜尋戰鬥陀螺X系列商品"""
    logger.info("正在掃描 PChome 24h 官方戰鬥陀螺X全系列商品...")
    found = []
    queries = ["BEYBLADE", "戰鬥陀螺X", "戰鬥陀螺 BX", "戰鬥陀螺 UX"]
    seen_ids = set()

    for q in queries:
        url = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={q}&page=1&sort=sale/dc"
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            if r.status_code == 200:
                data = r.json()
                for p in data.get("prods", []):
                    pid = p.get("Id")
                    name = p.get("name", "")
                    price = p.get("price", 0)
                    
                    # 篩選戰鬥陀螺相關商品（三重鋼鐵過濾機制）
                    if pid and pid not in seen_ids:
                        if is_authentic_beyblade_product(name):
                            seen_ids.add(pid)
                            prod_url = f"https://24h.pchome.com.tw/prod/{pid}"
                            _, max_p = get_official_price_and_limit(name, fallback_price=price)
                            found.append({
                                "name": name,
                                "url": prod_url,
                                "max_price": max_p,
                                "enabled": True
                            })
        except Exception as e:
            logger.warning(f"PChome 搜尋 {q} 異常: {e}")

    logger.info(f"PChome 24h 共發現 {len(found)} 款正版戰鬥陀螺X商品！")
    return found

def search_toysrus_beyblade() -> list:
    """從玩具反斗城台灣官網搜尋戰鬥陀螺X商品"""
    logger.info("正在掃描玩具反斗城台灣官網全系列商品...")
    found = []
    seen_urls = set()
    url = "https://www.toysrus.com.tw/search?q=BEYBLADE"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if ".html" in href and any(k in href.lower() for k in ["beyblade", "bx-", "ux-"]):
                    full_url = href if href.startswith("http") else f"https://www.toysrus.com.tw{href}"
                    title = a.text.strip() or "玩具反斗城 戰鬥陀螺X商品"
                    if full_url not in seen_urls and is_authentic_beyblade_product(title):
                        seen_urls.add(full_url)
                        _, max_p = get_official_price_and_limit(title, fallback_price=1500)
                        found.append({
                            "name": title,
                            "url": full_url,
                            "max_price": max_p,
                            "enabled": True
                        })
    except Exception as e:
        logger.warning(f"玩具反斗城搜尋異常: {e}")

    logger.info(f"玩具反斗城共發現 {len(found)} 款戰鬥陀螺X商品！")
    return found

def search_funbox_beyblade() -> list:
    """從麗嬰國際官方購物網搜尋商品"""
    logger.info("正在掃描麗嬰國際官方商城戰鬥陀螺專區...")
    found = []
    seen_urls = set()
    url = "https://shop.funbox.com.tw/products?query=%E6%88%B0%E9%AC%A5%E9%99%80%E8%9E%BA"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/products/" in href and not href.endswith("/products"):
                    clean_path = href.split("?")[0]
                    full_url = f"https://shop.funbox.com.tw{clean_path}" if clean_path.startswith("/") else clean_path
                    title = a.text.strip() or "麗嬰國際 戰鬥陀螺X"
                    if full_url not in seen_urls and is_authentic_beyblade_product(title):
                        seen_urls.add(full_url)
                        _, max_p = get_official_price_and_limit(title, fallback_price=1500)
                        found.append({
                            "name": title,
                            "url": full_url,
                            "max_price": max_p,
                            "enabled": True
                        })
    except Exception as e:
        logger.warning(f"麗嬰國際官網搜尋異常: {e}")

    logger.info(f"麗嬰國際官網共發現 {len(found)} 款商品！")
    return found

def update_config_with_discovered(discovered: list, config_file: str = "config.yaml"):
    """將發現的商品去重並合併寫入 config.yaml"""
    if not os.path.exists(config_file):
        if os.path.exists("config.example.yaml"):
            with open("config.example.yaml", "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        else:
            cfg = {"targets": []}
    else:
        with open(config_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

    existing_targets = cfg.get("targets", [])
    existing_urls = {t.get("url", "").strip() for t in existing_targets}

    added_count = 0
    for item in discovered:
        url = item.get("url", "").strip()
        if url and url not in existing_urls:
            existing_targets.append(item)
            existing_urls.add(url)
            added_count += 1

    cfg["targets"] = existing_targets

    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    logger.info(f"✅ 成功將 {added_count} 款新發現的正版戰鬥陀螺X商品寫入 {config_file}！(目前總計監控: {len(existing_targets)} 款)")
    return added_count, len(existing_targets)

def run_discovery():
    all_discovered = []
    all_discovered.extend(search_pchome_beyblade())
    all_discovered.extend(search_toysrus_beyblade())
    all_discovered.extend(search_funbox_beyblade())
    added, total = update_config_with_discovered(all_discovered)
    return added, total

if __name__ == "__main__":
    run_discovery()
