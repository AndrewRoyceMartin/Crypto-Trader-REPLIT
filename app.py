# app.py
from __future__ import annotations

import json
import logging
import os
from importlib import import_module
from typing import Any, Optional

from flask import (
    Flask,
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

# ------------------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")

# Load .env locally; on Render, env vars are already injected
try:
    from dotenv import load_dotenv  # optional
    load_dotenv(override=False)
except Exception:
    pass

# Logging suitable for Render
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger("app")

# Currency default (used by demo / summary)
DEFAULT_CURRENCY = os.getenv("CURRENCY", "AUD")


# ------------------------------------------------------------------------------
# Jinja helpers (safe endpoint resolver: no current_app usage in templates)
# ------------------------------------------------------------------------------
@app.context_processor
def _endpoint_helpers():
    def endpoint_url(name: str, default: Optional[str] = None, **values) -> str:
        try:
            return url_for(name, **values)
        except Exception:
            return default or ""
    return dict(endpoint_url=endpoint_url)


# ------------------------------------------------------------------------------
# Pages
# ------------------------------------------------------------------------------
@app.get("/")
def home():
    # Keep root lightweight and cacheable by Render’s health checks
    return redirect(url_for("dashboard"), code=302)


@app.get("/dashboard")
def dashboard():
    try:
        return render_template("dashboard.html")
    except Exception as e:
        log.exception("Error rendering dashboard: %s", e)
        return (
            f"<h1>Dashboard error</h1><pre>{str(e)}</pre>",
            500,
            {"Content-Type": "text/html; charset=utf-8"},
        )


# ------------------------------------------------------------------------------
# Health
# ------------------------------------------------------------------------------
@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


# ------------------------------------------------------------------------------
# API: prefer your existing blueprint; provide safe fallbacks if absent
# ------------------------------------------------------------------------------
# If you already have an 'api' blueprint, do nothing here.
# Otherwise, register a minimal '/api' with /summary and /holdings
if "api" not in app.blueprints:
    api = Blueprint("api", __name__, url_prefix="/api")

    def _try_provider(candidates: list[tuple[str, str]]):
        """
        Try to import a callable from known locations:
        e.g. ('api.portfolio', 'get_summary_json'), ('services.portfolio', 'get_summary')
        """
        for mod_name, attr in candidates:
            try:
                mod = import_module(mod_name)
                fn = getattr(mod, attr)
                if callable(fn):
                    return fn
            except Exception:
                continue
        return None

    @api.get("/summary")
    def summary():
        """
        Return portfolio summary. If your real provider exists, use it.
        Otherwise, serve a harmless demo payload so the dashboard renders.
        """
        provider = _try_provider([
            ("api.portfolio", "get_summary_json"),
            ("api.portfolio", "get_summary"),
            ("services.portfolio", "get_summary_json"),
            ("services.portfolio", "get_summary"),
            ("app", "get_portfolio_summary"),  # optional user function
        ])
        try:
            data = provider() if provider else {
                "total_value": 0.0,
                "daily_pnl_percent": 0.0,
                "total_pnl_percent": 0.0,
                "last_updated": None,
                "currency": DEFAULT_CURRENCY,
            }
            json.dumps(data)  # ensure serialisable
            return jsonify(data), 200
        except Exception as e:
            log.exception("summary() failed: %s", e)
            return jsonify({"error": "summary_failed", "detail": str(e)}), 500

    @api.get("/holdings")
    def holdings():
        """
        Return holdings list. Uses your provider if present; otherwise [].
        """
        provider = _try_provider([
            ("api.portfolio", "get_holdings_json"),
            ("api.portfolio", "get_holdings"),
            ("services.portfolio", "get_holdings_json"),
            ("services.portfolio", "get_holdings"),
            ("app", "get_portfolio_holdings"),  # optional user function
        ])
        try:
            data = provider() if provider else []
            if not isinstance(data, list):
                raise TypeError("holdings provider must return a list")
            json.dumps(data)
            return jsonify(data), 200
        except Exception as e:
            log.exception("holdings() failed: %s", e)
            return jsonify({"error": "holdings_failed", "detail": str(e)}), 500

    app.register_blueprint(api)


# ------------------------------------------------------------------------------
# API error handlers (only affect /api/*)
# ------------------------------------------------------------------------------
@app.errorhandler(404)
def _not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "not_found", "path": request.path}), 404
    return ("Not found", 404)


@app.errorhandler(500)
def _internal_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "internal_error", "detail": str(e)}), 500
    return ("Internal server error", 500)


# ------------------------------------------------------------------------------
# Entrypoint (Render sets $PORT)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5050"))
    log.info("Starting server on 0.0.0.0:%s", port)
    app.run(host="0.0.0.0", port=port)
