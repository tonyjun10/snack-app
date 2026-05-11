import os
import sqlite3
import requests
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, Response, g
)
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

DATABASE = os.environ.get("DATABASE_PATH", "requests.db")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")


# ─── Database ────────────────────────────────────────────────────────────────

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS snack_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_name TEXT NOT NULL,
                search_term TEXT NOT NULL,
                product_name TEXT NOT NULL,
                brand TEXT,
                price TEXT,
                image_url TEXT,
                product_url TEXT,
                source TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        db.commit()


# ─── Auth ─────────────────────────────────────────────────────────────────────

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ─── Product Search ───────────────────────────────────────────────────────────

def search_products(query, lang="ko"):
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        return _demo_products(query)
    try:
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        }
        resp = requests.get(
            "https://openapi.naver.com/v1/search/shop.json",
            headers=headers,
            params={"query": query, "display": 12, "sort": "sim"},
            timeout=10,
        )
        data = resp.json()
        results = []
        for item in data.get("items", []):
            name = item.get("title", "").replace("<b>", "").replace("</b>", "")
            price_raw = item.get("lprice", "")
            price = f"₩{int(price_raw):,}" if price_raw else ""
            results.append({
                "product_name": name,
                "brand": item.get("brand", "") or item.get("maker", ""),
                "price": price,
                "image_url": item.get("image", ""),
                "product_url": item.get("link", ""),
                "source": "Naver Shopping",
            })
        return results
    except Exception as e:
        print(f"Naver search error: {e}")
        return _demo_products(query)


def _demo_products(query):
    return [
        {"product_name": f"{query} - 샘플 제품 A (500ml)", "brand": "데모 브랜드", "price": "₩1,500",
         "image_url": "https://placehold.co/200x200/f0f4ff/6366f1?text=🧃", "product_url": "#", "source": "데모"},
        {"product_name": f"{query} - 샘플 제품 B (340ml × 6캔)", "brand": "데모 브랜드 B", "price": "₩8,900",
         "image_url": "https://placehold.co/200x200/f0f4ff/6366f1?text=🥤", "product_url": "#", "source": "데모"},
        {"product_name": f"{query} - 샘플 제품 C (대용량 1L)", "brand": "데모 브랜드 C", "price": "₩2,200",
         "image_url": "https://placehold.co/200x200/f0f4ff/6366f1?text=🫙", "product_url": "#", "source": "데모"},
    ]


# ─── Routes: User ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    lang = request.args.get("lang", session.get("lang", "ko"))
    session["lang"] = lang
    return render_template("index.html", lang=lang)

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    lang = session.get("lang", "ko")
    if not query:
        return jsonify([])
    return jsonify(search_products(query, lang))

@app.route("/confirm", methods=["POST"])
def confirm():
    data = request.get_json()
    name = data.get("name", "").strip()
    items = data.get("items", [])  # list of {search_term, product}

    if not name or not items:
        return jsonify({"ok": False, "error": "missing fields"}), 400

    db = get_db()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    saved = 0
    for item in items:
        product = item.get("product", {})
        if not product.get("product_name"):
            continue
        db.execute(
            """INSERT INTO snack_requests
               (requester_name, search_term, product_name, brand, price,
                image_url, product_url, source, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name,
                item.get("search_term", ""),
                product.get("product_name", ""),
                product.get("brand", ""),
                product.get("price", ""),
                product.get("image_url", ""),
                product.get("product_url", ""),
                product.get("source", ""),
                ts,
            ),
        )
        saved += 1
    db.commit()
    return jsonify({"ok": True, "count": saved})


# ─── Routes: Admin ────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        error = "비밀번호가 틀렸습니다. / Wrong password."
    return render_template("admin_login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    rows = db.execute("SELECT * FROM snack_requests ORDER BY timestamp DESC").fetchall()
    return render_template("admin.html", rows=rows)

@app.route("/admin/export")
@admin_required
def admin_export():
    db = get_db()
    rows = db.execute("SELECT * FROM snack_requests ORDER BY timestamp DESC").fetchall()
    def generate():
        cols = ["id", "requester_name", "search_term", "product_name",
                "brand", "price", "image_url", "product_url", "source", "timestamp"]
        yield ",".join(cols) + "\n"
        for row in rows:
            yield ",".join(f'"{str(row[c]).replace(chr(34), chr(39))}"' for c in cols) + "\n"
    return Response(generate(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=snack_requests.csv"})

@app.route("/admin/delete/<int:req_id>", methods=["POST"])
@admin_required
def admin_delete(req_id):
    db = get_db()
    db.execute("DELETE FROM snack_requests WHERE id = ?", (req_id,))
    db.commit()
    return redirect(url_for("admin_dashboard"))


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
