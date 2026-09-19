# E&H Men's Soccer 2026 Tracker

A small static web app for following the 2026 Emory & Henry men's soccer season, with a dedicated watch section for Niklas Borck. The visual system uses the team's black, white and gold palette and includes family-provided player and team photography.

## What is included

- completed results and home/away filters
- overall and South Atlantic Conference records
- recent team performance metrics
- remaining SAC fixtures
- current conference table
- Niklas Borck player profile and verified match-sheet log
- responsive light and dark themes

## Publish with GitHub Pages

1. Create a new GitHub repository.
2. Upload `index.html`, `styles.css`, `app.js`, and `.nojekyll` to the repository root.
3. Open **Settings → Pages**.
4. Under **Build and deployment**, choose **Deploy from a branch**.
5. Select the `main` branch and the `/ (root)` folder, then save.
6. GitHub will show the public URL after the first deployment completes.

No build command, server, API key, or database is required.

## Automatic updates

The GitHub Action in `.github/workflows/update-season.yml` runs every hour and can also be started manually from the Actions tab. It refreshes `data/season.json` from the official SAC schedule, standings and team statistics. It also discovers newly published official E&H box scores and verifies Niklas Borck's appearance, start, minutes, goals, assists, shots and shots on goal.

The updater is deliberately conservative. If a page is unavailable or a player row cannot be mapped reliably, the last verified value remains in place rather than being replaced with incomplete data.

For a manual correction, edit `data/season.json`, commit the change and push it to `main`. GitHub Pages will redeploy automatically.

Official sources:

- Team schedule: https://thesac.com/schedule.aspx?schedule=2504
- SAC standings: https://thesac.com/standings.aspx?path=msoc
- SAC statistics: https://thesac.com/stats.aspx?path=msoc&year=2026
- E&H match sheets: https://www.gowasps.com/sports/msoc/2026-27/schedule
- Niklas Borck updates: https://www.sofascore.com/football/player/niklas-borck/2722370

## Privacy

The site is entirely static. It sets no cookies and sends no personal or family data to a backend. External links open their respective sports-data websites.
