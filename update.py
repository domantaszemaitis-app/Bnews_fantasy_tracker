"""Runs before the app starts: downloads the newest server.py / index.html from GitHub."""
import io, os, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ("server.py", "index.html", "update.py", "README.md")   # start.bat and repo.txt are never overwritten

def main():
    try: repo = open(os.path.join(HERE, "repo.txt")).read().strip()
    except Exception: return
    if "/" not in repo or repo.upper().startswith("YOUR"):
        print("Updates are off (repo.txt is not set up yet)."); return
    try:
        req = urllib.request.Request(f"https://github.com/{repo}/archive/refs/heads/main.zip", headers={"User-Agent": "Mozilla/5.0"})
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=20).read()))
    except Exception as e:
        print("Could not check for updates, starting the version you have:", e); return
    changed = []
    for name in z.namelist():
        parts = name.split("/", 1)
        if len(parts) == 2 and parts[1] in FILES:
            new, path = z.read(name), os.path.join(HERE, parts[1])
            old = open(path, "rb").read() if os.path.exists(path) else None
            if new != old:
                open(path, "wb").write(new); changed.append(parts[1])
    print("Updated: " + ", ".join(changed) if changed else "You have the latest version.")

if __name__ == "__main__":
    main()
