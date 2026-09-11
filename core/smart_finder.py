import re
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from core.msrp import get_official_price_and_limit
from core.meta_updater import load_hot_picks, update_hot_picks_from_sources

def get_current_hot_picks_data() -> Tuple[Dict[str, Any], str]:
    """取得當前熱門神物分類資料與最後更新時間"""
    data = load_hot_picks()
    if data and "categories" in data:
        return data["categories"], data.get("last_updated", "最新")
    # 若檔案不存在則現場更新一次
    updated = update_hot_picks_from_sources()
    return updated.get("categories", HOT_PICKS), updated.get("last_updated", "剛才")

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
        {"model": "BX-25", "name": "戰鬥陀螺X 專業收納手提包", "desc": "全台常態缺貨手提箱神物", "official_price": 850},
        {"model": "BX-37", "name": "雙重極限衝擊戰鬥盤豪華組", "desc": "雙軌道超加速對戰套裝", "official_price": 1498},
        {"model": "BX-07", "name": "極限激戰初始組 (含盤與天劍豪華組)", "desc": "標準 X 賽事必備加速齒輪套裝", "official_price": 1795},
        {"model": "BXG-01", "name": "復刻紀念款 烈焰飛鳳S", "desc": "初代爆轉陀螺經典復刻限定版", "official_price": 350},
        {"model": "BXG-04", "name": "復刻紀念款 銀牙烈虎S", "desc": "初代爆轉白虎復刻限定版", "official_price": 350},
        {"model": "BXG-47", "name": "復刻限定 暴風天馬3 (BX00)", "desc": "鋼鐵奇兵情懷天馬復刻版", "official_price": 999},
    ]
}

# ==============================================================================
# 【三重鋼鐵過濾機制 (Triple Steel Filter)】
# ==============================================================================

# 負面黑名單 (硬剔除：只要含有此名單中的詞彙，直接判定非戰鬥陀螺)
BLACKLIST_KEYWORDS = [
    # 鞋類與鞋周邊
    "鞋", "涼鞋", "拖鞋", "洞洞鞋", "運動鞋", "男鞋", "女鞋", "童鞋", "球鞋", "帆布鞋", "皮鞋",
    "clog", "crocs", "puma", "nike", "adidas",
    # 服裝與穿搭
    "衣服", "上衣", "長褲", "短褲", "牛仔褲", "外套", "t恤", "t-shirt", "背心", "洋裝", "裙", "襪", "帽子", "內衣", "內褲",
    # 首飾珠寶、化妝鏡面盒
    "首飾", "首飾盒", "收納鏡面", "珠寶", "飾品", "項鍊", "手鍊", "手環", "手鐲", "戒指", "耳環", "耳釘", "胸針", "吊墜", "化妝盒", "化妝箱", "珠寶盒", "美妝",
    # 3C電腦零件、電池、變壓器
    "變壓器", "充電器", "適配器", "充電線", "電源線", "電池", "華碩", "asus", "zenbook", "vivobook", "rog", "msi", "微星",
    "筆電", "筆記型電腦", "主機板", "記憶體", "散熱器", "耳機", "喇叭", "音響", "轉接器", "轉接頭", "保護貼", "手機殼", "保護套",
    "平板", "滑鼠", "鍵盤", "type-c", "usbc", "65w", "45w", "120w", "150w", "19v", "20v", "3.42a", "2.37a",
    "c31n", "c23-ux", "ux32", "ux305", "ux580", "ux390", "ux410", "ux5400", "ux3404", "rx32",
    # 家具生活用品與家電
    "椅凳", "凳子", "椅子", "桌子", "保溫杯", "水壺", "水杯", "浴巾", "毛巾", "床單", "枕頭", "沙發", "窗簾",
    "飛利浦", "philips", "氣炸鍋", "調理機", "豆漿機", "破壁機", "小廚神", "果汁機", "吸塵器", "吹風機", "抽獎", "抽ux"
]

