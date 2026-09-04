# EKS 계층 - 성적 등록 nginx 이미지
FROM nginx:1.27-alpine

COPY default.conf /etc/nginx/conf.d/default.conf
COPY score.html   /usr/share/nginx/html/score.html

RUN mkdir -p /var/log/app

EXPOSE 80
