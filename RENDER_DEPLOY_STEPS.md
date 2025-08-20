# Deploy to Render — Step-by-step (no coding)

## Backend (Flask API)
1. Go to https://dashboard.render.com → **New** → **Blueprint** (recommended) and connect your GitHub repo.
   - Render will detect `render.yaml` in the repo and set up services.
2. Alternatively: **New → Web Service** and fill in:
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt || pip install -r altona_village_cms/requirements.txt`
   - Start Command: `gunicorn "altona_village_cms.src.main:app" --workers=2 --timeout=120 -b 0.0.0.0:$PORT`
3. Add a **PostgreSQL** database in Render and link it to the backend; Render auto-injects `DATABASE_URL`.
4. Add env vars to the backend service:
   - `SECRET_KEY` (any random string)
   - `JWT_SECRET_KEY` (any random string)
   - `CORS_ORIGINS` → `https://<your-frontend-domain>,http://localhost:5173`
5. Deploy. When live, your backend URL will look like `https://altona-village-backend.onrender.com`.

## Frontend (React/Vite static site)
1. In `render.yaml` we already set a Static Site for `altona-village-frontend/dist`.
2. Ensure the env var `VITE_API_BASE` points to your backend URL with `/api`, e.g.:
   `https://altona-village-backend.onrender.com/api`
3. Deploy the static site. Test a page that calls the API.

## Smoke Test Checklist
- Can log in with a known test user (or admin) → JWT is returned and stored
- Create/Edit/Delete a contractor/resident entry → changes appear in list
- Filters (date/company) work and can be cleared
- Exports (CSV/XLSX) download and open
- Permissions: viewer cannot access admin pages
- Mobile: narrow the browser to verify navbar and forms are still usable

## If something fails
- Copy the exact error (screenshot if possible) and paste it back to me. I’ll give you the precise change to make.
