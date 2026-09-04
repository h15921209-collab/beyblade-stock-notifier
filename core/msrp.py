import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# 台灣官方總代理（麗嬰國際 Funbox）戰鬥陀螺X (BEYBLADE X) 標準建議售價表 (NTD)
OFFICIAL_MSRP_TABLE = {
    # --- 基本 Booster 強化組 (單陀螺無發射器，官方定價 NT$ 399) ---
    "BX-01": 399, "BX-02": 399, "BX-03": 399, "BX-04": 399,
    "BX-05": 399, "BX-06": 399, "BX-08": 399, "BX-09": 399,
    "BX-13": 399, "BX-14": 399, "BX-15": 399, "BX-16": 399,
    "BX-19": 399, "BX-20": 399, "BX-21": 399, "BX-22": 399,
    "BX-23": 399, "BX-24": 399, "BX-26": 399, "BX-27": 399,
    "BX-31": 399, "BX-33": 399, "BX-34": 399, "BX-35": 399,
    "BX-36": 399, "BX-38": 399, "BX-50": 399,
    
    # --- Starter 入門組 (附發射器/發射線，官方定價 NT$ 550) ---
    "UX-01": 550, "UX-02": 550, "UX-03": 550, "UX-04": 550,
    "UX-05": 550, "UX-06": 550, "UX-07": 550, "UX-08": 550,
    "UX-09": 550, "UX-10": 550, "UX-11": 550, "UX-12": 550,
    "UX-13": 550, "UX-14": 550, "UX-15": 550, "UX-16": 550,
    "UX-17": 550, "UX-18": 550, "UX-19": 550, "UX-20": 550,
    "UX-21": 1399, # 三陀螺進階對戰組

    # --- 復刻紀念款 / 限定版 (BXG, BX00，官方定價 NT$ 750 ~ 999) ---
    "BXG-01": 750, "BXG-02": 750, "BXG-03": 750, "BXG-04": 750,
    "BXG-47": 999, "BX00": 999,
    
    # --- 客製系列 (CX) ---
    "CX-01": 450, "CX-02": 450, "CX-03": 450, "CX-04": 650,
    "CX-18": 650,

    # --- 發射器與握把配件 (官方原價 NT$ 250，原價+10% 上限為 NT$ 275) ---
    "BX-11": 250,  # 發射器握把
    "BX-12": 250,  # 發射器握把 (黑)
    "BX-18": 250,  # 旋風發射器 (天藍)
    "BX-28": 250,  # 旋風發射器 (白色)
    "BX-29": 250,  # 發射器握把 (白色)
    "BX-30": 250,  # 發射器握把配件
    "BX-39": 250,  # 發射器
    "BX-40": 250,  # 發射器
    "BX-51": 250,  # 旋風發射器

    # --- 收納箱與配件 (官方定價 NT$ 1199) ---
    "BX-25": 1199, # 戰鬥陀螺X專業收納手提包

    # --- 對戰盤 / 豪華對戰套裝組 ---
    "BX-07": 750,  # 極限對戰盤
    "BX-10": 750,  # X型對戰盤
    "BX-32": 899,  # 廣域對戰盤
    "BX-17": 1299, # 極限衝擊對戰組
    "BX-37": 1498, # 雙重極限衝擊戰鬥盤豪華版
    "BX-46": 1498, # 豪華對戰盤組
}

def extract_model_code(name: str) -> Optional[str]:
    """從商品名稱中提取型號代碼 (如 BX-28, BX-35, UX-04, BXG-01, BX00)"""
    name_upper = name.upper()
    # 支援 BXG-xx, BX-xx, UX-xx, CX-xx
    match = re.search(r'\b(BXG-[0-9]+|BX-[0-9]+|UX-[0-9]+|CX-[0-9]+|BX00)\b', name_upper)
    if match:
        return match.group(1)
    
    # 支援無連字號但常見的如 BX35, UX04, BX28
    match2 = re.search(r'\b(BX[0-9]{2}|UX[0-9]{2})\b', name_upper)
    if match2:
        val = match2.group(1)
        return f"{val[:2]}-{val[2:]}"

    return None

def get_official_price_and_limit(name: str, fallback_price: Optional[float] = None) -> Tuple[int, int]:
    """
    依據商品名稱判定官方原價與「原價 + 10%」上限 (四捨五入取整)
    回傳: (官方原價, 原價加10%上限)

    【鋼鐵紀律】：
    嚴禁聽信賣場黃牛開價！所有定價上限均以麗嬰國際總代理建議售價為基準。
    """
    model = extract_model_code(name)
    official_price = None

    if model and model in OFFICIAL_MSRP_TABLE:
        official_price = OFFICIAL_MSRP_TABLE[model]
    else:
        name_upper = name.upper()
        # 1. 任何發射器、握把、配件類 ➔ 官方原價絕不超過 NT$ 250 (上限 NT$ 275)
        if "發射器" in name_upper or "握把" in name_upper or "拉繩" in name_upper or "拉條" in name_upper:
            official_price = 250
        # 2. 任何豪華對戰組 ➔ 官方原價 NT$ 1498 (上限 NT$ 1648)
        elif "豪華" in name_upper or "對戰組" in name_upper or "戰鬥盤組" in name_upper:
            official_price = 1498
        # 3. 專業收納箱 ➔ 官方原價 NT$ 1199 (上限 NT$ 1319)
        elif "收納" in name_upper or "手提" in name_upper or "提包" in name_upper or "提箱" in name_upper:
            official_price = 1199
        # 4. 單純戰鬥盤 ➔ 官方原價 NT$ 750 (上限 NT$ 825)
        elif "對戰盤" in name_upper or "戰鬥盤" in name_upper:
            official_price = 750
        # 5. UX 系列單陀螺 ➔ 官方原價 NT$ 550 (上限 NT$ 605)
        elif "UX" in name_upper:
            official_price = 550
        # 6. 復刻紀念款 ➔ 官方原價 NT$ 750 (上限 NT$ 825)
        elif "BXG" in name_upper or "紀念" in name_upper or "復刻" in name_upper:
            official_price = 750
        # 7. 標準單顆陀螺 ➔ 官方原價一律鎖定 NT$ 399 (上限 NT$ 439)
        else:
            official_price = 399

    # 計算原價 + 10% (四捨五入)
    max_price = round(official_price * 1.10)
    return official_price, max_price
