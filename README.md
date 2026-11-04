# Draft Tracker

Follow your Basketnews **EuroLeague Draft** team live, without opening every boxscore. Pick your players once, and the app shows their stats and **Modern-scoring fantasy points**, updating by itself while games are played.

**Live version:** https://bnews-fantasy-tracker.onrender.com/

*This is a fan-made tool. It is not affiliated with Euroleague or Basketnews.*

---

## What it does

- Loads every EuroLeague game of the season from Euroleague's public stats feed.
- Calculates fantasy points for every player with the Basketnews **Modern** scoring system (see below).
- Lets you build your own team by starring players, and shows the full boxscore line for each of them, similar to the Euroleague website, plus fantasy points.
- Updates live during games with no page refresh needed.
- Works on a phone as well as on a computer.

## Using the app

### 1. Build your team
Open **All players** and tap the ☆ next to each player in your draft team. The star turns orange, and the player shows up under **My team**. Tap the star again to remove someone.

Your team is saved **in your browser, on the device you are using**. It is not shared between your phone and your laptop, and clearing your browser data removes it. Each friend builds their own team the same way.

### 2. Pick a round
The dropdown above the table decides what you see:

- **A specific round (for example Round 9):** the exact numbers from that round's game. During a live game they update as it happens, and a **Live** marker (a green pill on a computer, a green dot next to the name on a phone) shows who is playing right now. A **Final** marker means the game is over.
- **All rounds (averages):** per-game averages over the whole season. Shooting percentages are calculated from the totals, not averaged. *FP total* is the season total and *FP avg* is the average per game.

A new round appears in the dropdown about an hour before its first tip-off, and the page switches to it automatically if you were looking at the newest round. If you chose an older round or "All rounds", it stays where you put it.

### 3. Set each player's role
Tap the role button at the end of a player's row to cycle through:

| Role | Effect on fantasy points |
|---|---|
| **Starter** | counts 100% |
| **Bench** | counts 50% |
| **Captain** | counts 200% |
| **Inactive** | points are shown in grey italics but **not counted** in the total |

The multipliers apply to every FP number in the table and to the **round total** at the top right. On a phone the role buttons show just **S / B / C / I**.

### 4. Reading the table
Columns follow the Euroleague boxscore, with fantasy points added.

| Column | Meaning |
|---|---|
| **FP** | Fantasy points (Basketnews Modern), including the role multiplier |
| **Min, PTS** | Minutes played, points |
| **2FG / 3FG / FT (M/A, %)** | Made/attempted and shooting percentage |
| **Rebounds O / D / T** | Offensive, defensive, total |
| **AST, STL, TO** | Assists, steals, turnovers |
| **Blocks F / A** | Blocks made (F = in favour) and received (A = against) |
| **Fouls C / D** | Fouls committed and fouls drawn |
| **PIR** | Euroleague's Performance Index Rating |

Tap a column title to sort by it. The **Best players** strip at the top shows the three highest fantasy scorers of the selected round across all players.

**On a phone** the layout is more compact: smaller text, short column names (2P, 3P, FT, OR, DR, RB, AS, ST, TO, BK, BA, PF, FD), no percentage columns, and the player column stays in place while you scroll sideways. 2P, 3P and FT show made/attempted, OR/DR/RB are offensive, defensive and total rebounds, BK/BA are blocks made and received, and PF/FD are fouls committed and drawn.

## How fantasy points are calculated (Modern scoring)

| Action | Points |
|---|---|
| Point scored | +1 |
| Defensive rebound | +1 |
| Offensive rebound | +1.5 |
| Assist | +1.5 |
| Steal | +1.5 |
| Blocked shot | +1 |
| Foul drawn | +1 |
| Player's team wins | +1.5 |
| Player's team loses | −1.5 |
| Missed shot (2-point or 3-point) | −1 |
| Missed free throw | −1 |
| Turnover | −1.5 |
| Received block | −0.5 |
| Five personal fouls | −5 |
| Double-double | +10 |
| Triple-double | +30 |
| Quadruple-double | +100 |

How the app applies a few of these:

- **Win/loss (±1.5)** is added only once a game is **final**, so a live player's score is slightly lower or higher until the final buzzer.
- **Double/triple/quadruple-double** count points, rebounds, assists, steals and blocks. Only the highest bonus applies (a triple-double gives +30, not +40). If Basketnews turns out to stack them, this is a one-line change.
- Players who did not play (0:00 minutes) have no game in that round.

## Good to know

- **Where the data comes from:** Euroleague's public stats feed. It is not an official developer product and could change without notice. If that happens the app may stop loading until it is adjusted.
- **How fast it updates:** the server checks live games roughly every 15 seconds and the page asks the server for news every 10 seconds, so numbers can run a little behind the Euroleague site.
- **Official numbers rule:** Basketnews is the reference for your league. If the app and Basketnews ever disagree (for example after a stat correction), trust Basketnews and tell whoever maintains the app.
- **Not included:** player positions, photos, wildcards (Triple Captain, Bench Boost), trades and league standings between friends. The app only tracks your own team's points.
- **First load is slow:** the first time the app starts it downloads every game of the season, one at a time, which can take a few minutes. Newest games appear first. Finished games are then saved on the server, so later loads are quick. On free hosting the server may also go to sleep when nobody uses it, so the first visit after a quiet period can take a moment.

## Run it on your own computer (Windows)

You only need this if you want your own copy instead of the live version.

1. Install Python from https://www.python.org/downloads/ . On the first installer screen, tick **"Add python.exe to PATH"**.
2. On the GitHub page of this project click the green **Code** button, then **Download ZIP**, and unzip it.
3. Double-click **`start.bat`**. Your browser opens the dashboard. Keep the black window open while you use it, because closing it stops the app.

Nothing else needs to be installed.

**Updates:** each time you start it, `start.bat` downloads the newest version from GitHub (this uses the `repo.txt` file, which must contain `your-github-username/repository-name`). You never need to download again.

## Settings (for whoever maintains the app)

At the top of `server.py`:

- `SEASON = "E2026"` is the season (E2026 means 2026-27). Use `E2025` to look at last season.
- `PORT = 8000` is the port for the local version.

## If something looks wrong

- **Stuck on "Loading games…":** wait a few minutes on the first start. If there is a red message, it says what failed (for example Euroleague asking us to slow down, which fixes itself).
- **A round or game is missing:** open `/api/debug` on the app's address (for example `http://localhost:8000/api/debug`) and send the text you see to whoever maintains the app. It shows what Euroleague's schedule returned.
- **My team disappeared:** your team lives in the browser of that device. A different browser, a private window or cleared browser data starts with an empty team.
