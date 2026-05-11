# 🍿 사무실 간식 요청 앱 / Office Snack Request App

A bilingual (Korean/English) internal web app for employees to request office snacks and drinks. Admins can view, filter, and export all requests.

---

## 📁 Project Structure

```
snack-app/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── Procfile            # Railway/Heroku start command
├── railway.toml        # Railway config
├── .env.example        # Environment variable template
├── .gitignore
└── templates/
    ├── base.html       # Shared layout (header, lang toggle)
    ├── index.html      # User-facing request form
    ├── admin_login.html
    └── admin.html      # Admin dashboard
```

---

## 🚀 Railway Deployment

### 1. Push to GitHub

```bash
cd snack-app
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USER/snack-app.git
git push -u origin main
```

### 2. Create Railway Project

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub Repo
2. Select your `snack-app` repo
3. Railway will auto-detect Python and build with Nixpacks

### 3. Set Environment Variables

In Railway dashboard → your service → **Variables**, add:

| Variable | Value | Required |
|---|---|---|
| `SECRET_KEY` | A long random string (e.g. UUID) | ✅ Yes |
| `ADMIN_PASSWORD` | Your chosen admin password | ✅ Yes |
| `SERPAPI_KEY` | Your SerpAPI key | Recommended |
| `DATABASE_PATH` | `/data/requests.db` (if using volume) | Optional |

> `PORT` is set automatically by Railway — do not add it.

### 4. (Recommended) Add a Persistent Volume

By default, SQLite data is lost when Railway redeploys your app.

To persist data:
1. Railway dashboard → your service → **Volumes**
2. Add a volume mounted at `/data`
3. Set `DATABASE_PATH=/data/requests.db` in Variables

### 5. Generate a Domain

Railway dashboard → your service → **Settings** → **Networking** → Generate Domain

---

## 🔑 Environment Variables Reference

```env
SECRET_KEY=some-long-random-string-here
ADMIN_PASSWORD=your_secure_password
SERPAPI_KEY=your_serpapi_api_key
DATABASE_PATH=requests.db
```

---

## 🔍 Product Search: SerpAPI

This app uses **SerpAPI** (Google Shopping engine) for product search.

- Sign up at https://serpapi.com
- Free plan: **100 searches/month**
- Paid plans start at $50/month for 5,000 searches

Without a key, the app shows placeholder demo products (useful for testing the UI).

### Why not scrape directly?

| Method | Stability | Legal risk |
|---|---|---|
| Direct Naver/Coupang scraping | ❌ Breaks often | ⚠️ ToS violation |
| SerpAPI (Google Shopping) | ✅ Stable | ✅ OK (they handle it) |
| Google Custom Search API | ✅ Stable | ✅ OK (but images only via CSE) |
| Naver Search API (공식) | ✅ Stable | ✅ OK |

### Alternative: Naver Shopping API (Korean products)

If you want Korean-focused results, you can use the **Naver Developers Shopping API**:

1. Register at https://developers.naver.com
2. Create an app → enable "Shopping" API
3. Replace `search_products()` in `app.py` with:

```python
def search_products_naver(query):
    headers = {
        "X-Naver-Client-Id": os.environ["NAVER_CLIENT_ID"],
        "X-Naver-Client-Secret": os.environ["NAVER_CLIENT_SECRET"],
    }
    resp = requests.get(
        "https://openapi.naver.com/v1/search/shop.json",
        params={"query": query, "display": 12, "sort": "sim"},
        headers=headers, timeout=10
    )
    items = resp.json().get("items", [])
    return [{
        "product_name": item["title"].replace("<b>", "").replace("</b>", ""),
        "brand": item.get("brand", ""),
        "price": f"₩{int(item['lprice']):,}" if item.get("lprice") else "",
        "image_url": item.get("image", ""),
        "product_url": item.get("link", ""),
        "source": "Naver Shopping",
    } for item in items]
```

---

## 💻 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy env file
cp .env.example .env
# Edit .env with your values

# Run
python app.py
```

App runs at http://localhost:5000

---

## 🔐 Admin Access

- URL: `/admin`
- Protected by `ADMIN_PASSWORD` environment variable
- Default (if not set): `admin123` — **change this before deploying!**

Features:
- View all requests with product images
- Filter by name or product
- Export all requests as CSV
- Delete individual requests

---

## ⚠️ Limitations

1. **SQLite on Railway**: Data resets on redeploy unless you use a Volume (see above)
2. **SerpAPI free tier**: 100 searches/month. For heavier use, upgrade or switch to Naver API
3. **No authentication for users**: Any employee can submit requests under any name — this is intentional for simplicity (internal use only)
4. **Image hosting**: Product images are loaded from external URLs (SerpAPI thumbnails); they may occasionally fail to load

---

## 🛠 Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (via Python's built-in `sqlite3`)
- **Product search**: SerpAPI (Google Shopping)
- **Deployment**: Railway (Nixpacks, Gunicorn)
- **Frontend**: Vanilla HTML/CSS/JS (no framework needed)
- **Fonts**: Noto Sans KR + Space Mono (Google Fonts)
