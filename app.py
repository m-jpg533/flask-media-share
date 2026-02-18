# from flask import Flask, request, jsonify, render_template
# import sqlite3
# import requests
# import os
# import math

# app = Flask(__name__)

# # ===== 資料庫路徑（關鍵修正）=====
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_PATH = os.path.join(BASE_DIR, "location.db")

# # ===== 初始化資料庫 =====
# def init_db():
    # conn = sqlite3.connect(DB_PATH)
    # c = conn.cursor()
    # c.execute("""
    # CREATE TABLE IF NOT EXISTS location (
        # id INTEGER PRIMARY KEY AUTOINCREMENT,
        # lat REAL,
        # lon REAL,
        # time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # )
    # """)
    # conn.commit()
    # conn.close()

# init_db()

# # ===== LINE 設定 =====
# LINE_TOKEN = "你的LINE_CHANNEL_ACCESS_TOKEN"
# LINE_USER_ID = "你的LINE_USER_ID"   # ⚠ 不是 Google API key

# # ===== 家的座標 =====
# HOME_LAT = 25.1166
# HOME_LON = 121.5166
# HOME_RADIUS = 100  # 公尺

# notified = False
# @app.route("/webhook", methods=["POST"])
# def webhook():
    # data = request.json
    # user_id = data["events"][0]["source"]["userId"]
    # print("LINE_USER_ID =", user_id)
    # return "ok"

# # ===== 計算距離 =====
# def distance_m(lat1, lon1, lat2, lon2):
    # R = 6371000
    # phi1 = math.radians(lat1)
    # phi2 = math.radians(lat2)
    # dphi = math.radians(lat2 - lat1)
    # dlambda = math.radians(lon2 - lon1)

    # a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    # return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

# # ===== LINE 推播 =====
# def send_line(msg):
    # headers = {
        # "Authorization": f"Bearer {LINE_TOKEN}",
        # "Content-Type": "application/json"
    # }
    # data = {
        # "to": LINE_USER_ID,
        # "messages": [{"type": "text", "text": msg}]
    # }
    # requests.post(
        # "https://api.line.me/v2/bot/message/push",
        # headers=headers,
        # json=data
    # )

# # ===== 首頁地圖 =====
# @app.route("/")
# def index():
    # return render_template("map.html")

# # ===== 接收定位 =====
# @app.route("/update", methods=["POST"])
# def update():
    # global notified

    # lat = float(request.json["lat"])
    # lon = float(request.json["lon"])

    # conn = sqlite3.connect(DB_PATH)
    # c = conn.cursor()
    # c.execute("INSERT INTO location(lat, lon) VALUES (?,?)", (lat, lon))
    # conn.commit()
    # conn.close()

    # dist = distance_m(lat, lon, HOME_LAT, HOME_LON)

    # # 到家通知一次
    # if dist < HOME_RADIUS and not notified:
        # map_url = f"https://maps.google.com/?q={lat},{lon}"
        # send_line("已到家 📍\n" + map_url)
        # notified = True

    # return jsonify({"status": "ok"})

# # ===== 取得最新位置 =====
# @app.route("/latest")
# def latest():
    # conn = sqlite3.connect(DB_PATH)
    # c = conn.cursor()
    # c.execute("SELECT lat, lon FROM location ORDER BY id DESC LIMIT 1")
    # row = c.fetchone()
    # conn.close()

    # if row:
        # return jsonify({"lat": row[0], "lon": row[1]})
    # return jsonify({"lat": None, "lon": None})

# # ===== Render 必備 =====
# if __name__ == "__main__":
    # port = int(os.environ.get("PORT", 5000))
    # app.run(host="0.0.0.0", port=port)



from flask import Flask, request, jsonify, render_template
import sqlite3
import os
import math

app = Flask(__name__)

# ==============================
# 資料庫設定（保證可建立）
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(BASE_DIR, exist_ok=True)
DB_PATH = os.path.join(BASE_DIR, "location.db")

print("使用資料庫:", DB_PATH)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS location (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lat REAL,
        lon REAL,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ==============================
# 家的座標（你之前提供）
# ==============================
HOME_LAT = 25.1166
HOME_LON = 121.5166
HOME_RADIUS = 100  # 公尺

notified = False

# ==============================
# 計算距離
# ==============================
def distance_m(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

# ==============================
# 首頁（Google 地圖）
# ==============================
@app.route("/")
def index():
    return render_template("map.html")

# ==============================
# 手機上傳定位
# ==============================
@app.route("/update", methods=["POST"])
def update():
    global notified

    data = request.json
    lat = float(data["lat"])
    lon = float(data["lon"])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO location(lat, lon) VALUES (?,?)", (lat, lon))
    conn.commit()
    conn.close()

    # 到家判斷（只標記，不推播）
    dist = distance_m(lat, lon, HOME_LAT, HOME_LON)
    arrived = False

    if dist < HOME_RADIUS and not notified:
        notified = True
        arrived = True

    return jsonify({
        "status": "ok",
        "arrived_home": arrived,
        "distance": int(dist)
    })

# ==============================
# 取得最新定位（地圖用）
# ==============================
@app.route("/latest")
def latest():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT lat, lon FROM location ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()

    if row:
        return jsonify({"lat": row[0], "lon": row[1]})
    return jsonify({"lat": None, "lon": None})

# ==============================
# 手機定位頁
# ==============================
@app.route("/driver")
def driver():
    return render_template("driver.html")

# ==============================
# Render / 本機啟動
# ==============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
