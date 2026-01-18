import os
from pathlib import Path
import streamlit as st
import pandas as pd

# -----------------------
# 1) 경로 안정화 (상대경로 이슈 방지)
# -----------------------
BASE_DIR = Path(__file__).resolve().parent

# -----------------------
# 2) DB 드라이버 호환 (MySQLdb 없으면 PyMySQL로)
# -----------------------
def get_mysql_connector():
    """
    Prefer MySQLdb(mysqlclient). If unavailable (common on Windows venv),
    fallback to PyMySQL (pure python).
    Returns: (module, connect_function)
    """
    try:
        import MySQLdb  # mysqlclient
        return MySQLdb, MySQLdb.connect
    except Exception:
        try:
            import pymysql
            return pymysql, pymysql.connect
        except Exception as e:
            raise RuntimeError(
                "MySQL 드라이버가 없습니다. 아래 중 하나를 설치하세요:\n"
                "1) pip install pymysql\n"
                "2) pip install mysqlclient (윈도우는 빌드툴 필요할 수 있음)\n"
            ) from e

DB_MODULE, mysql_connect = get_mysql_connector()

# -----------------------
# 3) 환경변수로 설정(친구 PC에서도 안전)
#    - 너가 하드코딩해둔 host/user/passwd 같은 거 때문에 친구가 안 될 수도 있어서
#    - 기본값은 너가 쓰던 값으로 두되, 친구는 .env나 시스템 환경변수로 바꿀 수 있게
# -----------------------
DB_CONFIG = dict(
    host=os.getenv("DB_HOST", "175.196.76.209"),
    user=os.getenv("DB_USER", "sk25_team3"),
    passwd=os.getenv("DB_PASS", "Encore7278!"),
    db=os.getenv("DB_NAME", "team3"),
    charset="utf8mb4",
)

# PyMySQL은 passwd 대신 password를 쓰는 경우가 많아서 안전하게 맞춰줌
def normalize_db_config(cfg: dict) -> dict:
    cfg = cfg.copy()
    if "passwd" in cfg and "password" not in cfg:
        # pymysql.connect는 password 인자를 받음
        cfg["password"] = cfg["passwd"]
    return cfg

# -----------------------
# 4) DB 연결 함수 (에러 메시지 친절하게)
# -----------------------
def get_conn():
    try:
        cfg = normalize_db_config(DB_CONFIG)
        # MySQLdb는 password 키가 있어도 무시하고 passwd를 씀. 둘 다 넣어도 크게 문제 없음.
        return mysql_connect(**cfg)
    except Exception as e:
        st.error(
            "DB 연결 실패!\n\n"
            "가능한 원인:\n"
            "- 친구 PC에서 DB 서버 접근이 차단(방화벽/네트워크)\n"
            "- DB 계정/비밀번호/DB명/host가 다름\n"
            "- 서버가 외부접속 허용 안 됨\n\n"
            f"에러: {type(e).__name__}: {e}"
        )
        raise

# -----------------------
# 5) 예시 쿼리 함수
# -----------------------
def read_table(table_name: str) -> pd.DataFrame:
    conn = get_conn()
    try:
        query = f"SELECT * FROM `{table_name}`"
        df = pd.read_sql(query, conn)
        return df
    finally:
        try:
            conn.close()
        except Exception:
            pass

# -----------------------
# 6) Streamlit UI
# -----------------------
st.set_page_config(page_title="FAQ", layout="wide")
st.title("FAQ")

table = st.text_input("읽을 테이블 이름", value="car_model")
if st.button("불러오기"):
    df = read_table(table)
    st.dataframe(df, use_container_width=True)