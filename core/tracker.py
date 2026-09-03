import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from scrapers.base import ProductInfo, StockStatus

logger = logging.getLogger(__name__)

class StateTracker:
    def __init__(self, state_file: str = "state.json", notify_on_initial_stock: bool = True):
        self.state_file = state_file
        self.notify_on_initial_stock = notify_on_initial_stock
        self.state: Dict[str, Dict[str, Any]] = {}
        self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
                logger.info(f"已自 {self.state_file} 載入 {len(self.state)} 筆歷史監控紀錄")
            except Exception as e:
                logger.warning(f"讀取狀態檔失敗，使用空白狀態: {e}")
                self.state = {}
        else:
            self.state = {}

    def save_state(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"儲存狀態檔失敗: {e}")

    def should_notify(self, target: dict, info: ProductInfo) -> bool:
        """
        判斷是否應該觸發 LINE 推播：
        1. 當前狀態必須為 IN_STOCK
        2. 若有設定最高金額 (max_price)，價格不得超過
        3. 僅在「初次檢測有貨」或「由缺貨/其他狀態 變更為 現貨」時通知
        4. 持續有貨則不重複推播
        """
        if info.status != StockStatus.IN_STOCK:
            # 更新為非有貨狀態，供後續補貨比對
            self._update_record(info.url, info.status)
            return False

        # 價格上限過濾
        max_price = target.get("max_price")
        if max_price is not None and info.price is not None:
            if info.price > float(max_price):
                logger.info(f"[{info.title}] 現貨價格 NT$ {info.price} 超過自訂上限 NT$ {max_price}，忽略推播")
                self._update_record(info.url, info.status)
                return False

        key = info.url
        record = self.state.get(key)

        if record is None:
            # 首次檢測
            self._update_record(key, info.status)
            if self.notify_on_initial_stock:
                logger.info(f"[{info.title}] 首次檢測即有現貨！觸發推播")
                return True
            else:
                logger.info(f"[{info.title}] 首次檢測有現貨（因設定略過首次推播）")
                return False

        last_status = record.get("last_status")

        # 核心防重複判斷：只有上一次是缺貨 (或未知/異常)，現在變成現貨，才推播
        if last_status != StockStatus.IN_STOCK.value and info.status == StockStatus.IN_STOCK:
            logger.info(f"[{info.title}] 偵測到補貨！({last_status} -> IN_STOCK)，觸發推播")
            self._update_record(key, info.status)
            return True

        # 持續有貨
        logger.debug(f"[{info.title}] 持續有現貨中，維持沉默防洗版")
        self._update_record(key, info.status)
        return False

    def _update_record(self, key: str, status: StockStatus):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if key not in self.state:
            self.state[key] = {
                "first_seen": now_str,
                "last_status": status.value,
                "last_updated": now_str,
            }
        else:
            self.state[key]["last_status"] = status.value
            self.state[key]["last_updated"] = now_str
        self.save_state()
