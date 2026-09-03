import unittest
from unittest.mock import patch, MagicMock
from notifier.line import LineNotifier
from scrapers.base import ProductInfo, StockStatus

class TestLineNotifier(unittest.TestCase):
    def setUp(self):
        self.notifier = LineNotifier("test_channel_token", "test_user_id")

    def test_is_configured(self):
        self.assertTrue(self.notifier.is_configured())
        empty_notifier = LineNotifier("", "")
        self.assertFalse(empty_notifier.is_configured())

    @patch("requests.post")
    def test_send_stock_alert_payload(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        info = ProductInfo(
            url="https://shop.funbox.com.tw/products/bx35",
            platform_name="麗嬰國際官方購物網",
            title="BX-35 戰鬥陀螺",
            price=399.0,
            status=StockStatus.IN_STOCK,
            direct_buy_url="https://shop.funbox.com.tw/products/bx35"
        )

        success = self.notifier.send_stock_alert(info)
        self.assertTrue(success)

        # 驗證請求參數
        self.assertTrue(mock_post.called)
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_channel_token")
        
        body = kwargs["json"]
        self.assertEqual(body["to"], "test_user_id")
        self.assertEqual(len(body["messages"]), 1)
        self.assertEqual(body["messages"][0]["type"], "flex")

        # 驗證直達搶購按鈕之 URI
        flex_body = body["messages"][0]["contents"]
        footer_btn = flex_body["footer"]["contents"][0]
        self.assertEqual(footer_btn["action"]["uri"], "https://shop.funbox.com.tw/products/bx35")

if __name__ == "__main__":
    unittest.main()
