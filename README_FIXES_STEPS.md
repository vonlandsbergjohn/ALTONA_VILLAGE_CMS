# Quick Fix Pack — Apply via GitHub Web

This pack adds safe, deployment-ready files and ignores local secrets/artifacts.

## What this does
- Adds `.gitattributes` to normalize line-endings (prevents CRLF/LF warnings)
- Adds `.gitignore` to stop committing `venv/`, `.env`, compiled files, local SQLite DB, and `uploads/`
- Adds `.env.example` (template for your real `.env`, which should NOT be committed)
- Adds `Procfile` + `render.yaml` for Render.com deployment (backend + static frontend)

## How to apply (no coding)
1. Download `altona_render_bootstrap.zip` to your computer.
2. Go to your GitHub repo → click **Add file → Upload files**.
3. Drag all the **files inside** the ZIP into the upload area (don’t upload the ZIP itself).
4. Commit directly to `main` (or create a new branch if you prefer).

## One-time cleanup (very important)
- In GitHub, delete these tracked items so they stop causing problems:
  - `venv/` (folder)
  - `.env` (file)
- Steps:
  1. Open the file/folder in GitHub
  2. Click the three-dots menu → **Delete**
  3. Commit the deletion

## Optional (backend code adjustments)
If your backend *does not* already handle Postgres on Render, open
`altona_village_cms/src/main.py` in GitHub and make these safe additions:

1) **Prefer Postgres if DATABASE_URL exists; else use local SQLite**
   ```python
   import os
   DATABASE_URL = os.getenv("DATABASE_URL")
   if DATABASE_URL and DATABASE_URL.startswith("postgres"):
       app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://", 1)
   else:
       app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
   ```

2) **CORS for your API**
   ```python
   from flask_cors import CORS
   CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})
   ```

3) **Ensure new blueprints are registered under `/api`**
   ```python
   # Example
   app.register_blueprint(transition_linking_bp, url_prefix="/api")
   ```

> If you can't find those lines, skip this optional step and we can handle it later.

## Next step — Deploy on Render
See `RENDER_DEPLOY_STEPS.md` included in this pack.
