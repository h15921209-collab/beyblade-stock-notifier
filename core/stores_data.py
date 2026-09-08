import urllib.parse
from typing import List, Dict, Any, Optional

# 全台經過官方授權、販售正版戰鬥陀螺之實體門市清單 (總計 76+ 家)
# 資料來源：全台 Funbox 百貨專櫃、玩具反斗城、鼎美玩具、Toy World、來玩聚等官方據點
OFFICIAL_STORES: List[Dict[str, Any]] = [
    # --- 台北市 (16 家) ---
    {"name": "FunBox Toy Store Outlet 麗嬰國際清倉中心", "city": "台北", "area": "內湖區", "type": "特賣Outlet", "brand": "Funbox", "mall": "內湖麗嬰清倉中心"},
    {"name": "Funbox Toys 南港 Lalaport", "city": "台北", "area": "南港區", "type": "百貨專櫃", "brand": "Funbox", "mall": "南港 LaLaport"},
    {"name": "Funbox Toys-三越南西", "city": "台北", "area": "中山區", "type": "百貨專櫃", "brand": "Funbox", "mall": "新光三越 台北南西店"},
    {"name": "Funbox Toys-信義新天地A8", "city": "台北", "area": "信義區", "type": "百貨專櫃", "brand": "Funbox", "mall": "新光三越 信義A8館 5F"},
    {"name": "Funbox Toys-南港CITYLINK", "city": "台北", "area": "南港區", "type": "百貨專櫃", "brand": "Funbox", "mall": "南港 CITYLINK"},
    {"name": "Funbox Toys-天母SOGO", "city": "台北", "area": "士林區", "type": "百貨專櫃", "brand": "Funbox", "mall": "遠東SOGO 天母店"},
    {"name": "Funbox Toys-天母三越", "city": "台北", "area": "士林區", "type": "百貨專櫃", "brand": "Funbox", "mall": "新光三越 天母店"},
    {"name": "Funbox Toys-潤泰南港", "city": "台北", "area": "南港區", "type": "百貨專櫃", "brand": "Funbox", "mall": "潤泰南港車站"},
    {"name": "Funbox Toys-美麗華", "city": "台北", "area": "中山區", "type": "百貨專櫃", "brand": "Funbox", "mall": "美麗華百樂園 4F"},
    {"name": "Funbox Toys-遠東SOGO", "city": "台北", "area": "大安區", "type": "百貨專櫃", "brand": "Funbox", "mall": "遠東SOGO 忠孝/復興館"},
    {"name": "Funbox Toys-遠百信義", "city": "台北", "area": "信義區", "type": "百貨專櫃", "brand": "Funbox", "mall": "遠百信義 A13 5F"},
    {"name": "南港環球Toy World", "city": "台北", "area": "南港區", "type": "連鎖玩具", "brand": "Toy World", "mall": "環球購物中心 南港車站店"},
    {"name": "玩具反斗城-天母大葉高島屋店", "city": "台北", "area": "士林區", "type": "連鎖旗艦", "brand": "玩具反斗城", "mall": "大葉高島屋 3F"},
    {"name": "鼎美 新光三越南西店", "city": "台北", "area": "中山區", "type": "百貨專櫃", "brand": "鼎美玩具", "mall": "新光三越 台北南西店"},
    {"name": "鼎美玩具：信義新光", "city": "台北", "area": "信義區", "type": "百貨專櫃", "brand": "鼎美玩具", "mall": "新光三越 信義新天地 A8"},
    {"name": "鼎美玩具：站前新光", "city": "台北", "area": "中正區", "type": "百貨專櫃", "brand": "鼎美玩具", "mall": "新光三越 台北站前店 8F"},

    # --- 新北市 (13 家) ---
    {"name": "Funbox Toys 誠品生活新店裕隆城", "city": "新北", "area": "新店區", "type": "百貨專櫃", "brand": "Funbox", "mall": "誠品生活新店 裕隆城 6F"},
    {"name": "Funbox Toys-中和環球", "city": "新北", "area": "中和區", "type": "百貨專櫃", "brand": "Funbox", "mall": "環球購物中心 中和店 3F"},
    {"name": "Funbox Toys-宏匯廣場", "city": "新北", "area": "新莊區", "type": "百貨專櫃", "brand": "Funbox", "mall": "宏匯廣場 5F"},
    {"name": "Funbox Toys-板橋大遠百", "city": "新北", "area": "板橋區", "type": "百貨專櫃", "brand": "Funbox", "mall": "Mega City 板橋大遠百 5F"},
    {"name": "Funbox Toys-板橋遠東", "city": "新北", "area": "板橋區", "type": "百貨專櫃", "brand": "Funbox", "mall": "遠東百貨 板橋中山店 6F"},
    {"name": "Funbox Toys-樹林秀泰", "city": "新北", "area": "樹林區", "type": "百貨專櫃", "brand": "Funbox", "mall": "秀泰生活 樹林店 4F"},
    {"name": "Funbox Toys-比漾廣場", "city": "新北", "area": "永和區", "type": "百貨專櫃", "brand": "Funbox", "mall": "永和比漾廣場 5F"},
    {"name": "Funbox Toys-汐科遠雄", "city": "新北", "area": "汐止區", "type": "百貨專櫃", "brand": "Funbox", "mall": "iFG遠雄廣場 3F"},
    {"name": "Funbox Toys-淡水禮萊廣場", "city": "新北", "area": "淡水區", "type": "百貨專櫃", "brand": "Funbox", "mall": "禮萊廣場 國賓影城 1F"},
    {"name": "Funbox 林口三井店", "city": "新北", "area": "林口區", "type": "特賣Outlet", "brand": "Funbox", "mall": "MITSUI OUTLET PARK 林口"},
    {"name": "TOY WORLD 中和環球店", "city": "新北", "area": "中和區", "type": "連鎖玩具", "brand": "Toy World", "mall": "環球購物中心 中和店 3F"},
    {"name": "Toyworld板橋環球", "city": "新北", "area": "板橋區", "type": "連鎖玩具", "brand": "Toy World", "mall": "板橋車站環球 2F"},
    {"name": "鼎美玩具板橋遠百店", "city": "新北", "area": "板橋區", "type": "百貨專櫃", "brand": "鼎美玩具", "mall": "遠東百貨 板橋中山店"},

    # --- 桃園市 (10 家) ---
    {"name": "Funbox Toys-台茂購物中心", "city": "桃園", "area": "蘆竹區", "type": "百貨專櫃", "brand": "Funbox", "mall": "台茂購物中心 4F"},
    {"name": "Funbox Toys-桃園環球A19", "city": "桃園", "area": "中壢區", "type": "百貨專櫃", "brand": "Funbox", "mall": "Global Mall 桃園A19 3F"},
    {"name": "Funbox Toys-桃園環球A8", "city": "桃園", "area": "龜山區", "type": "百貨專櫃", "brand": "Funbox", "mall": "Global Mall 桃園A8"},
    {"name": "Funbox Toys-桃園站前", "city": "桃園", "area": "桃園區", "type": "百貨專櫃", "brand": "Funbox", "mall": "新光三越 桃園站前店 8F"},
    {"name": "Funbox Toys-桃園遠東", "city": "桃園", "area": "桃園區", "type": "百貨專櫃", "brand": "Funbox", "mall": "遠東百貨 桃園店 6F"},
    {"name": "Funbox Toys-華泰名店城", "city": "桃園", "area": "中壢區", "type": "特賣Outlet", "brand": "Funbox", "mall": "GLORIA OUTLETS 華泰名店城"},
    {"name": "TOY WORLD 台茂", "city": "桃園", "area": "蘆竹區", "type": "連鎖玩具", "brand": "Toy World", "mall": "台茂購物中心 4F"},
    {"name": "TOY WORLD 大江購物中心", "city": "桃園", "area": "中壢區", "type": "連鎖玩具", "brand": "Toy World", "mall": "大江國際購物中心 4F"},
    {"name": "Toyworld 桃園環球A19店", "city": "桃園", "area": "中壢區", "type": "連鎖玩具", "brand": "Toy World", "mall": "Global Mall 桃園A19 3F"},
    {"name": "豬帽子 Boarhat 環球A19店", "city": "桃園", "area": "中壢區", "type": "專業模型", "brand": "豬帽子", "mall": "Global Mall 桃園A19 3F"},

    # --- 新竹縣市 (6 家) ---
    {"name": "Funbox Toys 竹北遠東店", "city": "新竹", "area": "竹北市", "type": "百貨專櫃", "brand": "Funbox", "mall": "遠東百貨 竹北店 4F"},
    {"name": "Funbox Toys-新竹巨城", "city": "新竹", "area": "東區", "type": "百貨專櫃", "brand": "Funbox", "mall": "Big City 遠東巨城購物中心 5F"},
    {"name": "Funbox Toys-新竹湳雅大魯閣", "city": "新竹", "area": "北區", "type": "百貨專櫃", "brand": "Funbox", "mall": "大魯閣湳雅廣場 2F"},
    {"name": "Funbox Toys-新竹遠東", "city": "新竹", "area": "東區", "type": "百貨專櫃", "brand": "Funbox", "mall": "新竹大遠百 6F"},
    {"name": "Funbox Toys-竹北享平方", "city": "新竹", "area": "竹北市", "type": "百貨專櫃", "brand": "Funbox", "mall": "享平方 Shown Square 2F"},
    {"name": "鼎美玩具 新竹遠百店", "city": "新竹", "area": "東區", "type": "百貨專櫃", "brand": "鼎美玩具", "mall": "新竹大遠百 6F"},

    # --- 苗栗縣 (1 家) ---
    {"name": "Funbox Toys-苗栗尚順", "city": "苗栗", "area": "頭份市", "type": "百貨專櫃", "brand": "Funbox", "mall": "尚順育樂世界 購物中心 5F"},

    # --- 台中市 (11 家) ---
    {"name": "Funbox Toys-台中Lalaport", "city": "台中", "area": "東區", "type": "百貨專櫃", "brand": "Funbox", "mall": "Mitsui Shopping Park LaLaport 台中 3F"},
    {"name": "Funbox Toys-台中三越", "city": "台中", "area": "西屯區", "type": "百貨專櫃", "brand": "Funbox", "mall": "新光三越 台中中港店 6F"},
    {"name": "Funbox Toys-台中中友", "city": "台中", "area": "北區", "type": "百貨專櫃", "brand": "Funbox", "mall": "中友百貨 C棟 7F"},
    {"name": "Funbox Toys-台中新時代", "city": "台中", "area": "東區", "type": "百貨專櫃", "brand": "Funbox", "mall": "大魯閣新時代購物中心 8F"},
    {"name": "Funbox Toys-台中港三井", "city": "台中", "area": "梧棲區", "type": "特賣Outlet", "brand": "Funbox", "mall": "MITSUI OUTLET PARK 台中港"},
    {"name": "Funbox Toys-台中遠東", "city": "台中", "area": "西屯區", "type": "百貨專櫃", "brand": "Funbox", "mall": "Top City 台中大遠百 5F"},
    {"name": "Funbox Toys-廣三SOGO", "city": "台中", "area": "西區", "type": "百貨專櫃", "brand": "Funbox", "mall": "廣三SOGO百貨 8F"},
    {"name": "Funbox Toys-文心秀泰", "city": "台中", "area": "南屯區", "type": "百貨專櫃", "brand": "Funbox", "mall": "秀泰生活 台中文心店 3F"},
    {"name": "Funbox Toys-豐原太平洋", "city": "台中", "area": "豐原區", "type": "百貨專櫃", "brand": "Funbox", "mall": "太平洋百貨 豐原店 5F"},
    {"name": "Funbox Toys-麗寶一期", "city": "台中", "area": "后里區", "type": "特賣Outlet", "brand": "Funbox", "mall": "麗寶Outlet Mall 一期 2F"},
    {"name": "Funbox Toys-麗寶二期", "city": "台中", "area": "后里區", "type": "特賣Outlet", "brand": "Funbox", "mall": "麗寶Outlet Mall 二期 D區"},

    # --- 嘉義市 (3 家) ---
    {"name": "Funbox Toys-嘉義三越", "city": "嘉義", "area": "西區", "type": "百貨專櫃", "brand": "Funbox", "mall": "新光三越 嘉義垂楊店 9F"},
    {"name": "Funbox Toys-嘉義耐斯", "city": "嘉義", "area": "東區", "type": "百貨專櫃", "brand": "Funbox", "mall": "耐斯廣場 購物中心 5F"},
    {"name": "Funbox Toys-嘉義遠東", "city": "嘉義", "area": "西區", "type": "百貨專櫃", "brand": "Funbox", "mall": "遠東百貨 嘉義店 6F"},

    # --- 台南市 (7 家) ---
    {"name": "Funbox Toys 新仁家樂福店", "city": "台南", "area": "仁德區", "type": "量販商場", "brand": "Funbox", "mall": "家樂福 新仁店 2F"},
    {"name": "Funbox Toys-南紡購物中心", "city": "台南", "area": "東區", "type": "百貨專櫃", "brand": "Funbox", "mall": "南紡購物中心 A1館 4F"},
    {"name": "Funbox Toys-台南三井", "city": "台南", "area": "歸仁區", "type": "特賣Outlet", "brand": "Funbox", "mall": "MITSUI OUTLET PARK 台南 3F"},
    {"name": "Funbox Toys-台南三越", "city": "台南", "area": "中西區", "type": "百貨專櫃", "brand": "Funbox", "mall": "新光三越 台南中山店 8F"},
    {"name": "Funbox Toys-台南西門", "city": "台南", "area": "中西區", "type": "百貨專櫃", "brand": "Funbox", "mall": "新光三越 台南新天地 本館 3F"},
    {"name": "Funbox Toys-台南遠百", "city": "台南", "area": "東區", "type": "百貨專櫃", "brand": "Funbox", "mall": "大遠百 台南成功店 5F"},
    {"name": "鼎美玩具 西門新光", "city": "台南", "area": "中西區", "type": "百貨專櫃", "brand": "鼎美玩具", "mall": "新光三越 台南新天地 3F"},

    # --- 高雄市 (4 家) ---
    {"name": "Funbox Toys-義大世界", "city": "高雄", "area": "大樹區", "type": "特賣Outlet", "brand": "Funbox", "mall": "義大世界購物廣場 C區 2F"},
    {"name": "Funbox Toys-高雄左營", "city": "高雄", "area": "左營區", "type": "百貨專櫃", "brand": "Funbox", "mall": "新光三越 高雄左營店 本館 5F"},
    {"name": "TOYWORLD岡山秀泰樂GO廣場", "city": "高雄", "area": "岡山區", "type": "連鎖玩具", "brand": "Toy World", "mall": "樂購廣場 秀泰影城 3F"},
    {"name": "鼎美玩具 漢神巨蛋", "city": "高雄", "area": "左營區", "type": "百貨專櫃", "brand": "鼎美玩具", "mall": "漢神巨蛋 購物廣場 6F"},

    # --- 屏東縣 (2 家) ---
    {"name": "Funbox Toys-屏東太平洋", "city": "屏東", "area": "屏東市", "type": "百貨專櫃", "brand": "Funbox", "mall": "太平洋百貨 屏東店 5F"},
    {"name": "Funbox Toys-屏東環球", "city": "屏東", "area": "屏東市", "type": "百貨專櫃", "brand": "Funbox", "mall": "環球購物中心 屏東市 3F"},

    # --- 宜蘭縣 (1 家) ---
    {"name": "Funbox Toys-新月廣場", "city": "宜蘭", "area": "宜蘭市", "type": "百貨專櫃", "brand": "Funbox", "mall": "蘭城新月廣場 4F"},

    # --- 台東縣 (1 家) ---
    {"name": "Funbox Toys-台東秀泰", "city": "台東", "area": "台東市", "type": "百貨專櫃", "brand": "Funbox", "mall": "秀泰生活 台東店 2F"},

    # --- 澎湖縣 (1 家) ---
    {"name": "Funbox Toys-澎坊商場", "city": "其他", "area": "馬公市", "type": "免稅商場", "brand": "Funbox", "mall": "Pier3 三號港 3F"},
]

