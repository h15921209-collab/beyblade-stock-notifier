import os
import time
import random
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import yaml

from scrapers import ScraperDispatcher, ProductInfo, StockStatus
from notifier import LineNotifier
from .tracker import StateTracker

logger = logging.getLogger("MonitorEngine")

class MonitorEngine:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.load_config()

        # 初始化 LINE Notifier (優先吃環境變數，方便雲端/Docker/Actions 注入)
        line_cfg = self.config.get("line_notify", {})
        channel_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN") or line_cfg.get("channel_access_token", "")
        user_id = os.environ.get("LINE_USER_ID") or line_cfg.get("user_id", "")
        self.notifier = LineNotifier(channel_token, user_id)

        # 監控設定
        mon_cfg = self.config.get("monitor", {})
        self.interval = int(os.environ.get("MONITOR_INTERVAL") or mon_cfg.get("interval_seconds", 60))
        self.jitter_min = int(mon_cfg.get("jitter_min_seconds", 5))
        self.jitter_max = int(mon_cfg.get("jitter_max_seconds", 15))
        self.heartbeat_time = str(mon_cfg.get("heartbeat_time", "09:00")).strip()
        self.notify_on_initial = bool(mon_cfg.get("notify_on_initial_stock", True))

        # 模組初始化
        self.dispatcher = ScraperDispatcher(timeout=mon_cfg.get("request_timeout", 10))
        state_file = mon_cfg.get("state_file", "state.json")
        self.tracker = StateTracker(state_file=state_file, notify_on_initial_stock=self.notify_on_initial)

        self.last_heartbeat_date: Optional[str] = self.tracker.state.get("last_heartbeat_date")

    def load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"找不到設定檔: {self.config_path}，請複製 config.example.yaml 為 config.yaml")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f) or {}

    def get_targets(self) -> List[dict]:
        targets = self.config.get("targets", [])
        return [t for t in targets if t.get("enabled", True)]

    def check_all_once(self, is_manual: Optional[bool] = None) -> List[ProductInfo]:
        """執行一輪完整的商品庫存巡檢"""
        from datetime import timezone, timedelta

        targets = self.get_targets()
        logger.info(f"開始執行本輪巡檢，共監控 {len(targets)} 項商品...")
        results = []
        notifications_sent = 0

        for idx, target in enumerate(targets, 1):
            url = target.get("url", "").strip()
            name = target.get("name", "未命名商品")
            logger.info(f"[{idx}/{len(targets)}] 檢查中: {name} ({url})")

            try:
                info = self.dispatcher.check(target)
                results.append(info)

                # 格式化狀態顯示
                status_emoji = "✅" if info.status == StockStatus.IN_STOCK else "❌"
                price_str = f"NT$ {info.price}" if info.price is not None else "未標價"
                logger.info(f"  --> {status_emoji} [{info.status.value}] {info.title} | 售價: {price_str}")

                # 判斷是否觸發推播
                if self.tracker.should_notify(target, info):
                    logger.info(f"  🔔 觸發 LINE 補貨推播通知: {info.title}")
                    self.notifier.send_stock_alert(info)
                    notifications_sent += 1

            except Exception as e:
                logger.error(f"檢查商品發生例外: {name} - {e}")

            # 目標間隨機微延遲 0.8~1.5 秒
            if idx < len(targets):
                time.sleep(random.uniform(0.8, 1.5))

        logger.info(f"本輪巡檢完成！共檢查 {len(results)} 項商品，發送 {notifications_sent} 則補貨通知。")

        # 判斷是否為手動巡檢
        if is_manual is None:
            is_manual = (
                os.environ.get("IS_MANUAL_RUN", "").lower() in ("true", "1") or
                os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
            )

        # 1. 若手動觸發且本輪無任何原價現貨 ➔ 發送手動巡檢完成回報！
        if is_manual and notifications_sent == 0:
            logger.info("手動巡檢完成但無原價現貨，發送手動完成回報卡片...")
            self.notifier.send_digest_report(total_monitored=len(targets), is_manual=True)

        # 2. 檢查每日早上 09:00 安心日報 (以台灣時間 UTC+8 計算)
        tz_tw = timezone(timedelta(hours=8))
        now_tw = datetime.now(tz_tw)
        today_str = now_tw.strftime("%Y-%m-%d")

        if now_tw.hour == 9 and self.last_heartbeat_date != today_str:
            logger.info(f"觸發每日早上 09:00 安心日報 (台灣時間 {now_tw.strftime('%H:%M')})...")
            self.notifier.send_digest_report(total_monitored=len(targets), is_manual=False)
            self.last_heartbeat_date = today_str
            self.tracker.state["last_heartbeat_date"] = today_str
            self.tracker.save_state()

        return results

    def check_heartbeat(self):
        """檢查是否達到每日心跳回報時間"""
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        today_str = now.strftime("%Y-%m-%d")

        if current_time_str == self.heartbeat_time and self.last_heartbeat_date != today_str:
            logger.info(f"觸發每日心跳健康回報 ({self.heartbeat_time})...")
            active_count = len(self.get_targets())
            self.notifier.send_heartbeat(active_count)
            self.last_heartbeat_date = today_str

    def run_daemon(self):
        """24 小時不間斷背景監控迴圈"""
        logger.info("==================================================")
        logger.info("⚡ 戰鬥陀螺X 缺貨有貨即時監控系統啟動")
        logger.info(f"🕒 輪詢基準週期: {self.interval} 秒 (+隨機浮動 {self.jitter_min}~{self.jitter_max} 秒)")
        logger.info(f"💚 每日心跳回報: {self.heartbeat_time}")
        logger.info("==================================================")

        try:
            while True:
                # 重新載入設定檔，支援動態熱更新商品清單（免重啟容器）
                try:
                    self.load_config()
                except Exception as e:
                    logger.warning(f"重新載入設定檔失敗: {e}")

                self.check_all_once()
                self.check_heartbeat()

                # 計算下一次檢查等待時間（加入隨機 Jitter 防被擋）
                sleep_seconds = self.interval + random.randint(self.jitter_min, self.jitter_max)
                logger.info(f"休眠等待 {sleep_seconds} 秒後進行下一輪巡檢...\n")
                time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            logger.info("使用者中斷監控程式，正在退出...")
