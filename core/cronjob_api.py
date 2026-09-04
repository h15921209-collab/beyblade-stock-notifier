import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class CronJobOrgClient:
    """cron-job.org 官方 REST API 用戶端"""
    BASE_URL = "https://api.cron-job.org"

    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def test_connection(self) -> bool:
        """測試 API Key 是否有效"""
        jobs = self.list_jobs()
        return jobs is not None

    def list_jobs(self) -> Optional[List[Dict[str, Any]]]:
        """列出帳號下所有 Cron Job"""
        url = f"{self.BASE_URL}/jobs"
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200:
                return r.json().get("jobs", [])
            logger.error(f"cron-job.org list_jobs 失敗 ({r.status_code}): {r.text}")
        except Exception as e:
            logger.error(f"cron-job.org 連線異常: {e}")
        return None

    def find_beyblade_job(self) -> Optional[Dict[str, Any]]:
        """自動尋找名稱含有陀螺或 beyblade 的排程任務"""
        jobs = self.list_jobs()
        if not jobs:
            return None
        for j in jobs:
            title = j.get("title", "").lower()
            if "陀螺" in title or "beyblade" in title:
                return j
        # 若找不到特定關鍵字，則回傳第一個任務
        return jobs[0] if jobs else None

    def update_job_schedule(self, job_id: int, interval_minutes: int) -> bool:
        """
        將任務排程更新為指定分鐘間隔 (5, 10, 15, 30, 60)
        """
        url = f"{self.BASE_URL}/jobs/{job_id}"
        if interval_minutes >= 60:
            minutes = [0]
        else:
            minutes = list(range(0, 60, interval_minutes))

        payload = {
            "job": {
                "schedule": {
                    "minutes": minutes,
                    "hours": [-1],
                    "mdays": [-1],
                    "months": [-1],
                    "wdays": [-1]
                }
            }
        }
        try:
            r = requests.patch(url, headers=self.headers, json=payload, timeout=10)
            if r.status_code == 200:
                logger.info(f"成功將 cron-job.org 任務 {job_id} 更新為每 {interval_minutes} 分鐘 (minutes: {minutes})")
                return True
            else:
                logger.error(f"更新 cron-job.org 失敗 ({r.status_code}): {r.text}")
        except Exception as e:
            logger.error(f"更新 cron-job.org 異常: {e}")
        return False
