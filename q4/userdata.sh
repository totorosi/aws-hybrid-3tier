#!/bin/bash
# 앱 인스턴스 userdata
# 인스턴스가 부팅되면 서비스가 자동으로 운영되도록 구성한다.
# 로그: /var/log/cloud-init-output.log
#
# 아래 4개 값은 시작 템플릿에서 치환하거나 직접 채운다.
#   AWS_ACCOUNT_ID  12자리 AWS 계정 ID
#   REGION          배포 리전
#   BUCKET          docker-compose.yaml / .env 를 올려 둔 S3 버킷
set -xe

AWS_ACCOUNT_ID="<AWS_ACCOUNT_ID>"
REGION="<REGION>"

BUCKET="<DEPLOY_BUCKET>"

ECR="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
APPDIR=/opt/app

# ── 1) Docker 설치 ─────────────────────────────────────
dnf install -y docker
systemctl enable --now docker
usermod -aG docker ec2-user

# ── 2) Docker Compose v2 (CLI 플러그인) ────────────────
mkdir -p /usr/local/lib/docker/cli-plugins
curl -sL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
     -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# ── 3) ECR 로그인 ──────────────────────────────────────
# 인스턴스 프로파일(std15-test-app-role)의 자격증명을 사용한다.
# 액세스 키를 인스턴스에 두지 않는다.
aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ECR"

# ── 4) S3 에서 compose 파일과 .env 복사 ────────────────
# 인스턴스에 소스는 두지 않는다. compose 파일만 받아 ECR 이미지를 끌어온다.
# .env 는 DB 자격증명을 담으므로 S3 객체를 비공개로 두고 IAM 으로만 읽는다.
mkdir -p $APPDIR
aws s3 cp "s3://$BUCKET/docker-compose.yaml" $APPDIR/docker-compose.yaml --region "$REGION"
aws s3 cp "s3://$BUCKET/.env"                $APPDIR/.env               --region "$REGION"
chmod 600 $APPDIR/.env

# ── 5) 서비스 기동 ─────────────────────────────────────
cd $APPDIR
docker compose -f $APPDIR/docker-compose.yaml up -d

# ── 6) 재부팅 시에도 자동 기동 ─────────────────────────
# compose 의 restart 정책이 동작하려면 docker 데몬이 부팅 시 떠 있어야 한다.
systemctl enable docker