# 正面授權品牌關鍵字
POSITIVE_BRAND_KEYWORDS = [
    "BEYBLADE", "戰鬥陀螺", "爆旋陀螺", "TAKARA TOMY", "TAKARATOMY", "麗嬰", "FUNBOX"
]

# 正面系列與部件特徵字（含主要系列標識與陀螺刃名）
POSITIVE_SERIES_KEYWORDS = [
    "X世代", "戰鬥盤", "對戰盤", "發射器", "發射握把", "握把配件", "極限激戰", "拉繩", "拉條",
    "隨機強化組", "盲包", "入門組", "入門套組", "改造組", "雙重極限", "陀螺", "豪華組", "對戰組",
    # 常見戰鬥陀螺專有名詞與精靈名稱
    "女武神", "武神", "龍騎士", "神杖", "炎鐮", "巨劍", "神劍", "神狼", "銀狼",
    "鳳凰飛翼", "鳳凰", "飛翼", "龍神", "蒼龍", "巨龍", "白虎", "天馬", "獅子",
    "獵爪", "鮫鯊", "狂鱗", "幽冥", "惡魔幽冥", "獅鷲", "獨角刺心", "刺心", "海妖",
    "鹿角", "黃蜂", "日輪", "地獄", "德蘭", "暴龍", "提爾風", "翼龍", "浪潮", "魔導"
]

def enrich_search_query(keyword: str) -> str:
    """
    第一重：搜尋詞自動擴增（Query Enrichment）
    若搜尋詞中未包含 BEYBLADE、戰鬥陀螺或陀螺，自動加掛 'BEYBLADE X '
    避免零售商搜尋引擎（如 PChome 24h）因型號代碼碰撞而跨足鞋類、3C 等雜物。
    """
    kw = keyword.strip()
    kw_upper = kw.upper()
    if "BEYBLADE" not in kw_upper and "戰鬥陀螺" not in kw and "陀螺" not in kw:
        return f"BEYBLADE X {kw}"
    return kw

def is_authentic_beyblade_product(title: str, target_keyword: Optional[str] = None) -> bool:
    """
    三重鋼鐵過濾機制核心檢驗：
    1. 負面黑名單：硬剔除任何鞋類、首飾、3C零件、家具雜物。
    2. 正面特徵檢驗：必須具備正版陀螺品牌（BEYBLADE/戰鬥陀螺/TAKARA TOMY等）或陀螺配件系列詞＋正規型號。
    3. 目標型號比對：若有指定 target_keyword（如 BX-07），確保商品名稱中型號絕對吻合，防止張冠李戴。
    """
    if not title or not isinstance(title, str):
        return False

    title_clean = title.strip()
    title_lower = title_clean.lower()
    title_upper = title_clean.upper()

    # 第一重：負面黑名單硬剔除 (Negative Blacklist)
    for bad_word in BLACKLIST_KEYWORDS:
        if bad_word.lower() in title_lower:
            return False

    # 第二重：正面特徵檢驗 (Positive Brand / Core Keywords)
    has_brand = any(brand.upper() in title_upper for brand in POSITIVE_BRAND_KEYWORDS)
    has_series = any(series in title_clean for series in POSITIVE_SERIES_KEYWORDS)

    # 檢查是否有合法的戰鬥陀螺代碼 (BX, UX, CX, BXG 等)，避免 206750-5BX 等偽代碼
    has_model_code = bool(re.search(r'(?<![A-Za-z0-9])(BX|UX|CX|BXG)[-_]?\d{1,3}(?![A-Za-z0-9])', title_upper))

    is_valid_beyblade = has_brand or (has_series and has_model_code)
    if not is_valid_beyblade:
        return False

    # 第三重：目標型號／關鍵字吻合度檢驗 (Target Model Matching)
    if target_keyword:
        kw = target_keyword.strip().upper()
        # 若 target_keyword 包含型號代碼（如 BX-07, UX-20）
        model_match = re.search(r'(?<![A-Za-z0-9])(BX|UX|CX|BXG)[-_]?(\d{1,3})(?![A-Za-z0-9])', kw)
        if model_match:
            prefix = model_match.group(1)
            num_str = model_match.group(2)
            num_int = int(num_str)
            # 必須精確符合該型號數字（允許 07 或 7，允許連字號或空格）
            pattern = rf'(?<![A-Za-z0-9]){prefix}[-_\s]?0?{num_int}(?![A-Za-z0-9])'
            if not re.search(pattern, title_upper):
                return False
        else:
            # 中文或其他關鍵字（如「魔導神杖」），品名必須包含關鍵字主要詞
            kw_clean = target_keyword.strip()
            if kw_clean not in title_clean:
                return False

    return True

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
    """從 PChome 24h 官方直營精準搜尋型號商品（自動加掛 BEYBLADE 前綴＋三重鋼鐵過濾）"""
    results = []
    enriched_kw = enrich_search_query(keyword)
    url = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={urllib.parse.quote(enriched_kw)}&page=1&sort=rnk/dc"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            data = r.json()
            for p in data.get("prods", [])[:10]:
                pid = p.get("Id")
                name = p.get("name", "")
                price = p.get("price", 0)
                # 三重鋼鐵過濾機制：嚴格驗證正版戰鬥陀螺且型號吻合
                if pid and is_authentic_beyblade_product(name, target_keyword=keyword):
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
    enriched_kw = enrich_search_query(keyword)
    url = f"https://www.toysrus.com.tw/search?q={urllib.parse.quote(enriched_kw)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            seen = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if ".html" in href and "search" not in href:
                    title = a.text.strip()
                    if title and is_authentic_beyblade_product(title, target_keyword=keyword) and len(title) > 5:
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
    enriched_kw = enrich_search_query(keyword)
    url = f"https://shop.funbox.com.tw/products?query={urllib.parse.quote(enriched_kw)}"
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
                    if title and is_authentic_beyblade_product(title, target_keyword=keyword) and len(title) > 5:
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

