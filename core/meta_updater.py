import json
import os
import sys
import re
import logging
from datetime import datetime
from typing import Dict, List, Any

# 確保當前目錄在 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from bs4 import BeautifulSoup
from core.msrp import get_official_price_and_limit, extract_model_code

logger = logging.getLogger(__name__)

DATA_FILE = "data/hot_picks.json"

# 社群與賽事公認比賽 T0 / 神級零件關鍵字
META_LEGENDARY_MODELS = {
    "UX-03": ("魔導神杖 (Wizard Rod)", "賽事長期統治級 T0 軸心神物，持久防禦雙絕頂"),
    "BX-35": ("隨機強化組Vol.4 (黑鳳凰羽翼)", "社群超人氣稀有防禦刃，抽率極低的神物"),
    "BX-23": ("鳳凰飛翼 (Phoenix Wing)", "金屬塗裝重裝甲，超強外側離心力主力攻擊刃"),
    "UX-04": ("戰鬥白龍 (Aero Pegasus / Dran Dagger)", "極限衝擊超人氣款式，比賽常勝攻擊軸心"),
    "UX-21": ("三陀螺對戰組 (巨神/狂暴組合)", "社群必買進階實戰套組，配件極度實用"),
    "UX-15": ("超加速特化型戰鬥陀螺", "高階賽事出賽率極高的特化新主流"),
}

