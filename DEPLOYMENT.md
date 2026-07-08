# Dotline — how it works and is deployed

A linear notebook: each note is a single vertical line of connected points. A
tap on a dot toggles "done" (black fill). Dots are `<button>`s and fully
keyboard-operable: Enter/Space toggles done, Delete/Backspace removes the point.
The dots always sit exactly on the line; the line runs a touch left of screen
centre (see `--shift`) so the right-hand labels get more room, on desktop and
mobile alike.

- **Free Dotline**: to the left of the dot — a short editable alias
  (auto-numbered 1, 2, 3…, can be replaced with your own word); to the right —
  the main item name.
- **Reverse Dotline** (`type: "reverse"`): the first event is the anchor at the
  top; each event below it is EARLIER (down = back in time), so a real up-arrow
  is drawn under every dot. Time (`HH:MM`) is shown on the left, event name on
  the right. New events default to −30 min from the previous one.
- Three time modals share one clean pattern (no titles — the content is
  self-evident): a big bold "hero" value (the thing you set) over a frosted-glass
  panel, a small secondary line (its consequence), a subtle × top-right (clicking
  outside also closes), and one round Apply button showing just a check.
  - **Edit time / Add event** — big centred `HH:MM` **text** field (accepts
    `13:30`, `1330`, `930`) + a ±6 h slider (synced with the time) + native date;
    small line shows "N earlier/later" vs the point above (hidden for the anchor).
  - **Change interval** (tap the interval pill) — big editable interval
    (e.g. `−1 h 30 min`, sign allowed) + a ±6 h slider; small line shows
    `→ HH:MM`. Changing it shifts all later events; the anchor stays fixed.
  - Dates other than the anchor day render as `14:30 · Jul 8`.
- The vertical axis sits slightly left of centre (`--shift` in `.spine`) to give
  the right-hand labels more room; the dots stay exactly on the line.
- Free-note connector: an empty link note is a small line-coloured dot on the
  line; tap it to expand the editable note, leave it empty to collapse back.
  Reverse connectors show the editable interval instead.
- The dashed grey circle at the bottom adds a new dot.
- Delete a point by dragging the dot sideways — the SVG string stretches, fades,
  and snaps. (Keyboard equivalent: focus the dot, press Delete/Backspace.)

**Live:** https://fungeneering.com/notes/

---

## Design system (single source of truth)

Everything visual is driven by CSS custom properties on `:root` in
`prototype.html`. Do not hard-code colours, sizes, or weights in components —
use a token so the system stays consistent.

**Type scale** (7 steps, no in-between values):

| Token | Size | Used for |
|-------|------|----------|
| `--fs-2xs` | 11px | uppercase labels, meta |
| `--fs-xs`  | 12px | fine hints |
| `--fs-sm`  | 13px | captions, buttons, secondary lines |
| `--fs-base`| 15px | controls, inputs |
| `--fs-md`  | 16px | primary content (item text) |
| `--fs-lg`  | 20px | mobile note title, close × glyph |
| `--fs-xl`  | 26px | screen H1, note title |
| `--fs-display` | 34px | modal hero value (the big number you set) |

**Weights:** `--w-regular` 400 (text) · `--w-medium` 500 (buttons/accent) ·
`--w-semibold` 600 (headings) · `--w-bold` 700 (modal hero).

**Type role:** one friendly rounded family, `--sans` (`ui-rounded` → SF Pro
Rounded on Apple, graceful fallback elsewhere), used everywhere. `--mono` is
retired from visible text; digits stay aligned via `font-variant-numeric:
tabular-nums`.
**Do NOT put a CJK font (Hiragino Maru Gothic, etc.) in the `--sans` stack** —
they carry Cyrillic glyphs and get chosen for Russian text, rendering it very
wide/spaced. The stack falls straight from the rounded Apple fonts to
`system-ui` so Cyrillic stays in SF Pro with normal spacing.

**Two accent colours — keep them separate:**
- `--line` **(green)** is reserved for the timeline itself — dots, the vertical
  line, arrowheads, clock hands, the connector dot, the ghost "+" and the card
  mini-previews. Nothing else.
- `--accent` **(purple)** is every UI accent — buttons, the round Apply, focus
  rings, the slider, sync dot, avatar, card hover/focus, the link-note pill
  border. Hover uses `--accent-strong`.

**Other tokens:** `--bg --surface --surface-2 --ink --muted --faint --hairline
--danger`, plus `--radius`, `--shadow`. All have light/dark variants driven by
`prefers-color-scheme` and the `data-theme` override. **Layout:** `--shift`
(axis offset left of centre), `--dot` (dot size).

The three time modals are built only from these tokens: a big hero value
(`--fs-display`, `--w-bold`) = the thing you set, a small sub (`--fs-sm`, muted)
= its consequence, `--fs-base` controls, round Apply in `--accent`.

---

## 1. Project structure (local)

`/Users/inxnik/nikita/135_fungeneering_com/notes/`

| File | What it is |
|------|------------|
| `prototype.html` | Source of the page (without `<head>`). **Edit this.** |
| `index.html` | Built standalone page = `_head` + `prototype.html` + `_tail`. Rebuild with the command below. |
| `backend/app.py` | Flask API (Google sign-in, sessions, notes in SQLite). |
| `backend/dotline-api.service` | systemd unit. |
| `backend/dotline.env.example` | Env template with Google Client ID. |
| `DEPLOYMENT.md` | This file. |

