import pytest
from unittest.mock import MagicMock, patch
from scrapers.base import ProductInfo, StockStatus
from core.dynamic_scanner import (
    scan_pchome_dynamic,
    scan_momo_dynamic,
    scan_toysrus_dynamic,
    scan_funbox_dynamic,
    scan_all_dynamic_channels,
)
from notifier.line import LineNotifier
from core.engine import MonitorEngine

def test_dynamic_scanner_pchome_filter(monkeypatch):
    """測試 PChome 動態掃蕩能正確過濾正版陀螺並阻擋黑名單/非陀螺雜物"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "prods": [
            {
                "Id": "PROD_GENUINE_1",
                "name": "TAKARATOMY BEYBLADE X 戰鬥陀螺 BX-34 鈷藍巨龍 2-60C",
                "price": 399
            },
            {
                "Id": "PROD_FAKE_AIRFRYER",
                "name": "PHILIPS 飛利浦 氣炸鍋 抽UX戰鬥陀螺",
                "price": 3999
            },
            {
                "Id": "PROD_EXPENSIVE_SCALPER",
                "name": "TAKARATOMY BEYBLADE X 戰鬥陀螺 BX-34 鈷藍巨龍",
                "price": 1800  # 超過 MSRP (399 + 10% = 439)
            }
        ]
    }

    with patch("requests.get", return_value=mock_resp), \
         patch("core.dynamic_scanner.PChomeScraper.check_stock") as mock_check:
        mock_check.return_value = ProductInfo(
            url="https://24h.pchome.com.tw/prod/PROD_GENUINE_1",
            platform_name="PChome 24h 購物",
            title="TAKARATOMY BEYBLADE X 戰鬥陀螺 BX-34 鈷藍巨龍 2-60C",
            price=399,
            status=StockStatus.IN_STOCK
        )

        results = scan_pchome_dynamic(limit=10)
        assert len(results) == 1
        assert results[0].price == 399
        assert "BX-34" in results[0].title

def test_dynamic_scanner_momo_filter(monkeypatch):
    """測試 Momo 動態掃蕩能正確解析並過濾"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = (
        'self.__next_f.push([1,"{\\"goodsCode\\":\\"15502059\\",\\"goodsName\\":\\"TAKARA TOMY 戰鬥陀螺X UX-03 魔導神杖\\",\\"goodsPrice\\":\\"550\\"}"]);'
        'self.__next_f.push([1,"{\\"goodsCode\\":\\"99999999\\",\\"goodsName\\":\\"PHILIPS 飛利浦氣炸鍋\\",\\"goodsPrice\\":\\"4990\\"}"]);'
    )

    with patch("requests.get", return_value=mock_resp), \
         patch("core.dynamic_scanner.MomoScraper.check_stock") as mock_check:
        mock_check.return_value = ProductInfo(
            url="https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code=15502059",
            platform_name="Momo 購物網",
            title="TAKARA TOMY 戰鬥陀螺X UX-03 魔導神杖",
            price=550,
            status=StockStatus.IN_STOCK
        )

        results = scan_momo_dynamic(limit=10)
        assert len(results) == 1
        assert results[0].price == 550
        assert "UX-03" in results[0].title