def search_momo_official(keyword: str) -> List[Dict[str, Any]]:
    """從 Momo 購物網官方正版授權通路精準搜尋型號商品"""
    results = []
    enriched_kw = enrich_search_query(keyword)
    url = f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={urllib.parse.quote(enriched_kw)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        if r.status_code == 200:
            pushes = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', r.text, re.DOTALL)
            joined = "".join(pushes)

            pattern = re.compile(
                r'\\"goodsCode\\":\\"(\d+)\\",\\"goodsName\\":\\"([^"\\]+)\\"',
                re.DOTALL
            )
            seen = set()
            for match in pattern.finditer(joined):
                gcode = match.group(1)
                raw_name = match.group(2)
                name = raw_name.encode('utf-8').decode('unicode_escape', errors='ignore') if '\\u' in raw_name else raw_name

                start = match.start()
                snippet = joined[start:start + 400]
                price_m = re.search(r'\\"goodsPrice\\":\\"([^\"]+)\\"', snippet)
                raw_price = price_m.group(1) if price_m else "0"
                price_digits = re.sub(r'[^\d]', '', raw_price)
                price = float(price_digits) if price_digits else 0

                if gcode and gcode not in seen and is_authentic_beyblade_product(name, target_keyword=keyword):
                    seen.add(gcode)
                    prod_url = f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={gcode}"
                    off_p, max_p = get_official_price_and_limit(name, fallback_price=price)
                    results.append({
                        "platform": "Momo 購物網",
                        "badge": "Momo官方直營",
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

def smart_cross_search(keyword: str) -> List[Dict[str, Any]]:
    """跨各大官方授權通路聯播搜尋"""
    keyword = keyword.strip()
    if not keyword:
        return []

    combined = []
    seen_urls = set()

    # 平行檢索各大官方通路 (PChome, Momo, 反斗城, Funbox)
    for func in [search_pchome_official, search_momo_official, search_toysrus_official, search_funbox_official]:
        for item in func(keyword):
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                combined.append(item)

    return combined
