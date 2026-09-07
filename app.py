import os
import yaml
import streamlit as st
from datetime import datetime
from scrapers import ScraperDispatcher, StockStatus
from notifier import LineNotifier
from core.github_sync import GitHubSync
import discover_targets

from core.msrp import get_official_price_and_limit
from core.smart_finder import smart_cross_search, sanitize_url, verify_official_channel, get_current_hot_picks_data, is_authentic_beyblade_product
from core.meta_updater import update_hot_picks_from_sources
from core.cronjob_api import CronJobOrgClient

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
cfg = load_config()
ADMIN_PIN = str(os.environ.get("ADMIN_PIN") or cfg.get("admin_pin", "8888")).strip()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🌀 戰鬥陀螺X 監控管理後台")
    st.markdown("請輸入管理員 PIN 碼驗證身分解鎖系統：")
    pin_input = st.text_input("管理 PIN 碼", type="password", placeholder="請輸入 PIN 碼")
    if st.button("🔓 登入後台", type="primary", use_container_width=True):
        if pin_input and pin_input == ADMIN_PIN:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("PIN 碼錯誤，請重新輸入！")
    st.stop()

# 進入主頁面
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

tab1, tab_hot, tab_search, tab3, tab4 = st.tabs([
    "📋 監控清單",
    "🏆 熱門神物（一鍵加入）",
    "🔍 型號搜尋與新增",
    "⏱️ 巡檢頻率",
    "⚡ 雲端快捷"
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
# ------------------------------------------------------------------------------
# Tab 2 (tab_hot): 社群熱門神物情報庫（一鍵加入）
# ------------------------------------------------------------------------------
with tab_hot:
    hot_categories, last_update_time = get_current_hot_picks_data()
    all_picks = [p for items in hot_categories.values() for p in items]

    col_head1, col_head2 = st.columns([3, 2])
    with col_head1:
        st.subheader("🏆 玩家社群與比賽熱門神物情報庫")
        st.caption(f"🕒 情報庫最後更新時間：`{last_update_time}` ｜ 共收錄 {len(all_picks)} 款主流爆款")
    with col_head2:
        st.write("")
        if st.button("🔄 立即連線全網更新情報庫", type="secondary", use_container_width=True):
            with st.spinner("正在連線麗嬰國際、反斗城與社群掃描最新發售型號..."):
                updated_data = update_hot_picks_from_sources()
                if GITHUB_TOKEN:
                    gh = GitHubSync(token=GITHUB_TOKEN, repo=GITHUB_REPO)
                    with open("data/hot_picks.json", "r", encoding="utf-8") as f:
                        gh.update_file_content("data/hot_picks.json", f.read(), "data: update hot picks meta database")
                st.success("🎉 熱門神物清單已成功更新至最新發售情報！")
                st.rerun()

    # 頂部醒目【一鍵全網搜尋追蹤全部熱門神物】
    st.write("")
    if st.button(f"⚡ 🚀 一鍵全網搜尋並追蹤「全部熱門神物」 (共 {len(all_picks)} 款)", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        existing_urls = {t.get("url") for t in targets}
        total_added = 0

        for i, p in enumerate(all_picks):
            m_code = p["model"]
            status_text.markdown(f"正在全通路檢索 **【{m_code}】{p['name']}** 官方正版賣場 ({i+1}/{len(all_picks)})...")
            progress_bar.progress((i + 1) / len(all_picks))
            found = smart_cross_search(m_code)
            for s in found:
                if s["url"] not in existing_urls:
                    targets.insert(0, {
                        "name": s["name"],
                        "url": s["url"],
                        "max_price": s["max_price"],
                        "enabled": True
                    })
                    existing_urls.add(s["url"])
                    total_added += 1

        save_config(cfg, sync_github=True)
        status_text.empty()
        progress_bar.empty()
        st.success(f"🎉 狂賀！已全自動跨各大官方通路檢索完畢，共為您新增 **{total_added} 間官方正版賣場** 進入監控名單！")
        st.rerun()

    st.caption("支援下方個別分類「一鍵全選加入」或自由「勾選批次加入」：")

    # 預設全部展開 (expanded=True)，在手機上無需點擊即可直接看到與操作！
    for cat_name, items in hot_categories.items():
        with st.expander(f"{cat_name} ({len(items)} 款精選)", expanded=True):
            # 最左側滿版醒目主按鈕
            if st.button(f"⚡ ➕ 一鍵追蹤「{cat_name}」全部 ({len(items)} 款)", type="primary", key=f"cat_all_{cat_name}", use_container_width=True):
                existing_urls = {t.get("url") for t in targets}
                cat_added = 0
                with st.spinner(f"正在為【{cat_name}】全網搜尋官方賣場..."):
                    for p in items:
                        found = smart_cross_search(p["model"])
                        for s in found:
                            if s["url"] not in existing_urls:
                                targets.insert(0, {
                                    "name": s["name"],
                                    "url": s["url"],
                                    "max_price": s["max_price"],
                                    "enabled": True
                                })
                                existing_urls.add(s["url"])
                                cat_added += 1
                save_config(cfg, sync_github=True)
                st.success(f"🎉 成功為【{cat_name}】新增 {cat_added} 間官方賣場！")
                st.rerun()

            st.divider()

            selected_in_cat = []
            for idx, pick in enumerate(items):
                p_col_chk, p_col1, p_col2, p_col3 = st.columns([0.5, 3, 2, 1.8])
                with p_col_chk:
                    is_sel = st.checkbox("", value=True, key=f"chk_{cat_name}_{pick['model']}_{idx}")
                    if is_sel:
                        selected_in_cat.append(pick)
                with p_col1:
                    st.markdown(f"**【{pick['model']}】{pick['name']}**")
                    st.caption(f"💡 {pick['desc']}")
                with p_col2:
                    _, max_lim = get_official_price_and_limit(pick['name'], fallback_price=pick['official_price'])
                    st.markdown(f"官方原價: `NT$ {pick['official_price']}`")
                    st.markdown(f"🔒 鎖定上限: **NT$ {max_lim}**")
                with p_col3:
                    if st.button(f"🔎 尋找賣場並追蹤", key=f"hot_{pick['model']}_{idx}"):
                        with st.spinner(f"正在全通路尋找 {pick['model']} 官方賣場..."):
                            found_stores = smart_cross_search(pick["model"])
                            if found_stores:
                                existing_urls = {t.get("url") for t in targets}
                                added = 0
                                for s in found_stores:
                                    if s["url"] not in existing_urls:
                                        targets.insert(0, {
                                            "name": s["name"],
                                            "url": s["url"],
                                            "max_price": s["max_price"],
                                            "enabled": True
                                        })
                                        existing_urls.add(s["url"])
                                        added += 1
                                save_config(cfg, sync_github=True)
                                st.success(f"🎉 成功為【{pick['model']}】新增 {added} 間官方賣場！")
                                st.rerun()
                            else:
                                st.warning(f"各大通路此款極度缺貨下架，暫無現存賣場。")

            if selected_in_cat and len(selected_in_cat) < len(items):
                if st.button(f"☑️ ➕ 批次加入本分類已勾選的 {len(selected_in_cat)} 款神物", type="secondary", key=f"sel_batch_{cat_name}", use_container_width=True):
                    existing_urls = {t.get("url") for t in targets}
                    batch_added = 0
                    with st.spinner(f"正在搜尋勾選的 {len(selected_in_cat)} 款賣場..."):
                        for p in selected_in_cat:
                            found = smart_cross_search(p["model"])
                            for s in found:
                                if s["url"] not in existing_urls:
                                    targets.insert(0, {
                                        "name": s["name"],
                                        "url": s["url"],
                                        "max_price": s["max_price"],
                                        "enabled": True
                                    })
                                    existing_urls.add(s["url"])
                                    batch_added += 1
                    save_config(cfg, sync_github=True)
                    st.success(f"🎉 成功為已勾選款式新增 {batch_added} 間官方賣場！")
                    st.rerun()

# ------------------------------------------------------------------------------
# Tab 3 (tab_search): 型號搜尋與新增網址
# ------------------------------------------------------------------------------
with tab_search:
    st.subheader("🔍 型號搜尋與新增網址")
    st.markdown("支援型號關鍵字跨通路跨搜，以及貼上任意賣場網址自動防偽與防黃牛！")

    sub_s1, sub_s2 = st.tabs([
        "🔍 型號全通路智慧跨搜",
        "🔗 貼入網址智慧解析與防偽"
    ])

    with sub_s1:
        st.markdown("#### 🚀 型號／關鍵字跨官方通路精準檢索")
        st.caption("自動跨麗嬰國際、反斗城、PChome 24h 官方直營比對正版賣場，杜絕假貨與個人賣家！")

        kw_col1, kw_col2 = st.columns([3, 1])
        with kw_col1:
            search_input = st.text_input("輸入型號代碼或中文名稱（例如：BX-35, UX-04, 魔導神杖, 收納包）：", "BX-35")
        with kw_col2:
            st.write("")
            st.write("")
            do_search = st.button("🔎 開始跨通路搜尋", type="primary", use_container_width=True)

        if do_search or "last_search_results" in st.session_state:
            if do_search:
                with st.spinner(f"正在全網檢索 {search_input} 官方正版賣場..."):
                    st.session_state["last_search_results"] = smart_cross_search(search_input)
                    st.session_state["last_search_keyword"] = search_input

            results = st.session_state.get("last_search_results", [])
            kw = st.session_state.get("last_search_keyword", "")
            st.markdown(f"**「{kw}」官方通路檢索結果（共找到 {len(results)} 間官方賣場）：**")

            if results:
                if st.button("➕ 一鍵將以上全部官方賣場加入監控", type="secondary", use_container_width=True):
                    added_num = 0
                    existing_urls = {t.get("url") for t in targets}
                    for r in results:
                        if r["url"] not in existing_urls:
                            targets.insert(0, {
                                "name": r["name"],
                                "url": r["url"],
                                "max_price": r["max_price"],
                                "enabled": True
                            })
                            existing_urls.add(r["url"])
                            added_num += 1
                    save_config(cfg, sync_github=True)
                    st.success(f"🎉 成功批次新增 {added_num} 間官方賣場至監控清單！")
                    st.rerun()

                for idx, item in enumerate(results):
                    with st.container():
                        c_plat, c_info, c_price, c_act = st.columns([1.5, 4, 2, 1.5])
                        with c_plat:
                            st.markdown(f"🏷️ **{item['platform']}**")
                            st.caption(f"`{item['badge']}`")
                        with c_info:
                            st.markdown(f"**[{item['name']}]({item['url']})**")
                        with c_price:
                            st.markdown(f"官方原價: `NT$ {item['official_price']}`")
                            st.markdown(f"🔒 鎖定上限: **NT$ {item['max_price']}**")
                        with c_act:
                            if st.button("➕ 加入", key=f"add_search_{idx}", use_container_width=True):
                                existing_urls = {t.get("url") for t in targets}
                                if item["url"] in existing_urls:
                                    st.warning("此賣場已在清單中！")
                                else:
                                    targets.insert(0, {
                                        "name": item["name"],
                                        "url": item["url"],
                                        "max_price": item["max_price"],
                                        "enabled": True
                                    })
                                    save_config(cfg, sync_github=True)
                                    st.toast(f"已成功加入：{item['name']}")
                                    st.rerun()
                        st.divider()
            else:
                st.info("查無符合官方直營賣場，請嘗試更換型號（如 BX-23、UX-01）或縮短關鍵字。")

    with sub_s2:
        st.markdown("#### 🔗 貼入任意賣場網址（自動淨化、驗證正版與防黃牛）")
        st.caption("自動剔除 FB/Line 垃圾追蹤碼，驗證官方授權店家，並強制鎖定原價+10%上限！")

        raw_input_url = st.text_input("貼入商品網址 (支援包含 fbclid/utm 等複雜連結):", "", key="smart_url_input")

        if raw_input_url:
            clean_url = sanitize_url(raw_input_url)
            if clean_url != raw_input_url.strip():
                st.info(f"✨ 系統已為您自動淨化網址去除追蹤碼：`{clean_url}`")

            is_official, badge_text = verify_official_channel(clean_url)
            if is_official:
                st.success(f"🛡️ 正版驗證通過：{badge_text}")
            else:
                st.warning(badge_text)

            if st.button("🔍 智慧解析賣場即時現貨與定價", type="primary", use_container_width=True):
                dispatcher = ScraperDispatcher()
                with st.spinner("正在連線賣場讀取即時商品資訊..."):
                    detected_info = dispatcher.check({"url": clean_url})
                    if detected_info.status != StockStatus.ERROR:
                        st.session_state["smart_title"] = detected_info.title
                        st.session_state["smart_curr_price"] = detected_info.price or 0
                        off_p, max_p = get_official_price_and_limit(detected_info.title, fallback_price=detected_info.price)
                        st.session_state["smart_off_price"] = off_p
                        st.session_state["smart_max_price"] = max_p
                    else:
                        st.error(f"解析失敗: {detected_info.error_msg}")

        if "smart_title" in st.session_state:
            s_title = st.session_state["smart_title"]
            s_curr_p = st.session_state["smart_curr_price"]
            s_off_p = st.session_state["smart_off_price"]
            s_max_p = st.session_state["smart_max_price"]

            st.write("---")
            st.markdown(f"**商品品名**：`{s_title}`")
            st.markdown(f"**當前賣場標價**：`NT$ {s_curr_p}` ｜ **官方原價 (MSRP)**：`NT$ {s_off_p}`")

            if s_curr_p > s_max_p:
                st.warning(f"⚠️ **黃牛溢價警示**：此賣場當前標價 (NT$ {s_curr_p}) 已大幅溢價！系統將強制將通知上限鎖死為 **NT$ {s_max_p}** (原價+10%)，在原廠補貨降價前絕不發推播打擾！")
            else:
                st.success(f"✅ 價格合規！通知上限自動設定為：**NT$ {s_max_p}** (官方原價+10%)")

            # 三重鋼鐵過濾機制檢驗
            is_valid_beyblade = is_authentic_beyblade_product(s_title)
            if not is_valid_beyblade:
                st.error("🛑 **非戰鬥陀螺商品警示**：此商品經三重鋼鐵過濾檢驗判定為非戰鬥陀螺正版品項（可能為鞋類、飾品、3C零件或非陀螺雜物）。為保持監控庫存純淨度，系統已拒絕收錄！")
            else:
                if st.button("➕ 確認加入監控清單", type="primary", key="confirm_smart_add", use_container_width=True):
                    clean_url = sanitize_url(raw_input_url)
                    targets.insert(0, {
                        "name": s_title,
                        "url": clean_url,
                        "max_price": s_max_p,
                        "enabled": True
                    })
                    save_config(cfg, sync_github=True)
                    st.success(f"🎉 成功新增：{s_title}，已同步推送到 GitHub 雲端！")
                    st.session_state.pop("smart_title", None)
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

    st.info(f"💡 目前設定：系統將會**每 {chosen_mins} 分鐘**精準巡檢全庫 {len(targets)} 款正版商品。")

    st.divider()
    st.subheader("🌐 cron-job.org 精準定時連動")
    st.caption("串接 cron-job.org API，拉動上方滑桿即可同步修改外部精準定時心跳，讓滑桿 100% 真正管用！")

    cronjob_cfg = cfg.setdefault("cronjob_org", {})
    cron_api_key = st.text_input(
        "cron-job.org API Key (從 Console -> Settings -> API Keys 取得)",
        value=cronjob_cfg.get("api_key", ""),
        type="password",
        help="登入 cron-job.org -> 點右上角頭像選 Settings -> API Keys -> Create API Key"
    )

    detected_job_id = cronjob_cfg.get("job_id")
    if cron_api_key:
        client = CronJobOrgClient(cron_api_key)
        jobs = client.list_jobs()
        if jobs:
            st.success(f"✅ 成功連線 cron-job.org！(帳號內共有 {len(jobs)} 個排程任務)")
            job_map = {j["jobId"]: f"{j.get('title', '未命名')} (ID: {j['jobId']})" for j in jobs}
            
            default_index = 0
            job_ids = list(job_map.keys())
            if detected_job_id in job_ids:
                default_index = job_ids.index(detected_job_id)
            else:
                for idx, j_id in enumerate(job_ids):
                    if "陀螺" in job_map[j_id] or "beyblade" in job_map[j_id].lower():
                        default_index = idx
                        break

            chosen_job_id = st.selectbox(
                "選擇要連動的定時任務：",
                options=job_ids,
                index=default_index,
                format_func=lambda x: job_map[x]
            )
            detected_job_id = chosen_job_id
        elif jobs is not None:
            st.warning("已連線但帳號內尚無排程任務，請先建立排程。")
        else:
            st.error("API Key 驗證失敗，請確認是否輸入正確。")

    st.divider()
    st.subheader("🔑 管理員安全 PIN 碼")
    new_pin_val = st.text_input("自訂後台登入 PIN 碼 (登入介面不再提供任何提示)", value=ADMIN_PIN, type="password", placeholder="例如: 9527 或 私人密碼")

    st.divider()
    st.subheader("📱 LINE 通知憑證")
    token_val = st.text_input("Channel Access Token", value=line_cfg.get("channel_access_token", ""), type="password")
    user_id_val = st.text_input("User ID", value=line_cfg.get("user_id", ""))

    if st.button("💾 儲存並更新雲端排程 (Save & Sync)", type="primary", use_container_width=True):
        monitor_cfg["interval_seconds"] = chosen_mins * 60
        line_cfg["channel_access_token"] = token_val
        line_cfg["user_id"] = user_id_val
        cfg["admin_pin"] = new_pin_val.strip() if new_pin_val else "8888"
        cronjob_cfg["api_key"] = cron_api_key
        if detected_job_id:
            cronjob_cfg["job_id"] = detected_job_id

        save_config(cfg, sync_github=True)

        # 1. 更新 GitHub Actions 的 .github/workflows/monitor.yml cron (保底排程)
        if GITHUB_TOKEN:
            gh = GitHubSync(token=GITHUB_TOKEN, repo=GITHUB_REPO)
            gh.update_workflow_cron(chosen_mins)

        # 2. 同步更新 cron-job.org 外部精準定時心跳！
        cron_synced = False
        if cron_api_key and detected_job_id:
            client = CronJobOrgClient(cron_api_key)
            cron_synced = client.update_job_schedule(detected_job_id, chosen_mins)

        if cron_synced:
            st.success(f"🎉 狂賀！已同步將外部定時 (cron-job.org) 與 GitHub 保底排程更新為每 {chosen_mins} 分鐘！滑桿已 100% 真正生效！")
        else:
            st.success(f"✅ 已更新本機與 GitHub 保底排程為每 {chosen_mins} 分鐘！(若填入 cron-job.org API Key 可實現外部全自動秒級連動)")
        st.rerun()

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
