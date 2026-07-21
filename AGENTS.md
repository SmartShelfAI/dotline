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
./deploy.sh         # build index.html + deploy frontend
```

## Baseline check before editing

Never start writing code before confirming the single source of truth. For this repo that means:

1. **Check local git state**  
   `git status --short` and `git branch -v`. If there are uncommitted changes, stop and ask the user how to handle them before adding new edits.

2. **Sync with GitHub**  
   `git fetch origin` and verify `origin/HEAD` matches local `HEAD`:  
   `git log --oneline HEAD..origin/master` should be empty.  
   If origin is ahead, do not write new code until the local branch is updated.

3. **Check the server before deploying**  
   Before any deploy, compare the file currently on the server against the committed baseline and the local built file:  
   ```bash
   git show HEAD:index.html | md5
   md5 index.html
   ssh -i ~/.ssh/id_rsa_smart_shelf -o BatchMode=yes root@212.24.97.97 'md5sum /var/www/fungeneering.com/notes/index.html'
   ```  
   Only deploy if the server copy matches `HEAD:index.html` (or matches the local changed `index.html` after a prior deploy from this session). If the server hash differs from both, stop and ask.

4. **Work from the latest baseline**  
   Edit only after the above checks pass. If edits were already made before verifying the baseline, stop, report the situation, and ask whether to reset, commit, or merge.

## Rules of thumb

- Make minimal, focused changes. The frontend is one file; global CSS rules easily leak.
- After changing styles, verify both desktop and mobile (narrow viewport).
- Do not run `git commit`, `git push`, `git reset`, `git rebase`, or force-push without explicit user confirmation.
- Keep `node_modules/` out of git — it is already in `.gitignore`.
