"""Single deployable entrypoint (used by Vercel, or `uvicorn main:app`).

FastAPI serves events/notifications/search/stats/uploads; every other path falls through to the
Flask app (auth, alumni directory, mentorship) mounted at the root. Locally you can still run the
two services separately on ports 5000 and 8000.
"""
from a2wsgi import WSGIMiddleware

from fastapi_service.main import app
from flask_service.app import app as flask_app

app.mount("/", WSGIMiddleware(flask_app))
