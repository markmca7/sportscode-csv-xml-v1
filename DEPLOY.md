
# Deploying the Sportscode CSV → XML App Online

Below are **three** easy hosting options. All accept file uploads and return a downloadable XML.

---

## Option A — Streamlit Community Cloud (fastest, free)
1. Create a **public GitHub repo** with `app.py` and `requirements.txt` (these two files are enough).
2. Go to **share.streamlit.io** and click **New app** → select your repo/branch.
3. Set **Python version** to 3.11 (or match your local), leave defaults.
4. Click **Deploy**.
5. Share the resulting URL with clients.

**Pros:** Dead simple, free, great for Streamlit apps.  
**Cons:** Public repos only (unless you’re on a paid workspace).

---

## Option B — Hugging Face Spaces (free)
1. Create a new **Space** (choose **Streamlit** template).
2. Upload `app.py` and `requirements.txt`.
3. Click **Commit**; your Space builds and goes live.
4. Share the Space URL.

**Pros:** Very quick, easy, handles file uploads well.  
**Cons:** Public by default (private Spaces require paid plan).

---

## Option C — Render / Fly.io / Any Docker host (private or custom domain)
1. Put these three files in a repo:
   - `app.py`
   - `requirements.txt`
   - `Dockerfile` (included in this folder)
2. Create a new **Web Service** from your repo.
3. Set the **Start Command** to the Dockerfile default, or leave blank to use it.
4. Ensure port **8501** is exposed or ENV `PORT` is respected.

**Pros:** Private, custom domain/SSL, simple scaling.  
**Cons:** Small monthly cost, slightly more setup.

---

## Notes on Privacy & Compliance
- **No data is stored** server-side by default; Streamlit runs in-memory. If you add logging or analytics, ensure you **exclude file contents**.
- Add a short **Privacy Policy** to the app (e.g., “files are processed in-memory and never stored”).
- If operating in the EU/UK: consider **GDPR** basics — define retention (none), purpose (conversion), and contact info.

## Optional Enhancements
- **Branding:** add your logo, brand colours, and a support email in the header.
- **Per-file limits:** reject very large CSVs (e.g., >15 MB) for predictable performance.
- **Error telemetry:** capture exceptions with Sentry (mask PII).
- **Auth:** protect with a simple password env var on Render/Fly.

---

## Local test
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Docker test locally
```bash
docker build -t sportscode-app .
docker run -p 8501:8501 sportscode-app
# open http://localhost:8501
```
