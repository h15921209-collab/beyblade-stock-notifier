import unittest
from unittest.mock import MagicMock, patch
from scrapers import (
    ScraperDispatcher,
    FunboxScraper,
    PChomeScraper,
    ToysrusScraper,
    MomoScraper,
    ShopeeFunboxScraper,
    KubiScraper,
    EsliteScraper,
    StockStatus,
    ProductInfo
)

class TestScrapers(unittest.TestCase):
    def setUp(self):
        self.dispatcher = ScraperDispatcher()

    def test_dispatcher_routing(self):
        """測試 7 大平台網址是否能精確分派到對應的 Scraper"""
        urls_and_types = [
            ("https://shop.funbox.com.tw/products/tm07984", FunboxScraper),
            ("https://24h.pchome.com.tw/prod/DEASR1-B900H2BID", PChomeScraper),
            ("https://www.toysrus.com.tw/zh-tw/beyblade-10058492.html", ToysrusScraper),
            ("https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code=12953255", MomoScraper),
            ("https://shopee.tw/product/42721867/25578850687", ShopeeFunboxScraper),
            ("https://preorder.amuzinc.com/products/bx-35", KubiScraper),
            ("https://www.eslite.com/product/1001234567", EsliteScraper),
        ]

        for url, expected_type in urls_and_types:
            scraper = self.dispatcher.get_scraper(url)
            self.assertIsNotNone(scraper, f"無法找到對應的 Scraper: {url}")
            self.assertIsInstance(scraper, expected_type, f"網址分派錯誤: {url} -> {type(scraper)}")

    def test_funbox_json_parsing(self):
        """測試麗嬰國際 Shopline JSON 解析與庫存判斷"""
        scraper = FunboxScraper()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "title": "BEYBLADE X BX-35 隨機強化組 Vol.4",
            "price": "399.0",
            "available": True,
            "featured_image": "https://img.funbox.com.tw/bx35.jpg",
            "variants": [{"available": True, "price": "399.0"}]
        }

        with patch.object(scraper.session, "get", return_value=mock_resp):
            info = scraper.check_stock("https://shop.funbox.com.tw/products/bx35-vol4")
            self.assertEqual(info.status, StockStatus.IN_STOCK)
            self.assertEqual(info.price, 399.0)
            self.assertEqual(info.title, "BEYBLADE X BX-35 隨機強化組 Vol.4")
            self.assertEqual(info.direct_buy_url, "https://shop.funbox.com.tw/products/bx35-vol4")

    def test_pchome_jsonp_parsing(self):
        """測試 PChome JSONP 解析與庫存數量判斷"""
        scraper = PChomeScraper()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = 'try{jsonp_prod({"DEASR1-B900H2BID-000":{"Name":"BX-25 戰鬥陀螺X專業收納包","Price":{"P":1199},"Qty":5,"Store":"DEASR1"}});}catch(e){}'

        with patch.object(scraper.session, "get", return_value=mock_resp):
            info = scraper.check_stock("https://24h.pchome.com.tw/prod/DEASR1-B900H2BID")
            self.assertEqual(info.status, StockStatus.IN_STOCK)
            self.assertEqual(info.price, 1199.0)
            self.assertEqual(info.stock_qty, 5)
            self.assertEqual(info.title, "BX-25 戰鬥陀螺X專業收納包")

    def test_toysrus_ldjson_parsing(self):
        """測試玩具反斗城 Schema.org JSON-LD 解析"""
        scraper = ToysrusScraper()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '''
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@type": "Product",
                "name": "BX-37 雙重極限衝擊戰鬥盤豪華組",
                "offers": {
                    "price": 1498,
                    "availability": "http://schema.org/InStock"
                }
            }
            </script>
        </head>
        <body></body>
        </html>
        '''

        with patch.object(scraper.session, "get", return_value=mock_resp):
            info = scraper.check_stock("https://www.toysrus.com.tw/zh-tw/beyblade-bx-37-10058492.html")
            self.assertEqual(info.status, StockStatus.IN_STOCK)
            self.assertEqual(info.price, 1498.0)
            self.assertIn("BX-37", info.title)

    def test_momo_out_of_stock_parsing(self):
        """測試 Momo 缺貨判定"""
        scraper = MomoScraper()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '''
        <html>
        <head>
            <meta property="og:title" content="【TAKARA TOMY】BEYBLADE X BX-35 隨機強化組" />
            <meta property="product:price:amount" content="450" />
        </head>
        <body>
            <div class="soldOut">此商品已售完，補貨中</div>
        </body>
        </html>
        '''

        with patch.object(scraper.session, "get", return_value=mock_resp):
            info = scraper.check_stock("https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code=12953255")
            self.assertEqual(info.status, StockStatus.OUT_OF_STOCK)
            self.assertEqual(info.price, 450.0)

if __name__ == "__main__":
    unittest.main()
