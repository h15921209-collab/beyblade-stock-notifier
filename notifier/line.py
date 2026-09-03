import logging
from datetime import datetime
from typing import Optional, Dict, Any
import requests
from scrapers.base import ProductInfo

logger = logging.getLogger(__name__)

class LineNotifier:
    PUSH_API_URL = "https://api.line.me/v2/bot/message/push"

    def __init__(self, channel_access_token: str, user_id: str):
        self.channel_access_token = channel_access_token.strip()
        self.user_id = user_id.strip()

    def is_configured(self) -> bool:
        return bool(self.channel_access_token and self.user_id)

    def _get_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.channel_access_token}"
        }

    def send_push(self, messages: list) -> bool:
        """發送 LINE 推播訊息"""
        if not self.is_configured():
            logger.warning("LINE 未設定 Channel Access Token 或 User ID，跳過推播")
            return False

        payload = {
            "to": self.user_id,
            "messages": messages
        }

        try:
            resp = requests.post(
                self.PUSH_API_URL,
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )
            if resp.status_code == 200:
                logger.info(f"LINE 推播發送成功！(接收者: {self.user_id[:6]}...)")
                return True
            else:
                logger.error(f"LINE 推播失敗 (HTTP {resp.status_code}): {resp.text}")
                return False
        except Exception as e:
            logger.error(f"LINE 推播連線異常: {e}")
            return False

    def send_stock_alert(self, info: ProductInfo) -> bool:
        """發送戰鬥陀螺X 補貨通知（含一鍵直接購買搶購連結）"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        price_text = f"NT$ {int(info.price):,}" if info.price is not None else "依賣場標示"
        qty_text = f"庫存剩餘約 {info.stock_qty} 件" if info.stock_qty else "現貨上架可購買"

        # 優先建構美觀的 Flex Message 卡片
        flex_bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": "#E60012",
                "paddingAll": "15px",
                "contents": [
                    {
                        "type": "text",
                        "text": "⚡ 戰鬥陀螺X 補貨現貨！",
                        "weight": "bold",
                        "color": "#FFFFFF",
                        "size": "lg"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"🏪 {info.platform_name}",
                                "size": "xs",
                                "color": "#888888",
                                "weight": "bold"
                            }
                        ]
                    },
                    {
                        "type": "text",
                        "text": info.title,
                        "weight": "bold",
                        "size": "md",
                        "wrap": True
                    },
                    {
                        "type": "separator"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {"type": "text", "text": "售價", "size": "sm", "color": "#555555", "flex": 2},
                                    {"type": "text", "text": price_text, "size": "lg", "color": "#E60012", "weight": "bold", "flex": 5}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {"type": "text", "text": "狀態", "size": "sm", "color": "#555555", "flex": 2},
                                    {"type": "text", "text": f"✅ {qty_text}", "size": "sm", "color": "#008800", "weight": "bold", "flex": 5}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {"type": "text", "text": "時間", "size": "xs", "color": "#999999", "flex": 2},
                                    {"type": "text", "text": now_str, "size": "xs", "color": "#999999", "flex": 5}
                                ]
                            }
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "color": "#E60012",
                        "height": "sm",
                        "action": {
                            "type": "uri",
                            "label": "🛒 立即前往搶購",
                            "uri": info.direct_buy_url
                        }
                    }
                ]
            }
        }

        # 備援純文字訊息
        fallback_text = (
            f"⚡【戰鬥陀螺X 補貨現貨通知！】⚡\n\n"
            f"🏪 通路：{info.platform_name}\n"
            f"🌀 商品：{info.title}\n"
            f"💰 售價：{price_text}\n"
            f"📦 狀態：✅ {qty_text}\n\n"
            f"🛒 一鍵直達搶購連結：\n{info.direct_buy_url}\n\n"
            f"⏱️ 查報時間：{now_str}"
        )

        messages = [
            {
                "type": "flex",
                "altText": f"⚡ 戰鬥陀螺X 補貨現貨！{info.title} - {price_text}",
                "contents": flex_bubble
            }
        ]

        success = self.send_push(messages)
        if not success:
            # 若 Flex Message 被拒，嘗試純文字備援
            logger.info("Flex 推播失敗，轉為純文字發送備援...")
            return self.send_push([{"type": "text", "text": fallback_text}])
        return True

    def send_digest_report(self, total_monitored: int, is_manual: bool = False) -> bool:
        """發送未找到原價陀螺時的安心日報 / 手動巡檢完成回報"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        report_title = "手動巡檢完成回報" if is_manual else "每日安心巡檢日報"
        header_color = "#1E293B" if is_manual else "#0F172A"

        flex_bubble = {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "backgroundColor": header_color,
                "paddingAll": "16px",
                "contents": [
                    {
                        "type": "text",
                        "text": f"🌀 戰鬥陀螺X {report_title}",
                        "color": "#38BDF8",
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "text",
                        "text": f"回報時間: {now_str}",
                        "color": "#94A3B8",
                        "size": "xs",
                        "margin": "xs"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "md",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {"type": "text", "text": "監控品項", "color": "#64748B", "size": "sm", "flex": 2},
                                    {"type": "text", "text": f"共 {total_monitored} 款官方正版", "wrap": True, "color": "#0F172A", "size": "sm", "flex": 4, "weight": "bold"}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {"type": "text", "text": "巡檢通路", "color": "#64748B", "size": "sm", "flex": 2},
                                    {"type": "text", "text": "麗嬰國際 / 反斗城 / PChome 等", "wrap": True, "color": "#0F172A", "size": "sm", "flex": 4}
                                ]
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "spacing": "sm",
                                "contents": [
                                    {"type": "text", "text": "原價現貨", "color": "#64748B", "size": "sm", "flex": 2},
                                    {"type": "text", "text": "暫無 (全數缺貨或黃牛溢價中)", "wrap": True, "color": "#EF4444", "size": "sm", "flex": 4, "weight": "bold"}
                                ]
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "backgroundColor": "#F8FAFC",
                        "cornerRadius": "8px",
                        "paddingAll": "10px",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "🛡️ 雲端虛擬機 24H 定時巡檢在線！一有「官方原價+10%內現貨」立即搶購推播！",
                                "color": "#475569",
                                "size": "xs",
                                "wrap": True
                            }
                        ]
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "uri",
                            "label": "📱 開啟手機管理後台",
                            "uri": "https://beyblade-stock.streamlit.app/"
                        },
                        "color": "#0284C7"
                    }
                ]
            }
        }

        fallback_text = (
            f"🌀【戰鬥陀螺X {report_title}】\n\n"
            f"⏱️ 時間：{now_str}\n"
            f"🎯 監控：共 {total_monitored} 款官方正版陀螺\n"
            f"🔍 結果：各大官方通路目前「暫無原價現貨」（全數缺貨或黃牛溢價中）\n"
            f"🛡️ 狀態：雲端 24H 巡邏守護中，一有正版原價補貨立即推播！\n\n"
            f"👉 手機後台：https://beyblade-stock.streamlit.app/"
        )

        messages = [
            {
                "type": "flex",
                "altText": f"🌀 戰鬥陀螺X {report_title}：目前暫無原價現貨，持續蹲守中！",
                "contents": flex_bubble
            }
        ]
        success = self.send_push(messages)
        if not success:
            return self.send_push([{"type": "text", "text": fallback_text}])
        return True

    def send_heartbeat(self, total_monitored: int) -> bool:
        """發送每日存活心跳回報（相容舊接口）"""
        return self.send_digest_report(total_monitored, is_manual=False)

    def send_test_message(self) -> bool:
        """發送連線驗證測試訊息"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = (
            f"🎉【戰鬥陀螺X 通知測試成功】\n\n"
            f"您的 LINE Messaging API 已成功串接！\n"
            f"當監控的 7 大正版通路有戰鬥陀螺補貨時，將會第一時間發送推播及一鍵購買按鈕到此處。\n\n"
            f"⏱️ 測試時間：{now_str}"
        )
        return self.send_push([{"type": "text", "text": msg}])
