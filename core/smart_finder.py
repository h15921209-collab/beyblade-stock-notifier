import re
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from core.msrp import get_official_price_and_limit

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# 官方授權正版白名單網域
OFFICIAL_DOMAINS = {
    "shop.funbox.com.tw": "麗嬰國際官方商城 (台灣總代理直營)",
    "24h.pchome.com.tw": "PChome 24h 購物 (官方正版直營)",
    "toysrus.com.tw": "玩具反斗城 (台灣官方直營)",
    "www.toysrus.com.tw": "玩具反斗城 (台灣官方直營)",
    "momo.com.tw": "Momo 購物網 (官方正版授權直營)",
    "www.momo.com.tw": "Momo 購物網 (官方正版授權直營)",
    "shopee.tw": "蝦皮商城 (麗嬰國際官方旗艦館)",
    "kble.tw": "酷比樂玩具 (正版授權專門店)",
    "www.kble.tw": "酷比樂玩具 (正版授權專門店)",
    "eslite.com": "誠品線上 (正版圖書玩具)",
    "www.eslite.com": "誠品線上 (正版圖書玩具)",
}

# 玩家論壇與社群熱門爆款精選清單
HOT_PICKS = {
    "🏆 論壇社群神物款": [
        {"model": "UX-03", "name": "魔導神杖 (Wizard Rod 5-70DB)", "desc": "社群公認比賽常勝 T0 軸心神物", "official_price": 550},
        {"model": "BX-35", "name": "隨機強化組Vol.4 (黑鳳凰羽翼 Black Shell)", "desc": "論壇最難抽之防禦爆款", "official_price": 399},
        {"model": "BX-23", "name": "鳳凰飛翼 (Phoenix Wing 9-60GF)", "desc": "重擊流金屬塗裝頂級攻擊陀螺", "official_price": 399},
        {"model": "UX-04", "name": "戰鬥白龍入門組 (Aero Pegasus/Dran Dagger)", "desc": "超人氣強勢聯名款式", "official_price": 550},
    ],
    "🔥 UX 最新獨特系列": [
        {"model": "UX-08", "name": "白銀神狼 (Silver Wolf 3-80FB)", "desc": "附自由回轉機構之持久型新王者", "official_price": 550},
        {"model": "UX-09", "name": "幽靈武士 (Ghost Circle 0-80GB)", "desc": "圓形金屬環極限離心力", "official_price": 550},
        {"model": "UX-10", "name": "騎士神劍 (Knight Mail 3-85BS)", "desc": "重裝甲衝擊防禦新型態", "official_price": 550},
        {"model": "UX-01", "name": "德蘭巨劍 (Dran Buster 1-60A)", "desc": "一擊必殺單點重衝擊", "official_price": 550},
        {"model": "UX-02", "name": "地獄炎鐮 (Hells Hammer 3-70H)", "desc": "平衡型下壓重擊型戰鬥陀螺", "official_price": 550},
    ],
    "🌀 BX 強勢主力款": [
        {"model": "BX-36", "name": "鯨魚浪潮 (Whale Wave 5-80E)", "desc": "最新大重量波浪形攻擊刃", "official_price": 399},
        {"model": "BX-34", "name": "鈷藍巨龍 (Cobalt Dragoon 2-60C)", "desc": "左迴旋強勢攻擊型陀螺", "official_price": 399},
        {"model": "BX-33", "name": "衝擊猛擊白虎 (Weiss Tiger 3-60U)", "desc": "高機動彈射爆擊型", "official_price": 399},
        {"model": "BX-31", "name": "隨機強化組Vol.3 (暴龍打擊/提爾風)", "desc": "強勢配件大集合", "official_price": 399},
        {"model": "BX-24", "name": "隨機強化組Vol.2 (雙足翼龍)", "desc": "超搶手罕見雙刀刃款", "official_price": 399},
    ],
    "🎁 限定紀念與對戰配件": [
        {"model": "BX-25", "name": "戰鬥陀螺X 專業收納手提包", "desc": "全台常態缺貨手提箱神物", "official_price": 1199},
        {"model": "BX-37", "name": "雙重極限衝擊戰鬥盤豪華組", "desc": "雙軌道超加速對戰套裝", "official_price": 1498},
        {"model": "BX-07", "name": "極限對戰盤 (單盤)", "desc": "標準 X 賽事必備加速齒輪盤", "official_price": 750},
        {"model": "BXG-01", "name": "復刻紀念款 烈焰飛鳳S", "desc": "初代爆轉陀螺經典復刻限定版", "official_price": 750},
        {"model": "BXG-04", "name": "復刻紀念款 銀牙烈虎S", "desc": "初代爆轉白虎復刻限定版", "official_price": 750},
        {"model": "BXG-47", "name": "復刻限定 暴風天馬3 (BX00)", "desc": "鋼鐵奇兵情懷天馬復刻版", "official_price": 999},
    ]
}