### Rebuild and deploy the frontend
```bash
cd /Users/inxnik/nikita/135_fungeneering_com/notes
cat > _head.html <<'EOF'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-color" content="#128074" />
<title>Dotline — linear notes</title>
<script src="https://accounts.google.com/gsi/client" async></script>
<style>
  html, body { margin: 0; padding: 0; }
  *, *::before, *::after { box-sizing: border-box; }
</style>
</head>
<body>
EOF
printf '</body>\n</html>\n' > _tail.html
cat _head.html prototype.html _tail.html > index.html
rm _head.html _tail.html
scp -i ~/.ssh/id_rsa_smart_shelf index.html \
  root@212.24.97.97:/var/www/fungeneering.com/notes/index.html
```
No nginx changes are needed — static files are served by the common `location /`.

---

## 2. Server (212.24.97.97, root, `~/.ssh/id_rsa_smart_shelf`)

Same server as fungeneering.com. Stack: Flask + gunicorn + systemd, configs in `/opt`.

| What | Value |
|------|-------|
| Static | `/var/www/fungeneering.com/notes/index.html` |
| Backend | `/opt/dotline/app.py`, DB `/opt/dotline/dotline.db` (SQLite) |
| Env | `/opt/dotline/dotline.env` (chmod 600) — only `GOOGLE_CLIENT_ID=` |
| Service | `dotline-api.service` → gunicorn on `127.0.0.1:5015` |
| nginx | block `location /notes/api/ { proxy_pass http://127.0.0.1:5015/api/; }` in `/etc/nginx/sites-enabled/fungeneering.com` |

### Service management
```bash
systemctl status dotline-api
systemctl restart dotline-api          # after editing app.py or env
journalctl -u dotline-api -n 50 --no-pager
curl http://127.0.0.1:5015/api/health  # local check
curl https://fungeneering.com/notes/api/health
```

### Update backend
```bash
scp -i ~/.ssh/id_rsa_smart_shelf backend/app.py root@212.24.97.97:/opt/dotline/app.py
ssh -i ~/.ssh/id_rsa_smart_shelf root@212.24.97.97 'systemctl restart dotline-api'
```

---

## 3. Authentication (Google Sign-In) — flow

1. Browser loads `index.html` + Google GSI script.
2. Frontend calls `GET /notes/api/config` and receives `googleClientId`
   (single source of truth — only on the server in env, not hardcoded in HTML).
3. The "Sign in" button renders the Google button. After sign-in Google returns
   an **ID-token (JWT)** to the callback.
4. Frontend sends `POST /notes/api/auth/google {credential}`.
5. Backend verifies the token via `https://oauth2.googleapis.com/tokeninfo`
   (checks `aud == CLIENT_ID`, `iss`, `email_verified`), creates/updates the
   user, starts a session, and sets an httpOnly cookie `dl_session`
   (Secure, SameSite=Lax, Path=/notes, 60 days).
6. `GET/PUT /notes/api/notes` then work via the cookie.

**Guest → cloud:** until signed in, notes live in `localStorage` (`dotline.v1`).
On first sign-in: if the cloud is empty but local notes exist, they are uploaded;
otherwise the cloud copy is adopted.

### API endpoints (all under `/notes/api`)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/config` | `{googleClientId}` |
| POST | `/auth/google` | sign in with Google credential → cookie |
| GET | `/me` | current user or 401 |
| POST | `/logout` | sign out |
| GET | `/notes` | `{notes:[...]}` for the user |
| PUT | `/notes` | save `{notes:[...]}` (≤2 MB) |
| GET | `/health` | `{ok, configured}` |

### Storage (SQLite `/opt/dotline/dotline.db`)
- `users(id, sub UNIQUE, email, name, picture, created)`
- `sessions(token PK, user_id, expires)`
- `data(user_id PK, json, updated)` — user's entire notes blob in one row
  (last-write-wins, frontend debounce 700 ms).
- Connections open with `busy_timeout=5000` and the DB runs in `journal_mode=WAL`
  so the two gunicorn workers don't hit "database is locked".

---

## 4. Google Sign-In status

**Status:** enabled. Current Client ID:
`25583558963-3l23v3r3n46n5fdqb7uaej2ufg6vfcbv.apps.googleusercontent.com`

Check:
```bash
curl https://fungeneering.com/notes/api/health
# {"ok":true,"configured":true}
```

The frontend picks up the Client ID via `GET /notes/api/config`, so it is not
hardcoded in HTML.

### To change or add a Client ID

1. https://console.cloud.google.com → APIs & Services → Credentials.
2. **OAuth client ID** of type **Web application**:
   - **Authorized JavaScript origins:** `https://fungeneering.com`
   - **Authorized redirect URIs:** leave empty (GSI works by origin).
3. On the server:
   ```bash
   ssh -i ~/.ssh/id_rsa_smart_shelf root@212.24.97.97
   nano /opt/dotline/dotline.env      # GOOGLE_CLIENT_ID=NEW_ID.apps.googleusercontent.com
   systemctl restart dotline-api
   curl http://127.0.0.1:5015/api/health   # configured:true
   ```

**Client Secret is not needed for GSI** — the backend verifies the ID token via
`https://oauth2.googleapis.com/tokeninfo`, checking `aud` against `CLIENT_ID`.

---

## 5. Notes for the future
- **Covers (banner over a note + faint tint on the home card):** decided to add
  later, not now. Preferred type = **uploaded photo**. That needs a real
  image-upload endpoint + file storage on the server (the ≤2 MB notes JSON blob
  can't hold photos). The cheap, no-server alternative is gradient/emoji presets
  (an id stored in the note) — fall back to that if photo storage is overkill.
- DB has no backup — add a cron `sqlite3 dotline.db .dump` if desired.
- Sync is last-write-wins: editing from two devices at the same time will
  overwrite each other (fine for personal notes).
- Google avatars load from `googleusercontent.com` (external host) — CSP on the
  production domain does not block them.
