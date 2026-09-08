import unittest
from core.stores_data import (
    OFFICIAL_STORES,
    get_all_stores,
    get_cities,
    get_stores_by_city,
    search_stores,
    get_google_maps_url
)

class TestStoresData(unittest.TestCase):
    def test_stores_count_and_integrity(self):
        """驗證門市數量達到 76 家以上，且每個門市欄位完整"""
        stores = get_all_stores()
        self.assertGreaterEqual(len(stores), 76, f"門市數量應 >= 76，目前為 {len(stores)}")
        for s in stores:
            self.assertTrue(s.get("name"), "門市名稱不可為空")
            self.assertTrue(s.get("city"), "門市縣市不可為空")
            self.assertTrue(s.get("mall"), "門市百貨商場不可為空")
            self.assertTrue(s.get("brand"), "門市品牌不可為空")

    def test_get_cities(self):
        """驗證縣市清單包含全台主要都會區"""
        cities = get_cities()
        self.assertIn("全部", cities)
        self.assertIn("台北", cities)
        self.assertIn("新北", cities)
        self.assertIn("台中", cities)
        self.assertIn("高雄", cities)

    def test_get_stores_by_city(self):
        """驗證縣市篩選功能與門市數量正確性"""
        taipei = get_stores_by_city("台北")
        self.assertEqual(len(taipei), 16)
        
        new_taipei = get_stores_by_city("新北")
        self.assertEqual(len(new_taipei), 13)

        kaohsiung = get_stores_by_city("高雄")
        self.assertEqual(len(kaohsiung), 4)

        all_stores = get_stores_by_city("全部")
        self.assertEqual(len(all_stores), len(OFFICIAL_STORES))

    def test_search_stores(self):
        """驗證關鍵字搜尋功能"""
        results = search_stores("A8")
        self.assertTrue(any("信義" in r["name"] or "A8" in r["name"] for r in results))

        results_toysrus = search_stores("玩具反斗城")
        self.assertGreaterEqual(len(results_toysrus), 1)

        results_empty = search_stores("")
        self.assertEqual(len(results_empty), len(OFFICIAL_STORES))

    def test_google_maps_url(self):
        """驗證 Google Maps 導航連結格式"""
        store = OFFICIAL_STORES[0]
        url = get_google_maps_url(store)
        self.assertTrue(url.startswith("https://www.google.com/maps/search/?api=1&query="))

if __name__ == "__main__":
    unittest.main()
