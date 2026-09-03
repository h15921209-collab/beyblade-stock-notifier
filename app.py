import os
import yaml
import streamlit as st
from datetime import datetime
from scrapers import ScraperDispatcher, StockStatus
from notifier import LineNotifier
from core.github_sync import GitHubSync
import discover_targets

from core.msrp import get_official_price_and_limit

# 頁面配置
st.set_page_config(
    page_title="戰鬥陀螺X 雲端監控管理後台",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 載入設定檔
CONFIG_PATH = "config.yaml"
GITHUB_REPO = "h15921209-collab/beyblade-stock-notifier"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "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")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_config(cfg: dict, sync_github: bool = True):
    # 儲存到本地
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
    # 同步至 GitHub
    if sync_github and GITHUB_TOKEN:
        gh = GitHubSync(token=GITHUB_TOKEN, repo=GITHUB_REPO)
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            yaml_content = f.read()
        gh.update_file_content("config.yaml", yaml_content, "ui: update targets and config via web manager")

# 登入與 PIN 碼驗證
ADMIN_PIN = os.environ.get("ADMIN_PIN", "8888")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🌀 戰鬥陀螺X 監控管理後台")
    st.markdown("請輸入管理員 PIN 碼解鎖系統（預設 PIN: `8888`）：")
    pin_input = st.text_input("管理 PIN 碼", type="password")
    if st.button("🔓 登入後台", type="primary"):
        if pin_input == ADMIN_PIN:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("PIN 碼錯誤，請重新輸入！")
    st.stop()

# 進入主頁面
cfg = load_config()
targets = cfg.get("targets", [])
monitor_cfg = cfg.get("monitor", {})
line_cfg = cfg.get("line_notify", {})

st.sidebar.title("🌀 戰鬥陀螺X 監控中心")
st.sidebar.markdown(f"**目前監控總數**：`{len(targets)}` 款")
active_count = sum(1 for t in targets if t.get("enabled", True))
st.sidebar.markdown(f"**啟用中商品**：`{active_count}` 款")
st.sidebar.markdown(f"**雲端排程**：每 `{monitor_cfg.get('interval_seconds', 900) // 60}` 分鐘巡檢一次")
st.sidebar.markdown("---")

if st.sidebar.button("🔒 登出後台"):
    st.session_state.authenticated = False
    st.rerun()

# 頁面標題與快速狀態
st.title("🌀 戰鬥陀螺X 缺貨有貨監控中心")
st.markdown("隨時隨地用手機管理監控網址、更新頻率與觸發即時雲端巡檢！")

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 商品清單與維護",
    "➕ 新增商品網址",
    "⏱️ 巡檢頻率與設定",
    "⚡ 雲端快捷操作"
])

# ------------------------------------------------------------------------------
# Tab 1: 商品清單與維護
# ------------------------------------------------------------------------------
with tab1:
    st.subheader(f"目前監控清單 ({len(targets)} 款)")
    search_kw = st.text_input("🔍 搜尋商品名稱或網址關鍵字（例如：BX-35、反斗城、收納包）：", "")

    col_btn1, col_btn2, col_btn3 = st.columns([1.5, 2, 2.5])
    with col_btn1:
        if st.button("💾 儲存並同步至雲端 GitHub", type="primary"):
            save_config(cfg, sync_github=True)
            st.success("✅ 設定已成功儲存並同步推送到 GitHub 雲端！")
    with col_btn2:
        if st.button("🛡️ 一鍵重算為「官方原價+10%」"):
            for t in targets:
                _, max_p = get_official_price_and_limit(t.get("name", ""), fallback_price=t.get("max_price"))
                t["max_price"] = max_p
            save_config(cfg, sync_github=True)
            st.success("🎉 全部商品已全數設定為「官方原價 + 10%」上限！")
            st.rerun()

    filtered_indices = []
    for idx, t in enumerate(targets):
        name = t.get("name", "")
        url = t.get("url", "")
        if search_kw.lower() in name.lower() or search_kw.lower() in url.lower():
            filtered_indices.append(idx)

    st.caption(f"符合搜尋條件共 {len(filtered_indices)} 款商品")

    for idx in filtered_indices:
        t = targets[idx]
        off_p, _ = get_official_price_and_limit(t.get("name", ""), fallback_price=t.get("max_price"))
        with st.expander(f"{'✅' if t.get('enabled', True) else '⏸️'} {t.get('name', '未命名商品')} (官方原價: NT$ {off_p} | 上限: NT$ {t.get('max_price')})"):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                t["name"] = st.text_input("品名", value=t.get("name", ""), key=f"name_{idx}")
                t["url"] = st.text_input("網址", value=t.get("url", ""), key=f"url_{idx}")
                st.markdown(f"[🛒 點此前賣場]({t.get('url')})")
            with c2:
                t["max_price"] = st.number_input("最高接受售價 (NT$)", value=int(t.get("max_price", 1500)), step=50, key=f"price_{idx}")
                t["enabled"] = st.checkbox("啟用監控", value=bool(t.get("enabled", True)), key=f"en_{idx}")
            with c3:
                st.write("")
                st.write("")
                if st.button("🗑️ 刪除", key=f"del_{idx}"):
                    targets.pop(idx)
                    save_config(cfg, sync_github=True)
                    st.toast("已刪除該商品！")
                    st.rerun()

