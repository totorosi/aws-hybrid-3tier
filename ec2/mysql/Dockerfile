# EC2 계층 - MySQL 이미지
# 요구사항: 컨테이너는 ECR 에 push 한 이미지만 사용한다
# -> Docker Hub 의 mysql 을 그대로 쓰지 않고, init.sql 을 담아 직접 빌드한다.
# 버전 고정: mysql:8.4 는 롤링 태그라 재빌드 시점에 따라 8.4.x 가 바뀐다.
# 2번 RDS 와 동일한 8.4.10 으로 맞춘다.
FROM mysql:8.4.10

# 한글 깨짐 방지 - init.sql 실행 전에 문자셋이 잡혀 있어야 한다.
# /etc/my.cnf 가 !includedir /etc/mysql/conf.d/ 를 포함한다.
COPY charset.cnf /etc/mysql/conf.d/charset.cnf

# /docker-entrypoint-initdb.d/ 에 놓인 .sql 은 컨테이너 최초 기동 시 자동 실행된다.
# testdb 생성 / 테이블 3개 / vinfo 뷰까지 여기서 만들어진다.
COPY init.sql /docker-entrypoint-initdb.d/10-init.sql

EXPOSE 3306
