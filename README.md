# 🌀 戰鬥陀螺X (Beyblade X) 缺貨補貨即時 LINE 通知軟體

專為戰鬥陀螺X玩家打造的 24 小時正版通路自動庫存監控系統。一旦偵測到缺貨商品補貨或重新上架，第一時間將通知推播至您的手機 LINE，訊息內附「🛒 立即前往搶購」直達連結，助您秒速入手原價正版商品！

---

## 🌟 核心特色

- 🛡️ **鎖定 7 大官方與授權正版通路**：
  - **麗嬰國際官方購物網** (`shop.funbox.com.tw`) - 台灣總代理原廠商城
  - **蝦皮商城 麗嬰國際官方旗艦店** (`shopee.tw/funbox_toys`) - 官方直營
  - **Momo 購物網 Funbox 館** (`momoshop.com.tw`) - 官方品牌專館
  - **PChome 24h TAKARA TOMY 館** (`24h.pchome.com.tw`) - 官方授權專區
  - **玩具反斗城台灣官網** (`toysrus.com.tw`) - 連鎖玩具實體龍頭線上商城
  - **酷比樂玩具專賣店** (`preorder.amuzinc.com`) - 老牌正版模型玩具商
  - **誠品線上** (`eslite.com`) - 誠品線上玩具/戰鬥陀螺專區
- ⚡ **直接購買直達搶購連結**：推播卡片附帶「一鍵開賣場」按鈕，省去手動開啟瀏覽器搜尋的時間。
- 📱 **LINE Messaging API 整合**：支援精美 Flex Message 卡片（包含通路名、品名、金額、庫存狀態與搶購按鈕）。
- 🔇 **狀態變更防洗版機制**：僅在「缺貨 ➔ 現貨」瞬間推播 1 次；持續有貨期間自動保持沉默，節省 LINE 免費推播額度。
- 💚 **每日存活心跳回報 (Heartbeat)**：每天固定時間（如 09:00）自動回報服務正常運作與監控商品數，確認背景監控未中斷。
- 🐳 **多元部署支援**：
  - **Docker Compose**：支援家用 NAS (Synology/QNAP)、VPS 或本機 24 小時高頻常駐巡檢，Volume 掛載 `config.yaml` 改網址即時生效。
  - **GitHub Actions**：提供定時排程腳本，免開主機即可在雲端免費巡檢。

---

## 📁 專案結構

```
beyblade-stock-notifier/
├── config.example.yaml          # 設定檔範本（含各通路網址示範）
├── config.yaml                  # 實際運行設定檔（由範本複製）
├── requirements.txt             # 依賴套件
├── main.py                      # 程式進入點 (CLI)
├── Dockerfile                   # Docker 容器封裝
├── docker-compose.yml           # Docker Compose 編排
├── .github/workflows/
│   └── monitor.yml              # GitHub Actions 定時排程工作流程
├── core/
│   ├── engine.py                # 主監控輪詢引擎與心跳排程
│   └── tracker.py               # 狀態機與防重複洗版機制
├── notifier/
│   └── line.py                  # LINE Messaging API 推播封裝
├── scrapers/                    # 7 大平台爬蟲適配器
│   ├── base.py                  # 基礎抽象類別與資料結構
│   ├── dispatcher.py            # 網址自動分派路由器
│   ├── funbox.py                # 麗嬰國際官方商城解析器
│   ├── pchome.py                # PChome 24h 解析器
│   ├── toysrus.py               # 玩具反斗城台灣解析器
│   ├── momo.py                  # Momo 購物網解析器
│   ├── shopee.py                # 蝦皮商城旗艦店解析器
│   ├── kubi.py                  # 酷比樂解析器
│   └── eslite.py                # 誠品線上解析器
└── tests/                       # 完整單元測試套件
```

---

## 🔑 LINE Messaging API 快速設定指引 (完全免費)

