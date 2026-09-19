# E&H Men's Soccer 2026 Tracker

A small static web app for following the 2026 Emory & Henry men's soccer season, with a dedicated watch section for Niklas Borck.

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

## Updating the data

All displayed data is in `index.html`. Search for the relevant player, fixture, result, or standings section and replace the visible values. Update the “Data through” date in the sidebar when results are added.

Official sources:

- Team schedule: https://thesac.com/schedule.aspx?schedule=2504
- SAC standings: https://thesac.com/standings.aspx?path=msoc
- SAC statistics: https://thesac.com/stats.aspx?path=msoc&year=2026
- Niklas Borck updates: https://www.sofascore.com/football/player/niklas-borck/2722370

## Privacy

The site is entirely static. It sets no cookies and sends no personal or family data to a backend. External links open their respective sports-data websites.
