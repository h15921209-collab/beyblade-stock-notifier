import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# 台灣官方總代理（麗嬰國際）戰鬥陀螺X (BEYBLADE X) 標準建議售價表 (NTD)
OFFICIAL_MSRP_TABLE = {
    # 基本 Booster 強化組 (單陀螺無發射器)
    "BX-01": 399, "BX-02": 399, "BX-03": 399, "BX-04": 399,
    "BX-05": 399, "BX-06": 399, "BX-08": 399, "BX-09": 399,
    "BX-13": 399, "BX-14": 399, "BX-15": 399, "BX-16": 399,
    "BX-19": 399, "BX-20": 399, "BX-21": 399, "BX-23": 399,
    "BX-24": 399, "BX-26": 399, "BX-27": 399, "BX-31": 399,
    "BX-33": 399, "BX-34": 399, "BX-35": 399, "BX-36": 399,
    "BX-38": 399,
    
    # Starter 入門組 (附發射器/發射線)
    "UX-01": 550, "UX-02": 550, "UX-03": 550, "UX-04": 550,
    "UX-05": 550, "UX-06": 550, "UX-07": 550, "UX-08": 550,
    "UX-09": 550, "UX-10": 550,

    # 復刻紀念款 / 限定版 (BXG, BX00)
    "BXG-01": 750, "BXG-02": 750, "BXG-03": 750, "BXG-04": 750,
    "BXG-47": 999, "BX00": 999,
    
    # 特殊強化組 / 隨機組
    "CX-18": 650,

    # 對戰盤 / 豪華對戰組
    "BX-07": 750,  # 極限對戰盤
    "BX-10": 750,  # X型對戰盤
    "BX-17": 1299, # 極限衝擊對戰組
    "BX-32": 899,  # 廣域對戰盤
    "BX-37": 1498, # 雙重極限衝擊戰鬥盤豪華版

    # 配件與收納
    "BX-25": 1199, # 戰鬥陀螺X專業收納包
    "BX-11": 250,  # 發射器握把
    "BX-12": 250,  # 發射器握把
    "BX-18": 350,  # 握把擴充
}

def extract_model_code(name: str) -> Optional[str]:
    """從商品名稱中提取型號代碼 (如 BX-35, UX-04, BXG-01, BX00)"""
    name_upper = name.upper()
    # 支援 BXG-xx, BX-xx, UX-xx, CX-xx
    match = re.search(r'\b(BXG-[0-9]+|BX-[0-9]+|UX-[0-9]+|CX-[0-9]+|BX00)\b', name_upper)
    if match:
        return match.group(1)
    
    # 支援無連字號但常見的如 BX35, UX04
    match2 = re.search(r'\b(BX[0-9]{2}|UX[0-9]{2})\b', name_upper)
    if match2:
        val = match2.group(1)
        return f"{val[:2]}-{val[2:]}"

    return None

def get_official_price_and_limit(name: str, fallback_price: Optional[float] = None) -> Tuple[int, int]:
    """
    依據商品名稱判定官方原價與「原價 + 10%」上限 (四捨五入取整)
    回傳: (官方原價, 原價加10%上限)
    """
    model = extract_model_code(name)
    official_price = None

    if model and model in OFFICIAL_MSRP_TABLE:
        official_price = OFFICIAL_MSRP_TABLE[model]
    else:
        # 關鍵字類型推估
        name_upper = name.upper()
        if "豪華" in name_upper or "對戰組" in name_upper or "BX-37" in name_upper or "BX-17" in name_upper:
            official_price = 1498
        elif "收納包" in name_upper or "BX-25" in name_upper:
            official_price = 1199
        elif "對戰盤" in name_upper or "戰鬥盤" in name_upper:
            official_price = 750
        elif "UX" in name_upper:
            official_price = 550
        elif "BXG" in name_upper or "紀念" in name_upper or "復刻" in name_upper:
            official_price = 750
        elif fallback_price and fallback_price > 0:
            official_price = int(fallback_price)
        else:
            official_price = 399  # 預設標準單顆陀螺原價

    # 計算原價 + 10% (四捨五入)
    max_price = round(official_price * 1.10)
    return official_price, max_price
