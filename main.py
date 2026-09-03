import argparse
import logging
import os
import sys

# 設定 UTF-8 輸出以正確顯示繁體中文與表情符號
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("Main")

def main():
    parser = argparse.ArgumentParser(description="戰鬥陀螺X (Beyblade X) 缺貨有貨即時 LINE 通知系統")
    parser.add_argument("--config", default="config.yaml", help="設定檔路徑 (預設: config.yaml)")
    parser.add_argument("--check-once", action="store_true", help="執行單次巡檢後退出 (適合 GitHub Actions 或 Cron)")
    parser.add_argument("--test-line", action="store_true", help="發送 LINE 測試連線訊息")
    parser.add_argument("--test-url", help="測試單一商品網址之爬蟲解析結果")
    parser.add_argument("--daemon", action="store_true", help="啟動 24 小時背景常駐監控模式")

    args = parser.parse_args()

    # 若 config.yaml 不存在但 config.example.yaml 存在，提示使用者
    config_file = args.config
    if not os.path.exists(config_file):
        if os.path.exists("config.example.yaml") and (args.check_once or args.daemon or args.test_line):
            logger.warning(f"找不到 {config_file}，暫時使用 config.example.yaml 進行示範/測試")
            config_file = "config.example.yaml"

    # 1. 測試單一商品網址
    if args.test_url:
        from scrapers import ScraperDispatcher
        dispatcher = ScraperDispatcher()
        print(f"\n🔍 正在測試解析網址: {args.test_url}")
        info = dispatcher.check({"url": args.test_url})
        print("========================================")
        print(f"平台通路: {info.platform_name}")
        print(f"商品標題: {info.title}")
        print(f"價格: NT$ {info.price}")
        print(f"狀態: {info.status.value}")
        print(f"庫存量: {info.stock_qty}")
        print(f"直達搶購連結: {info.direct_buy_url}")
        if info.error_msg:
            print(f"錯誤訊息: {info.error_msg}")
        print("========================================\n")
        return

    # 2. 測試 LINE 連線
    if args.test_line:
        from core import MonitorEngine
        engine = MonitorEngine(config_path=config_file)
        print("\n🚀 正在發送 LINE 測試推播訊息...")
        success = engine.notifier.send_test_message()
        if success:
            print("✅ 測試訊息發送成功！請檢查手機 LINE 官方帳號訊息。")
        else:
            print("❌ 發送失敗，請確認 config.yaml 或環境變數中的 channel_access_token 與 user_id 是否正確。")
        return

    # 3. 執行單次檢查 (GitHub Actions / 手動觸發)
    if args.check_once:
        from core import MonitorEngine
        engine = MonitorEngine(config_path=config_file)
        engine.check_all_once()
        return

    # 4. 常駐背景模式 (預設行為)
    from core import MonitorEngine
    engine = MonitorEngine(config_path=config_file)
    engine.run_daemon()

if __name__ == "__main__":
    main()
