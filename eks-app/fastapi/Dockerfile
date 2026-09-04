# EKS 계층 - 성적 등록 fastAPI 이미지
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# RDS Proxy 에 TLS 로 붙기 위한 루트 인증서 번들
COPY rds-global-bundle.pem /app/rds-global-bundle.pem
COPY main.py .

# 로그 디렉터리 (hostPath 볼륨이 여기 마운트된다)
RUN mkdir -p /var/log/app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
