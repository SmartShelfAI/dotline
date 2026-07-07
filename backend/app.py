"""Dotline notes API — Google Sign-In auth + per-user notes in SQLite.

Runs behind nginx at https://fungeneering.com/notes/api/  (nginx strips /notes,
so Flask sees /api/...). Google ID tokens are verified via Google's tokeninfo
endpoint, so no extra python packages are needed beyond Flask + requests.
"""
import os
import json
import time
import sqlite3
import secrets
import datetime

import requests
from flask import Flask, request, jsonify, make_response

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "dotline.db")
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
COOKIE = "dl_session"
SESSION_DAYS = 60
MAX_BLOB = 2_000_000  # ~2 MB per user of notes JSON

app = Flask(__name__)


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = db()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            sub TEXT UNIQUE,
            email TEXT, name TEXT, picture TEXT,
            created TEXT);
        CREATE TABLE IF NOT EXISTS sessions(
            token TEXT PRIMARY KEY,
            user_id INTEGER,
            expires REAL);
        CREATE TABLE IF NOT EXISTS data(
            user_id INTEGER PRIMARY KEY,
            json TEXT,
            updated TEXT);
        """
    )
    c.commit()
    c.close()


init_db()


def now():
    return datetime.datetime.utcnow().isoformat()


def current_user():
    tok = request.cookies.get(COOKIE)
    if not tok:
        return None
    c = db()
    row = c.execute(
        "SELECT s.expires AS s_expires, u.* FROM sessions s "
        "JOIN users u ON u.id = s.user_id WHERE s.token = ?",
        (tok,),
    ).fetchone()
    c.close()
    if not row or row["s_expires"] < time.time():
        return None
    return row


def user_json(u):
    return {"email": u["email"], "name": u["name"], "picture": u["picture"]}


@app.get("/api/config")
def config():
    # single source of truth for the client id — frontend fetches it on load
    return jsonify({"googleClientId": CLIENT_ID})


@app.post("/api/auth/google")
def auth_google():
    data = request.get_json(silent=True) or {}
    cred = data.get("credential")
    if not cred:
        return jsonify({"error": "no credential"}), 400
    try:
        r = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": cred},
            timeout=10,
        )
    except Exception:
        return jsonify({"error": "verify failed"}), 502
    if r.status_code != 200:
        return jsonify({"error": "invalid token"}), 401
    claims = r.json()
    if not CLIENT_ID:
        return jsonify({"error": "server not configured"}), 503
    if claims.get("aud") != CLIENT_ID:
        return jsonify({"error": "bad audience"}), 401
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        return jsonify({"error": "bad issuer"}), 401
    if str(claims.get("email_verified")).lower() != "true":
        return jsonify({"error": "email not verified"}), 401

    sub = claims["sub"]
    email = claims.get("email", "")
    name = claims.get("name", "") or email.split("@")[0]
    picture = claims.get("picture", "")

    c = db()
    c.execute(
        "INSERT INTO users(sub, email, name, picture, created) VALUES(?,?,?,?,?) "
        "ON CONFLICT(sub) DO UPDATE SET email=excluded.email, name=excluded.name, "
        "picture=excluded.picture",
        (sub, email, name, picture, now()),
    )
    uid = c.execute("SELECT id FROM users WHERE sub = ?", (sub,)).fetchone()["id"]
    tok = secrets.token_urlsafe(32)
    exp = time.time() + SESSION_DAYS * 86400
    c.execute("INSERT INTO sessions(token, user_id, expires) VALUES(?,?,?)", (tok, uid, exp))
    c.commit()
    c.close()

    resp = make_response(jsonify({"user": {"email": email, "name": name, "picture": picture}}))
    resp.set_cookie(
        COOKIE, tok, max_age=SESSION_DAYS * 86400,
        httponly=True, secure=True, samesite="Lax", path="/notes",
    )
    return resp


@app.get("/api/me")
def me():
    u = current_user()
    if not u:
        return jsonify({"error": "unauth"}), 401
    return jsonify({"user": user_json(u)})


@app.post("/api/logout")
def logout():
    tok = request.cookies.get(COOKIE)
    if tok:
        c = db()
        c.execute("DELETE FROM sessions WHERE token = ?", (tok,))
        c.commit()
        c.close()
    resp = make_response(jsonify({"ok": True}))
    resp.set_cookie(COOKIE, "", max_age=0, path="/notes")
    return resp


@app.get("/api/notes")
def get_notes():
    u = current_user()
    if not u:
        return jsonify({"error": "unauth"}), 401
    c = db()
    row = c.execute("SELECT json FROM data WHERE user_id = ?", (u["id"],)).fetchone()
    c.close()
    notes = json.loads(row["json"]).get("notes", []) if row else []
    return jsonify({"notes": notes})


@app.put("/api/notes")
def put_notes():
    u = current_user()
    if not u:
        return jsonify({"error": "unauth"}), 401
    data = request.get_json(silent=True) or {}
    notes = data.get("notes", [])
    if not isinstance(notes, list):
        return jsonify({"error": "bad payload"}), 400
    blob = json.dumps({"notes": notes})
    if len(blob) > MAX_BLOB:
        return jsonify({"error": "too big"}), 413
    c = db()
    c.execute(
        "INSERT INTO data(user_id, json, updated) VALUES(?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET json=excluded.json, updated=excluded.updated",
        (u["id"], blob, now()),
    )
    c.commit()
    c.close()
    return jsonify({"ok": True, "updated": now()})


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "configured": bool(CLIENT_ID)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5015, debug=True)
