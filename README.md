# SNAP Retailer Locator API

API to find the **top K closest SNAP-accepting retailers** from the Historical SNAP Retailer Locator Data (2005–2025), using either **latitude/longitude** or **zip code**.

## Setup

```bash
cd "/Users/muskanmahajan/Snap Finder API"
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: **http://127.0.0.1:8000**
- Interactive docs: **http://127.0.0.1:8000/docs**

## Endpoints

### `GET /retailers/closest`

Returns the top **K** closest retailers. You can specify location in two ways:

**By coordinates (latitude/longitude):**

```text
GET /retailers/closest?lat=61.21&lon=-149.90&k=10
```

**By zip code:**

The API uses the centroid of all retailers in that zip as the reference point, then returns the K closest retailers to that point.

```text
GET /retailers/closest?zip_code=99501&k=10
```

**Query parameters:**

| Parameter   | Type   | Required | Description                                      |
|------------|--------|----------|--------------------------------------------------|
| `lat`      | float  | No*      | Latitude (use together with `lon`)               |
| `lon`      | float  | No*      | Longitude (use together with `lat`)              |
| `zip_code` | string | No*      | Zip code (alternative to `lat`/`lon`)            |
| `k`        | int    | No       | Number of results (default 10, max 100)          |

\* Provide either `lat` and `lon`, or `zip_code`.

**Response:** JSON array of retailer objects, each including store details and `distance_miles` (distance from the given location or zip centroid).

### `GET /health`

Returns service status and whether the store dataset is loaded.

## Data

- **Source:** `Historical SNAP Retailer Locator Data 2005-2025.csv`
- Rows with missing or invalid coordinates (e.g. 0,0) are excluded from distance search.
- Distances are computed with the **Haversine formula** (miles).

---

## Hosting

The app loads the full CSV at startup (~700k rows), so use a platform with **at least 512MB–1GB RAM**. The repo includes a `Procfile` and `runtime.txt` for one-click deploys.

### Deploy on Render (recommended)

1. **Push this repo to GitHub** (include `Historical SNAP Retailer Locator Data 2005-2025.csv` in the repo so Render can see it).
2. Go to [render.com](https://render.com) → **New** → **Web Service** and connect your GitHub repo.
3. Configure the service:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** choose **Starter** ($7/mo) or higher — the free tier has 512MB and may run out of memory loading the CSV. Starter (512MB) usually works; upgrade if you see OOM on deploy.
4. Click **Create Web Service**. Render will build and deploy. Your API URL will be like `https://<your-service-name>.onrender.com`.
5. **First deploy:** Startup can take 30–60 seconds while the CSV loads. Hit `https://<your-service-name>.onrender.com/health` until you see `"stores_loaded": true`. Then use `/docs` for the interactive API.

**Summary:** API base = `https://<your-service-name>.onrender.com`, docs = `https://<your-service-name>.onrender.com/docs`.

### Other options: Railway or Docker

- **Railway:** [railway.app](https://railway.app) → New Project → Deploy from GitHub. It will use the `Procfile`. Add a public domain in Settings → Networking; give the service at least 512MB RAM.
- **Docker:** From the project root run `docker build -t snap-finder-api .` then `docker run -p 8000:8000 snap-finder-api`. Use the image on any VPS (e.g. Fly.io, EC2) and expose port 8000.

### Notes

- **CSV in repo:** The app expects `Historical SNAP Retailer Locator Data 2005-2025.csv` in the **project root**. If you don’t commit the CSV (e.g. due to size), upload it to the host or mount it so it’s at that path when the app starts.
- **Startup time:** Loading ~700k rows can take 30–60 seconds. The `/health` endpoint will report `stores_loaded: true` once ready.
- **Port:** Hosting platforms set `PORT`; the Procfile and start commands use `$PORT`. Locally you use `8000`.
