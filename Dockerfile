FROM python:3.11-slim

# 設定時區為台北時區
ENV TZ=Asia/Taipei
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app

# 先複製依賴套件清單進行快取安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製原始碼
COPY . .

# 預設執行常駐背景監控
CMD ["python", "main.py", "--daemon"]
