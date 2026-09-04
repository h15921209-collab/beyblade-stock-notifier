import unittest
import os
from core.tracker import StateTracker
from scrapers.base import ProductInfo, StockStatus

class TestTracker(unittest.TestCase):
    def setUp(self):
        self.test_state_file = "test_state.json"
        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)
        self.tracker = StateTracker(state_file=self.test_state_file, notify_on_initial_stock=True)

    def tearDown(self):
        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)

    def test_state_transitions_and_deduplication(self):
        """測試狀態轉換與防重複推播邏輯"""
        target = {"name": "BX-35 陀螺", "url": "https://example.com/bx35", "max_price": 500}

        # 1. 首次檢測有貨 -> 應觸發推播
        info_in_stock = ProductInfo(
            url="https://example.com/bx35",
            platform_name="TestShop",
            title="BX-35 陀螺",
            price=399.0,
            status=StockStatus.IN_STOCK,
            direct_buy_url="https://example.com/bx35"
        )
        self.assertTrue(self.tracker.should_notify(target, info_in_stock))

        # 2. 第二次檢測仍為有貨 -> 應保持沉默（防重複洗版）
        self.assertFalse(self.tracker.should_notify(target, info_in_stock))

        # 3. 第三次檢測變為缺貨 -> 不推播，但狀態更新為 OUT_OF_STOCK
        info_out_of_stock = ProductInfo(
            url="https://example.com/bx35",
            platform_name="TestShop",
            title="BX-35 陀螺",
            price=399.0,
            status=StockStatus.OUT_OF_STOCK,
            direct_buy_url="https://example.com/bx35"
        )
        self.assertFalse(self.tracker.should_notify(target, info_out_of_stock))

        # 4. 第四次檢測重新補貨 (OUT_OF_STOCK -> IN_STOCK) -> 應再次觸發補貨推播！
        self.assertTrue(self.tracker.should_notify(target, info_in_stock))

    def test_max_price_filter(self):
        """測試最高金額防黃牛過濾"""
        target = {"name": "BX-35 陀螺", "url": "https://example.com/bx35", "max_price": 400}
        
        # 價格 450 超過上限 400 -> 不應推播
        info_expensive = ProductInfo(
            url="https://example.com/bx35",
            platform_name="TestShop",
            title="BX-35 陀螺",
            price=450.0,
            status=StockStatus.IN_STOCK
        )
        self.assertFalse(self.tracker.should_notify(target, info_expensive))

    def test_bx28_scalper_block(self):
        """測試 BX-28 旋風發射器賣 1280 時絕對會被防黃牛機制封殺"""
        from core.msrp import get_official_price_and_limit
        off_p, max_p = get_official_price_and_limit("TAKARATOMY BEYBLADE X 戰鬥陀螺X BX-28 旋風發射器 右迴旋(白色) 陀螺")
        self.assertEqual(off_p, 250)
        self.assertEqual(max_p, 275)

        target = {"name": "BX-28 旋風發射器", "url": "https://example.com/bx28", "max_price": max_p}
        info_scalper = ProductInfo(
            url="https://example.com/bx28",
            platform_name="PChome",
            title="BX-28 旋風發射器",
            price=1280.0,
            status=StockStatus.IN_STOCK
        )
        # 1280 遠高於 275，絕不推播！
        self.assertFalse(self.tracker.should_notify(target, info_scalper))

if __name__ == "__main__":
    unittest.main()