# ------------------------------------------------------------------------------
# Tab 2: 新增商品網址
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("➕ 新增戰鬥陀螺X商品網址")
    st.markdown("支援 7 大通路（麗嬰國際、蝦皮商城、Momo、PChome 24h、玩具反斗城、酷比樂、誠品線上）：")

    new_url = st.text_input("貼入商品網址 (URL):", "")
    detected_info = None

    if new_url and st.button("🔍 自動解析商品資訊"):
        dispatcher = ScraperDispatcher()
        with st.spinner("正在連線解析商品頁面..."):
            detected_info = dispatcher.check({"url": new_url})
            if detected_info.status != StockStatus.ERROR:
                st.success(f"辨識成功！通路：{detected_info.platform_name} | 現貨狀態: {detected_info.status.value}")
                st.session_state["prefill_name"] = detected_info.title
                off_p, max_p = get_official_price_and_limit(detected_info.title, fallback_price=detected_info.price)
                st.session_state["prefill_price"] = max_p
                st.info(f"💡 官方參考原價: NT$ {off_p} ➔ 自動鎖定防黃牛上限 (+10%): **NT$ {max_p}**")
            else:
                st.warning(f"自動辨識未獲取完整資料: {detected_info.error_msg}")

    with st.form("add_product_form"):
        prod_name = st.text_input("商品自訂名稱:", value=st.session_state.get("prefill_name", ""))
        prod_max_price = st.number_input("最高價格上限 (NT$):", value=st.session_state.get("prefill_price", 1500), step=50)
        submitted = st.form_submit_button("➕ 確認加入監控清單", type="primary")

        if submitted:
            if not new_url.strip():
                st.error("請填寫商品網址！")
            else:
                targets.insert(0, {
                    "name": prod_name.strip() or "戰鬥陀螺X新商品",
                    "url": new_url.strip(),
                    "max_price": prod_max_price,
                    "enabled": True
                })
                save_config(cfg, sync_github=True)
                st.success(f"🎉 成功新增：{prod_name}，已同步推送到 GitHub 雲端！")
                st.session_state.pop("prefill_name", None)
                st.session_state.pop("prefill_price", None)
                st.rerun()

