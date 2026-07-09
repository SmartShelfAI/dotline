# Dotline — agent notes

## Project structure

- `prototype.html` — the single source of truth (HTML + CSS + JS). **Edit this file.**
- `index.html` — built standalone file = `_head.html` + `prototype.html` + `_tail.html`. Rebuild after any change to `prototype.html`.
- `backend/` — Flask API (Google Sign-In, sessions, SQLite). Usually not touched for frontend changes.
- `DEPLOYMENT.md` — server details and deployment steps.
- `DECISIONS.md` — design and architecture decisions.

## Build & validate

Before publishing, run the validators:

```bash
cd /Users/inxnik/nikita/135_fungeneering_com/notes
npm install          # only first time / when dependencies change
npm run check        # runs ESLint + Prettier check
```

- **ESLint** (`npm run lint`) checks JS inside `prototype.html` for errors and unused variables.
- **Prettier** (`npm run format:check`) checks formatting.
- If Prettier complains, run `npm run format` to auto-fix style.
- If ESLint reports errors, fix them before deploying. Warnings are acceptable but should be reviewed.

Then rebuild and deploy:

```bash
./tools/build.sh     # or manually: cat _head.html prototype.html _tail.html > index.html
scp -i ~/.ssh/id_rsa_smart_shelf index.html root@212.24.97.97:/var/www/fungeneering.com/notes/index.html
```

## Rules of thumb

- Make minimal, focused changes. The frontend is one file; global CSS rules easily leak.
- After changing styles, verify both desktop and mobile (narrow viewport).
- Do not run `git commit`, `git push`, `git reset`, `git rebase`, or force-push without explicit user confirmation.
- Keep `node_modules/` out of git — it is already in `.gitignore`.