def load_hot_picks() -> Dict[str, Any]:
    """讀取熱門神物資料庫"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"讀取 {DATA_FILE} 失敗: {e}")
    return {}

def update_hot_picks_from_sources() -> Dict[str, Any]:
    """
    自動連線台灣總代理麗嬰國際、玩具反斗城與 PChome 24h，
    爬取並分析最新上市款式，自動分類整理出最新社群與賽事熱門神物清單。
    """
    logger.info("開始從官方通路與社群情報更新熱門神物清單...")
    
    discovered_items = {} # model_code -> {model, name, desc, official_price}

    # 1. 先置入社群傳奇神物
    for model, (name, desc) in META_LEGENDARY_MODELS.items():
        off_p, _ = get_official_price_and_limit(model)
        discovered_items[model] = {
            "model": model,
            "name": name,
            "desc": desc,
            "official_price": off_p,
            "tier": "LEGEND"
        }

    # 2. 爬取麗嬰國際與 PChome 最新上架型號
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        # PChome 24h 最新陀螺
        r = requests.get("https://ecshweb.pchome.com.tw/search/v3.3/all/results?q=BEYBLADE%20X&page=1&sort=new/dc", headers=headers, timeout=8)
        if r.status_code == 200:
            data = r.json()
            for p in data.get("prods", []):
                p_name = p.get("name", "")
                model = extract_model_code(p_name)
                if model and model not in discovered_items:
                    off_p, _ = get_official_price_and_limit(p_name, fallback_price=p.get("price"))
                    clean_title = re.sub(r'【.*?】|TAKARA TOMY|BEYBLADE X|戰鬥陀螺|公司貨|正版|代理', '', p_name).strip()
                    discovered_items[model] = {
                        "model": model,
                        "name": clean_title or model,
                        "desc": f"官方最新上市款式 (原廠定價 NT$ {off_p})",
                        "official_price": off_p,
                        "tier": "NEW"
                    }
    except Exception as e:
        logger.warning(f"爬取 PChome 最新陀螺失敗: {e}")

    try:
        # 麗嬰國際官方商城最新陀螺
        r = requests.get("https://shop.funbox.com.tw/products?query=%E6%88%B0%E9%AC%A5%E9%99%80%E8%9E%BA", headers=headers, timeout=8)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                title = a.text.strip()
                model = extract_model_code(title)
                if model and model not in discovered_items and len(title) > 4:
                    off_p, _ = get_official_price_and_limit(title)
                    clean_title = re.sub(r'TAKARA TOMY|BEYBLADE X|戰鬥陀螺|麗嬰國際', '', title).strip()
                    discovered_items[model] = {
                        "model": model,
                        "name": clean_title or model,
                        "desc": f"麗嬰國際總代理推薦 (原廠定價 NT$ {off_p})",
                        "official_price": off_p,
                        "tier": "NEW"
                    }
    except Exception as e:
        logger.warning(f"爬取麗嬰國際失敗: {e}")

    # 3. 分類整合
    cat_legend = []
    cat_ux = []
    cat_bx = []
    cat_special = []

    # 確保經典神物排在第一區
    for model, (name, desc) in META_LEGENDARY_MODELS.items():
        off_p, _ = get_official_price_and_limit(model)
        cat_legend.append({
            "model": model,
            "name": name,
            "desc": desc,
            "official_price": off_p
        })

    for model, item in discovered_items.items():
        if model in META_LEGENDARY_MODELS:
            continue
        
        m_upper = model.upper()
        if "UX" in m_upper:
            cat_ux.append(item)
        elif "BXG" in m_upper or "00" in m_upper or "BX-25" in m_upper or "BX-37" in m_upper or "BX-07" in m_upper or "BX-10" in m_upper:
            cat_special.append(item)
        elif "BX" in m_upper or "CX" in m_upper:
            cat_bx.append(item)
        else:
            cat_bx.append(item)

    # 補充重要配件若未抓到
    special_defaults = [
        {"model": "BX-25", "name": "戰鬥陀螺X 專業收納手提包", "desc": "全台常態缺貨手提箱神物", "official_price": 1199},
        {"model": "BX-37", "name": "雙重極限衝擊戰鬥盤豪華組", "desc": "雙軌道超加速對戰套裝", "official_price": 1498},
        {"model": "BX-07", "name": "極限對戰盤 (單盤)", "desc": "標準 X 賽事必備加速齒輪盤", "official_price": 750},
        {"model": "BXG-01", "name": "復刻紀念款 烈焰飛鳳S", "desc": "初代爆轉陀螺經典復刻限定版", "official_price": 750},
        {"model": "BXG-04", "name": "復刻紀念款 銀牙烈虎S", "desc": "初代爆轉白虎復刻限定版", "official_price": 750},
        {"model": "BX00", "name": "復刻限定 暴風天馬3 (BXG-47)", "desc": "鋼鐵奇兵情懷天馬限定款", "official_price": 999},
    ]
    seen_special_models = {x["model"] for x in cat_special}
    for sd in special_defaults:
        if sd["model"] not in seen_special_models:
            cat_special.append(sd)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    final_data = {
        "last_updated": now_str,
        "categories": {
            "🏆 論壇社群神物款": cat_legend[:6],
            "🔥 UX 最新獨特系列": cat_ux[:8] if cat_ux else [
                {"model": "UX-08", "name": "白銀神狼 (Silver Wolf 3-80FB)", "desc": "持久型新王者", "official_price": 550},
                {"model": "UX-09", "name": "幽靈武士 (Ghost Circle 0-80GB)", "desc": "圓形金屬環極限離心力", "official_price": 550},
                {"model": "UX-10", "name": "騎士神劍 (Knight Mail 3-85BS)", "desc": "重裝甲衝擊防禦新型態", "official_price": 550},
                {"model": "UX-01", "name": "德蘭巨劍 (Dran Buster 1-60A)", "desc": "一擊必殺單點重衝擊", "official_price": 550},
                {"model": "UX-02", "name": "地獄炎鐮 (Hells Hammer 3-70H)", "desc": "平衡型下壓重擊型戰鬥陀螺", "official_price": 550},
            ],
            "🌀 BX & CX 強勢主力款": cat_bx[:8] if cat_bx else [
                {"model": "BX-36", "name": "鯨魚浪潮 (Whale Wave 5-80E)", "desc": "最新大重量波浪形攻擊刃", "official_price": 399},
                {"model": "BX-34", "name": "鈷藍巨龍 (Cobalt Dragoon 2-60C)", "desc": "左迴旋強勢攻擊型陀螺", "official_price": 399},
                {"model": "BX-33", "name": "衝擊猛擊白虎 (Weiss Tiger 3-60U)", "desc": "高機動彈射爆擊型", "official_price": 399},
                {"model": "BX-31", "name": "隨機強化組Vol.3 (暴龍打擊)", "desc": "強勢配件大集合", "official_price": 399},
                {"model": "BX-24", "name": "隨機強化組Vol.2 (雙足翼龍)", "desc": "超搶手罕見雙刀刃款", "official_price": 399},
            ],
            "🎁 限定紀念與對戰配件": cat_special[:8]
        }
    }

    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    total_count = sum(len(v) for v in final_data["categories"].values())
    logger.info(f"✅ 熱門神物情報庫更新完成！共彙整 {total_count} 款主流陀螺 (更新時間: {now_str})")
    return final_data

if __name__ == "__main__":
    update_hot_picks_from_sources()
