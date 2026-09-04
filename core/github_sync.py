import base64
import re
import logging
from typing import Optional, Tuple, List, Dict, Any
import requests

logger = logging.getLogger(__name__)

class GitHubSync:
    def __init__(self, token: str, repo: str = "h15921209-collab/beyblade-stock-notifier"):
        self.token = token.strip()
        self.repo = repo.strip()
        self.base_url = f"https://api.github.com/repos/{self.repo}"

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Beyblade-Streamlit-Manager"
        }

    def get_file_content(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """取得 GitHub 倉庫中的檔案內容與 SHA"""
        url = f"{self.base_url}/contents/{file_path}"
        try:
            r = requests.get(url, headers=self._get_headers(), timeout=10)
            if r.status_code == 200:
                data = r.json()
                content = base64.b64decode(data.get("content", "")).decode("utf-8")
                sha = data.get("sha")
                return content, sha
        except Exception as e:
            logger.error(f"取得檔案失敗 ({file_path}): {e}")
        return None, None

    def update_file_content(self, file_path: str, new_content: str, message: str) -> bool:
        """更新或建立 GitHub 倉庫中的檔案"""
        url = f"{self.base_url}/contents/{file_path}"
        _, sha = self.get_file_content(file_path)

        encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": message,
            "content": encoded,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        try:
            r = requests.put(url, headers=self._get_headers(), json=payload, timeout=10)
            if r.status_code in (200, 201):
                logger.info(f"GitHub 檔案更新成功: {file_path}")
                return True
            else:
                logger.error(f"GitHub 檔案更新失敗 ({r.status_code}): {r.text}")
                return False
        except Exception as e:
            logger.error(f"更新 GitHub 檔案異常: {e}")
            return False

    def update_workflow_cron(self, interval_minutes: int) -> bool:
        """動態修改 GitHub Actions 巡檢 cron 週期"""
        file_path = ".github/workflows/monitor.yml"
        content, sha = self.get_file_content(file_path)
        if not content:
            return False

        new_cron = f"- cron: '*/{interval_minutes} * * * *'" if interval_minutes < 60 else "- cron: '0 * * * *'"
        updated_content = re.sub(r"- cron: ['\"][^'\"]+['\"]", new_cron, content)
        return self.update_file_content(file_path, updated_content, f"ci: update monitor frequency to {interval_minutes} minutes")

    def trigger_monitor_now(self, trigger_source: str = "manual") -> bool:
        """一鍵觸發 GitHub Actions 立即巡檢"""
        url = f"{self.base_url}/actions/workflows/monitor.yml/dispatches"
        try:
            payload = {
                "ref": "main",
                "inputs": {
                    "trigger_source": trigger_source
                }
            }
            r = requests.post(url, headers=self._get_headers(), json=payload, timeout=10)
            return r.status_code == 204
        except Exception as e:
            logger.error(f"觸發 Actions 失敗: {e}")
            return False

    def get_recent_runs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """取得最近幾次雲端巡檢紀錄"""
        url = f"{self.base_url}/actions/runs?per_page={limit}"
        try:
            r = requests.get(url, headers=self._get_headers(), timeout=10)
            if r.status_code == 200:
                return r.json().get("workflow_runs", [])
        except Exception as e:
            logger.error(f"查詢 Actions 紀錄失敗: {e}")
        return []
