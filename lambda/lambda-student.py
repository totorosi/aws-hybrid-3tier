"""
서버리스 계층 - 교육생 정보 조회 Lambda

student.html 의 검색 기능이 호출한다.
DB 접속은 RDS Proxy 를 경유하며, 접속 정보는 이 Lambda 의 환경 변수에 둔다.

경로:  ANY /student/list        전체 목록 + 과정 목록
       ANY /student/list?name=홍&class_idx=1    필터 조회

막혔던 두 가지 (해결 방법을 여기 남겨둔다):

 1) pymysql 은 RDS Proxy 의 caching_sha2_password 클라이언트 인증을 통과하지 못한다.
    (1045 Access denied — MariaDB 클라이언트는 되는데 pymysql 만 실패)
    -> 프록시의 ClientPasswordAuthType 을 MYSQL_NATIVE_PASSWORD 로 설정해야 한다.
       이 값은 클라이언트↔프록시 구간만 정하며, 프록시↔DB 는 그대로 caching_sha2 를 쓴다.

 2) TLS 를 켜는 옵션은 ssl={"ssl": {}} 가 아니라 ssl_ca 다.
    ssl={"ssl": {}} 은 조용히 무시되어 평문으로 붙는다.
    확인 방법: SHOW SESSION STATUS LIKE 'Ssl_cipher'  (@@ssl_cipher 는 서버 설정값이라 무의미)
"""

import json
import os

import pymysql
from pymysql.cursors import DictCursor

def _find_ca():
    """RDS 루트 인증서 번들을 찾는다.
    레이어에 두면 /opt/python/, 함수에 함께 넣으면 /var/task/ 에 놓인다."""
    for p in (
        "/opt/python/rds-global-bundle.pem",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "rds-global-bundle.pem"),
    ):
        if os.path.exists(p):
            return p
    return None


CA_PATH = _find_ca()

DB = {
    "host": os.environ["DB_HOST"],          # RDS Proxy 엔드포인트
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASS"],
    "database": os.environ.get("DB_NAME", "testdb"),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "connect_timeout": 5,
}

# ssl_ca 를 주면 TLS 로 붙고 인증서 검증까지 한다.
if os.environ.get("DB_SSL", "1") == "1" and CA_PATH:
    DB["ssl_ca"] = CA_PATH

HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
}

SQL_STUDENTS = """
    SELECT  s.idx        AS no
    ,       c.class_name AS class_name
    ,       s.name       AS name
    ,       s.email      AS email
    ,       s.location   AS location
    FROM        tstudent s
    INNER JOIN  tclass   c ON s.class_idx = c.idx
    WHERE       (%(class_idx)s IS NULL OR s.class_idx = %(class_idx)s)
    AND         (%(name)s      IS NULL OR s.name LIKE %(like)s)
    ORDER BY    s.idx
"""

SQL_CLASSES = "SELECT idx, class_name FROM tclass ORDER BY idx"


def _respond(status, body):
    return {
        "statusCode": status,
        "headers": HEADERS,
        "body": json.dumps(body, ensure_ascii=False),
    }


def lambda_handler(event, context):
    qs = event.get("queryStringParameters") or {}
    name = (qs.get("name") or "").strip() or None
    raw_class = (qs.get("class_idx") or "").strip()

    class_idx = None
    if raw_class:
        try:
            class_idx = int(raw_class)
        except ValueError:
            return _respond(400, {"error": "class_idx 는 정수여야 합니다."})

    params = {
        "class_idx": class_idx,
        "name": name,
        "like": f"%{name}%" if name else None,
    }

    try:
        conn = pymysql.connect(**DB)
    except Exception as e:
        # 접속 실패 원인을 화면에서 바로 알 수 있게 그대로 노출한다 (실습용)
        return _respond(500, {"error": "DB 접속 실패", "detail": str(e)})

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(SQL_CLASSES)
                classes = cur.fetchall()
                cur.execute(SQL_STUDENTS, params)
                students = cur.fetchall()
    except Exception as e:
        return _respond(500, {"error": "조회 실패", "detail": str(e)})

    return _respond(200, {
        "classes": classes,
        "students": students,
        "count": len(students),
        "via": "RDS Proxy",
    })