# ------------------------------------------------------------------------------
# Tab 3: 巡檢頻率與設定
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("⏱️ 雲端巡檢頻率設定")
    current_mins = monitor_cfg.get("interval_seconds", 900) // 60
    if current_mins not in [5, 10, 15, 30, 60]:
        current_mins = 15

    freq_options = [5, 10, 15, 30, 60]
    chosen_mins = st.select_slider(
        "選擇巡檢間隔時間（分鐘）：",
        options=freq_options,
        value=current_mins,
        format_func=lambda x: f"每 {x} 分鐘"
    )

    st.info(f"💡 目前設定：GitHub Actions 雲端伺服器將會**每 {chosen_mins} 分鐘**自動執行一次全系列 63 款商品巡檢。")

    st.subheader("📱 LINE 通知憑證")
    token_val = st.text_input("Channel Access Token", value=line_cfg.get("channel_access_token", ""), type="password")
    user_id_val = st.text_input("User ID", value=line_cfg.get("user_id", ""))

    if st.button("💾 儲存並更新雲端排程 (Update Cron)", type="primary"):
        monitor_cfg["interval_seconds"] = chosen_mins * 60
        line_cfg["channel_access_token"] = token_val
        line_cfg["user_id"] = user_id_val
        save_config(cfg, sync_github=True)

        # 更新 GitHub Actions 的 .github/workflows/monitor.yml cron
        if GITHUB_TOKEN:
            gh = GitHubSync(token=GITHUB_TOKEN, repo=GITHUB_REPO)
            success = gh.update_workflow_cron(chosen_mins)
            if success:
                st.success(f"🎉 成功將雲端 GitHub Actions 巡檢頻率更新為每 {chosen_mins} 分鐘一次！")
            else:
                st.warning("已更新 config.yaml，但更新 workflow cron 時回傳異常，請檢查權限。")
        else:
            st.success("已更新本地設定檔！")

# ------------------------------------------------------------------------------
# Tab 4: 雲端快捷操作
# ------------------------------------------------------------------------------
with tab4:
    st.subheader("⚡ 雲端快捷手動操作")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🚀 立即雲端巡檢")
        st.caption("不等 15 分鐘，現在就讓 GitHub Actions 在雲端虛擬機立即掃描一次！")
        if st.button("▶️ 立即觸發雲端檢查"):
            gh = GitHubSync(token=GITHUB_TOKEN, repo=GITHUB_REPO)
            with st.spinner("正在向 GitHub 傳送觸發指令..."):
                if gh.trigger_monitor_now():
                    st.success("✅ 雲端巡檢指令已發送！請稍候 30 秒至 1 分鐘查看結果。")
                else:
                    st.error("❌ 觸發失敗，請確認 Token 權限。")

    with col2:
        st.markdown("#### 📲 LINE 測試卡片")
        st.caption("立即發送一則測試訊息到手機，確認 LINE Bot 是否在線。")
        if st.button("📨 發送測試通知"):
            notifier = LineNotifier(line_cfg.get("channel_access_token", ""), line_cfg.get("user_id", ""))
            with st.spinner("發送中..."):
                if notifier.send_test_message():
                    st.success("✅ 測試訊息已送出，請看手機 LINE！")
                else:
                    st.error("❌ 發送失敗，請確認 Token 與 User ID。")

    with col3:
        st.markdown("#### 🔍 自動掃描新商品")
        st.caption("自動連線 PChome、反斗城、麗嬰國際，搜尋最新上市的陀螺。")
        if st.button("🔎 全通路搜尋新陀螺"):
            with st.spinner("全通路深度掃描中，請稍候約 10 秒..."):
                added, total = discover_targets.run_discovery()
                save_config(load_config(), sync_github=True)
                st.success(f"🎉 掃描完成！新發現 {added} 款商品，目前總共監控 {total} 款！")
                st.rerun()

    st.markdown("---")
    st.subheader("📊 最近雲端巡檢紀錄 (GitHub Actions Runs)")
    gh = GitHubSync(token=GITHUB_TOKEN, repo=GITHUB_REPO)
    runs = gh.get_recent_runs(limit=5)
    if runs:
        for r in runs:
            status_icon = "🟢" if r.get("conclusion") == "success" else ("🟡" if r.get("status") == "in_progress" else "⚪")
            st.markdown(f"{status_icon} **{r.get('name')}** - 狀態: `{r.get('status')}` ({r.get('conclusion') or '執行中'}) | 啟動時間: `{r.get('created_at')}` [查看雲端即時 Log]({r.get('html_url')})")
    else:
        st.caption("暫無歷史紀錄")