def sanitize_url(raw_url: str) -> str:
    """去除冗餘追蹤碼與參數，還原乾淨標準網址"""
    raw_url = raw_url.strip()
    parsed = urllib.parse.urlparse(raw_url)
    clean_params = []
    if parsed.query:
        # 去除常見垃圾追蹤碼
        bad_keys = {"fbclid", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "spm", "igshid", "gclid", "ref"}
        queries = urllib.parse.parse_qsl(parsed.query)
        clean_params = [(k, v) for k, v in queries if k.lower() not in bad_keys and not k.startswith("utm_")]

    new_query = urllib.parse.urlencode(clean_params)
    clean_url = urllib.parse.urlunparse((parsed.scheme or "https", parsed.netloc, parsed.path, parsed.params, new_query, ""))
    return clean_url

def verify_official_channel(url: str) -> Tuple[bool, str]:
    """檢驗賣場網址是否為官方授權直營正版白名單"""
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    for official_dom, desc in OFFICIAL_DOMAINS.items():
        if domain == official_dom or domain.endswith("." + official_dom):
            return True, desc
    return False, "⚠️ 非官方直營白名單（注意：可能為第三方個人賣家或未授權店家）"

def search_pchome_official(keyword: str) -> List[Dict[str, Any]]:
    """從 PChome 24h 官方直營精準搜尋型號商品"""
    results = []
    url = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={urllib.parse.quote(keyword)}&page=1&sort=rnk/dc"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            data = r.json()
            for p in data.get("prods", [])[:6]:
                pid = p.get("Id")
                name = p.get("name", "")
                price = p.get("price", 0)
                # 嚴格確認為陀螺相關且包含關鍵字
                if pid and ("BX" in name.upper() or "UX" in name.upper() or "陀螺" in name or "BEYBLADE" in name.upper()):
                    prod_url = f"https://24h.pchome.com.tw/prod/{pid}"
                    off_p, max_p = get_official_price_and_limit(name, fallback_price=price)
                    results.append({
                        "platform": "PChome 24h",
                        "badge": "PChome官方直營",
                        "name": name,
                        "url": prod_url,
                        "current_price": price,
                        "official_price": off_p,
                        "max_price": max_p,
                        "is_overpriced": price > max_p if price > 0 else False
                    })
    except Exception:
        pass
    return results

def search_toysrus_official(keyword: str) -> List[Dict[str, Any]]:
    """從玩具反斗城台灣官網精準搜尋型號商品"""
    results = []
    url = f"https://www.toysrus.com.tw/search?q={urllib.parse.quote(keyword)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            seen = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if ".html" in href and "search" not in href:
                    title = a.text.strip()
                    if title and keyword.upper() in title.upper() and len(title) > 5:
                        full_url = href if href.startswith("http") else f"https://www.toysrus.com.tw{href}"
                        if full_url not in seen:
                            seen.add(full_url)
                            off_p, max_p = get_official_price_and_limit(title)
                            results.append({
                                "platform": "玩具反斗城",
                                "badge": "反斗城官方直營",
                                "name": title,
                                "url": full_url,
                                "current_price": off_p,
                                "official_price": off_p,
                                "max_price": max_p,
                                "is_overpriced": False
                            })
    except Exception:
        pass
    return results

def search_funbox_official(keyword: str) -> List[Dict[str, Any]]:
    """從麗嬰國際官方旗艦網精準搜尋"""
    results = []
    url = f"https://shop.funbox.com.tw/products?query={urllib.parse.quote(keyword)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            seen = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/products/" in href and not href.endswith("/products"):
                    clean_path = href.split("?")[0]
                    title = a.text.strip()
                    if title and keyword.upper() in title.upper() and len(title) > 5:
                        full_url = f"https://shop.funbox.com.tw{clean_path}" if clean_path.startswith("/") else clean_path
                        if full_url not in seen:
                            seen.add(full_url)
                            off_p, max_p = get_official_price_and_limit(title)
                            results.append({
                                "platform": "麗嬰國際",
                                "badge": "總代理官方商城",
                                "name": title,
                                "url": full_url,
                                "current_price": off_p,
                                "official_price": off_p,
                                "max_price": max_p,
                                "is_overpriced": False
                            })
    except Exception:
        pass
    return results

def smart_cross_search(keyword: str) -> List[Dict[str, Any]]:
    """跨各大官方授權通路聯播搜尋"""
    keyword = keyword.strip()
    if not keyword:
        return []

    combined = []
    seen_urls = set()

    # 平行檢索各大官方通路
    for func in [search_pchome_official, search_toysrus_official, search_funbox_official]:
        for item in func(keyword):
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                combined.append(item)

    return combined