def get_all_stores() -> List[Dict[str, Any]]:
    """取得全台所有正版官方門市清單"""
    return OFFICIAL_STORES

def get_cities() -> List[str]:
    """取得所有收錄的縣市名稱（含門市數量統計）"""
    city_order = ["全部", "台北", "新北", "桃園", "新竹", "苗栗", "台中", "嘉義", "台南", "高雄", "屏東", "宜蘭", "台東", "其他"]
    existing = {s["city"] for s in OFFICIAL_STORES}
    return [c for c in city_order if c == "全部" or c in existing]

def get_stores_by_city(city: str) -> List[Dict[str, Any]]:
    """依照縣市篩選門市清單"""
    if not city or city == "全部":
        return OFFICIAL_STORES
    return [s for s in OFFICIAL_STORES if s["city"] == city]

def search_stores(keyword: str) -> List[Dict[str, Any]]:
    """根據名稱、區域、商場或品牌關鍵字搜尋門市"""
    if not keyword or not keyword.strip():
        return OFFICIAL_STORES
    kw = keyword.strip().lower()
    return [
        s for s in OFFICIAL_STORES
        if kw in s["name"].lower()
        or kw in s["city"].lower()
        or kw in s["area"].lower()
        or kw in s["mall"].lower()
        or kw in s["brand"].lower()
    ]

def get_google_maps_url(store: Dict[str, Any]) -> str:
    """產生該門市的 Google Maps 搜尋與導航連結"""
    query = f"{store['name']} {store['mall']}"
    return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"
