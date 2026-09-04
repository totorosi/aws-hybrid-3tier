# EC2 계층 - Nginx 이미지
FROM nginx:1.27-alpine

# 기본 설정을 우리가 작성한 리버스 프록시 설정으로 교체
COPY default.conf /etc/nginx/conf.d/default.conf

# 사이트 시작 파일
COPY index.html /usr/share/nginx/html/index.html

EXPOSE 80
