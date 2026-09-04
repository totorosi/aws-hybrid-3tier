"""
EKS 계층 - 성적 등록 API

score.html 이 호출한다. DB 는 RDS Proxy 를 경유한다.

경로 (nginx 가 /score/ 를 떼고 넘겨준다)
    GET  /init      과정 목록 + 학생 목록
    GET  /list      등록된 성적 전체
    POST /register  성적 등록 (있으면 갱신)

주의 (9번에서 겪은 것과 동일)
  1) 프록시의 ClientPasswordAuthType 이 MYSQL_NATIVE_PASSWORD 여야 한다.
     caching_sha2_password 로 두면 pymysql 이 1045 로 거부당한다.
  2) TLS 를 켜는 옵션은 ssl={"ssl": {}} 가 아니라 ssl_ca 다.

로그는 /var/log/app/fastapi.log 에 쓴다.
이 경로는 hostPath 볼륨이라 파드가 아니라 워커노드의 디스크에 남는다 (요구사항).
"""

import logging
import os
from pathlib import Path

import pymysql
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pymysql.cursors import DictCursor

# ── 로깅: 워커노드에 파일로 기록 ────────────────────────────
LOG_DIR = Path(os.getenv("LOG_DIR", "/var/log/app"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "fastapi.log", encoding="utf-8"),
        logging.StreamHandler(),          # kubectl logs 로도 보이게
    ],
)
log = logging.getLogger("score-api")

app = FastAPI(title="std15-test score API")


def _find_ca():
    for p in ("/opt/python/rds-global-bundle.pem",
              "/app/rds-global-bundle.pem"):
        if os.path.exists(p):
            return p
    return None


CA_PATH = _find_ca()

DB = {
    "host": os.environ["DB_HOST"],            # RDS Proxy 엔드포인트
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASS"],
    "database": os.getenv("DB_NAME", "testdb"),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "connect_timeout": 5,
}
if os.getenv("DB_SSL", "1") == "1" and CA_PATH:
    DB["ssl_ca"] = CA_PATH


def get_conn():
    return pymysql.connect(**DB)


class ScoreIn(BaseModel):
    student_idx: int = Field(..., ge=1)
    kor: int = Field(..., ge=0, le=100)
    eng: int = Field(..., ge=0, le=100)
    mat: int = Field(..., ge=0, le=100)


@app.get("/health")
def health():
    with get_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            return cur.fetchone()


@app.get("/init")
def init():
    """과정 목록과 학생 목록. 화면의 두 select 를 채운다."""
    with get_conn() as c:
        with c.cursor() as cur:
            cur.execute("SELECT idx, class_name FROM tclass ORDER BY idx")
            classes = cur.fetchall()
            cur.execute(
                "SELECT idx, name, class_idx FROM tstudent ORDER BY idx"
            )
            students = cur.fetchall()
    log.info("init: classes=%d students=%d", len(classes), len(students))
    return {"classes": classes, "students": students}


@app.get("/list")
def score_list():
    """등록된 성적 전체. 화면 하단 표를 채운다."""
    sql = """
        SELECT  s.idx        AS no
        ,       c.class_name AS class_name
        ,       s.name       AS name
        ,       t.kor        AS kor
        ,       t.eng        AS eng
        ,       t.mat        AS mat
        ,       ROUND((t.kor + t.eng + t.mat) / 3, 1) AS avg
        FROM        tscore   t
        INNER JOIN  tstudent s ON t.student_idx = s.idx
        INNER JOIN  tclass   c ON s.class_idx   = c.idx
        ORDER BY    s.idx
    """
    with get_conn() as c:
        with c.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    log.info("list: %d rows", len(rows))
    return rows


@app.post("/register")
def register(body: ScoreIn):
    """성적 등록. 같은 학생의 기존 행이 있으면 갱신한다.

    tscore 에 student_idx UNIQUE 제약이 없어서 그냥 INSERT 하면
    같은 학생의 행이 계속 쌓인다. 그래서 존재 확인 후 분기한다.
    """
    try:
        with get_conn() as c:
            with c.cursor() as cur:
                cur.execute(
                    "SELECT idx FROM tstudent WHERE idx = %s",
                    (body.student_idx,),
                )
                if cur.fetchone() is None:
                    raise HTTPException(404, "존재하지 않는 교육생입니다.")

                cur.execute(
                    "SELECT idx FROM tscore WHERE student_idx = %s",
                    (body.student_idx,),
                )
                row = cur.fetchone()

                if row:
                    cur.execute(
                        "UPDATE tscore SET kor=%s, eng=%s, mat=%s "
                        "WHERE student_idx=%s",
                        (body.kor, body.eng, body.mat, body.student_idx),
                    )
                    action = "updated"
                else:
                    cur.execute(
                        "INSERT INTO tscore (student_idx, kor, eng, mat) "
                        "VALUES (%s, %s, %s, %s)",
                        (body.student_idx, body.kor, body.eng, body.mat),
                    )
                    action = "inserted"
            c.commit()
    except HTTPException:
        raise
    except Exception as e:
        log.error("register failed: %s", e)
        raise HTTPException(500, f"등록 실패: {e}")

    log.info(
        "register %s: student_idx=%s kor=%s eng=%s mat=%s",
        action, body.student_idx, body.kor, body.eng, body.mat,
    )
    return {"result": action, "student_idx": body.student_idx}
