# Office Request App

I got tired of people asking me to restock snacks or buy office supplies over KakaoTalk with zero context — no photo, no link, just "can you get chips." So I built this.

## What it does

Employees go to the app, type in their name, and search for whatever they need — snacks, drinks, A4 paper, pens, whatever. It pulls real product results from Naver Shopping so they can pick the *exact* item (right brand, right size, right quantity). They add things to a cart, leave a note if it's urgent, and submit. I get a clean admin view showing who requested what, with product images, prices, and links — and I can export everything as a CSV.

No more vague requests. No more forgetting. Just a simple paper trail.

## Why I built it

Mostly because I'm the one doing the restocking and I wanted a better system than a group chat. Also a good excuse to build something actually useful for the office instead of yet another todo app.

## Tech stack

- **Python + Flask** — backend and routing
- **SQLite** — keeps it simple, no external DB needed
- **Naver Shopping API** — product search with real Korean results
- **Vanilla HTML/CSS/JS** — no frontend framework, just clean templates
- **Railway** — deployment, with a mounted volume so data persists
