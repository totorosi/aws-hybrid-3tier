# EC2 계층 - fastAPI 이미지
FROM python:3.12-slim

WORKDIR /app

# 의존성을 먼저 복사해 레이어 캐시를 살린다 (main.py 만 고칠 때 재설치 안 함)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

# Nginx 리버스 프록시 뒤에서 동작하므로 0.0.0.0 으로 바인딩해야 한다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