def test_dynamic_scanner_toysrus_and_funbox():
    """測試 Toysrus 與 Funbox 掃描過濾邏輯"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = """
    <html>
        <body>
            <a href="/products/tm01234">戰鬥陀螺X BX-07 極限對戰盤</a>
            <a href="/products/clothes123">精美戰鬥陀螺衣服長褲</a>
        </body>
    </html>
    """

    with patch("requests.get", return_value=mock_resp), \
         patch("core.dynamic_scanner.FunboxScraper.check_stock") as mock_check:
        mock_check.return_value = ProductInfo(
            url="https://shop.funbox.com.tw/products/tm01234",
            platform_name="麗嬰國際官方商城",
            title="戰鬥陀螺X BX-07 極限對戰盤",
            price=750,
            status=StockStatus.IN_STOCK
        )

        results = scan_funbox_dynamic(limit=10)
        assert len(results) == 1
        assert "BX-07" in results[0].title

def test_scan_all_dynamic_channels():
    """測試四大通路匯流與網址去重"""
    prod1 = ProductInfo(
        url="https://24h.pchome.com.tw/prod/P1",
        platform_name="PChome 24h",
        title="戰鬥陀螺X BX-01",
        price=399,
        status=StockStatus.IN_STOCK
    )
    prod2 = ProductInfo(
        url="https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code=M1",
        platform_name="Momo 購物網",
        title="戰鬥陀螺X UX-01",
        price=550,
        status=StockStatus.IN_STOCK
    )

    with patch("core.dynamic_scanner.scan_pchome_dynamic", return_value=[prod1]), \
         patch("core.dynamic_scanner.scan_momo_dynamic", return_value=[prod2]), \
         patch("core.dynamic_scanner.scan_toysrus_dynamic", return_value=[]), \
         patch("core.dynamic_scanner.scan_funbox_dynamic", return_value=[prod1]):  # 重複的 url
        
        all_prods = scan_all_dynamic_channels(limit_per_channel=10)
        assert len(all_prods) == 2
        urls = {p.url for p in all_prods}
        assert "https://24h.pchome.com.tw/prod/P1" in urls
        assert "https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code=M1" in urls

def test_line_notifier_dynamic_alert():
    """測試動態突發捕獲專屬推播卡片建立與雙按鈕"""
    notifier = LineNotifier("test_token", "test_user")
    mock_push = MagicMock(return_value=True)
    notifier.send_push = mock_push

    info = ProductInfo(
        url="https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code=12345",
        platform_name="Momo 購物網",
        title="TAKARA TOMY 戰鬥陀螺X UX-03 魔導神杖",
        price=550,
        status=StockStatus.IN_STOCK
    )

    success = notifier.send_dynamic_stock_alert(info, official_price=550, max_price=605)
    assert success is True
    assert mock_push.called

    call_args = mock_push.call_args[0][0]
    msg = call_args[0]
    assert msg["type"] == "flex"
    assert "⚡【全網動態突發捕獲】" in msg["altText"]

    # 驗證雙按鈕設計
    buttons = msg["contents"]["footer"]["contents"]
    assert len(buttons) == 2
    assert buttons[0]["action"]["label"] == "🛒 立即前往搶購"
    assert buttons[0]["action"]["uri"] == info.direct_buy_url
    assert buttons[1]["action"]["label"] == "🌀 開啟手機管理後台"
    assert "beyblade-stock.streamlit.app" in buttons[1]["action"]["uri"]

def test_engine_dynamic_sweep_integration(tmp_path):
    """測試 Engine 巡檢包含動態掃蕩與防重複推播流程"""
    cfg_file = tmp_path / "test_cfg.yaml"
    cfg_file.write_text("""
line_notify:
  channel_access_token: "fake"
  user_id: "fake"
monitor:
  enable_dynamic_scanner: true
  notify_on_initial_stock: true
  state_file: "{}"
targets: []
""".format(str(tmp_path / "state.json").replace("\\", "/")), encoding="utf-8")

    engine = MonitorEngine(config_path=str(cfg_file))
    engine.notifier.send_dynamic_stock_alert = MagicMock(return_value=True)
    engine.notifier.send_digest_report = MagicMock(return_value=True)

    fake_prod = ProductInfo(
        url="https://24h.pchome.com.tw/prod/DYN123",
        platform_name="PChome 24h",
        title="戰鬥陀螺X BX-35 黑鳳凰",
        price=399,
        status=StockStatus.IN_STOCK
    )

    with patch("core.dynamic_scanner.scan_all_dynamic_channels", return_value=[fake_prod]):
        # 第一輪巡檢：應該發送動態補貨通知
        results = engine.check_all_once(is_manual=False)
        assert len(results) == 1
        assert engine.notifier.send_dynamic_stock_alert.call_count == 1

        # 第二輪巡檢：若持續有現貨，智慧雙軌記憶應阻擋重複通知
        results2 = engine.check_all_once(is_manual=False)
        assert engine.notifier.send_dynamic_stock_alert.call_count == 1  # 依然為 1，不重複發送