> 註：LINE Notify 已於 2025 年終止服務。本專案採用官方長期維護的 **LINE Messaging API (LINE 官方帳號 / Bot)**，每月提供 200 則免費推播訊息（對於補貨通知綽綽有餘）。

1. 前往 [LINE Developers Console](https://developers.line.biz/console/) 並以個人 LINE 帳號登入。
2. 點擊 **Create a new provider**（名稱可自訂，如：`BeybladeMonitor`）。
3. 點擊 **Create a Messaging API channel**：
   - **Channel name**：自訂名稱（例如：`戰鬥陀螺補貨通知`）。
   - **Channel description**：自訂簡介。
   - **Category / Subcategory**：隨意選擇。
4. 建立後，進入該 Channel 的 **Messaging API** 分頁：
   - 掃描頁面上的 **QR code**，將您的通知機器人加為 LINE 好友。
   - 拉到最下方找到 **Channel access token (long-lived)**，點擊 **Issue** 產生 Token 並複製。
5. 進入 **Basic settings** 分頁，拉到最下方找到 **Your user ID**（以 `U` 開頭的字串），複製下來。
6. 將這兩串金鑰填入 `config.yaml` 中的 `line_notify` 區塊即可！

---

## 🚀 快速開始

### 1. 安裝環境依賴

```bash
# 複製設定檔範本
cp config.example.yaml config.yaml

# 安裝 Python 依賴
pip install -r requirements.txt
```

### 2. 編輯 `config.yaml`

開啟 `config.yaml` 填入您的 LINE 金鑰與想監控的商品網址：

```yaml
line_notify:
  channel_access_token: "YOUR_LINE_CHANNEL_ACCESS_TOKEN"
  user_id: "YOUR_LINE_USER_ID"

monitor:
  interval_seconds: 60      # 輪詢間隔基準（秒）
  jitter_min_seconds: 5     # 隨機延遲最小秒數
  jitter_max_seconds: 15    # 隨機延遲最大秒數
  heartbeat_time: "09:00"   # 每日存活回報時間

targets:
  - name: "BX-25 戰鬥陀螺X專業收納包"
    url: "https://24h.pchome.com.tw/prod/DEASR1-B900H2BID"
    max_price: 1300
    enabled: true
```

### 3. 功能驗證與測試

```bash
# 測試 LINE 推播連線（手機將收到一則測試卡片）
python main.py --test-line

# 測試單一商品網址解析
python main.py --test-url "https://24h.pchome.com.tw/prod/DEASR1-B900H2BID"

# 執行單次完整巡檢（檢查所有 targets 後退出）
python main.py --check-once

# 執行單元測試套件
python -m pytest -v
```

---

## 🐳 Docker / NAS 部署 (推薦 24 小時高頻常駐)

非常適合部屬於家中 Synology / QNAP NAS、Raspberry Pi 或 VPS 雲端主機：

```bash
# 啟動容器 (背景執行)
docker compose up -d

# 查看即時監控日誌
docker compose logs -f

# 停止容器
docker compose down
```

> **提示**：因為 `docker-compose.yml` 已經掛載了 `./config.yaml`，您隨時可以在宿主機上新增或刪除商品網址，監控程式每輪巡檢都會自動讀取最新網址，**完全不需重新 build 映像檔**！

---

## ☁️ GitHub Actions 免主機部署 (零成本雲端排程)

若您手邊沒有 24 小時開著的電腦或 NAS，可利用 GitHub Actions 免費定時執行：

1. 將本專案 Push 到您自己的 **GitHub 私人倉庫 (Private Repository)**。
2. 進入倉庫的 **Settings** ➔ **Secrets and variables** ➔ **Actions**。
3. 點擊 **New repository secret** 新增以下兩個機密變數：
   - `LINE_CHANNEL_ACCESS_TOKEN`
   - `LINE_USER_ID`
4. 系統將會自動依據 `.github/workflows/monitor.yml` 設定每 15 分鐘自動在雲端執行一次巡檢，缺貨變現貨時推播通知到您的 LINE！
