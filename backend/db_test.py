import pymysql

conn = pymysql.connect(
    host="175.196.76.209",
    port=3306,
    user="sk25_team6",
    password="Encore7281!",
    database="team6",
    charset="utf8mb4"
)

with conn.cursor() as cursor:
    cursor.execute("SELECT 1;")
    print("DB 연결 성공:", cursor.fetchone())

conn.close()
