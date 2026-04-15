#!/Users/ryann/Desktop/Newzyx/venv/bin/python
"""
run_once.py — Run the full pipeline a single time and exit.
Usage: python run_once.py
"""
from pipeline import db, collect, extract, process, episode, tts, upload, rss
from datetime import datetime
import sys
import io
import os

STEPS = [
    ("Collecting URLs",     "Scraping news headlines"),
    ("Extracting articles", "Pulling article text"),
    ("AI processing",       "Scoring & summarizing"),
    ("Selecting articles",  "Building episode"),
    ("Creating script",     "Podcast script + polish"),
    ("Generating audio",    "ElevenLabs TTS"),
    ("Building webpage",    "Generating episode page"),
    ("Updating RSS feed",   "Adding episode to feed"),
    ("Uploading to S3",     "All files"),
]

TOTAL = len(STEPS)
real_stdout = sys.stdout


def draw_bar(current, total, label, detail="", done=False):
    pct = int((current / total) * 100)
    filled = pct // 5
    bar = "\u2588" * filled + "\u2591" * (20 - filled)
    check = " \u2713" if done else " ..."
    info = f"  ({detail})" if detail and not done else ""
    real_stdout.write(f"\r  [{bar}] {pct:3d}%  Step {current}/{total}: {label}{check}{info}      ")
    real_stdout.flush()


def run_step(num, fn):
    label, detail = STEPS[num - 1]
    draw_bar(num, TOTAL, label, detail)
    buf = io.StringIO()
    sys.stdout = buf
    try:
        result = fn()
    except BaseException:
        sys.stdout = real_stdout
        raise
    sys.stdout = real_stdout
    output = buf.getvalue()
    if output.strip():
        real_stdout.write(f"\r{' ' * 100}\r")
        real_stdout.write(output)
    draw_bar(num, TOTAL, label, done=True)
    real_stdout.write("\n")
    return result


try:
    start = datetime.now()
    base = os.path.dirname(__file__)

    print()
    print("  \u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557")
    print("  \u2551          NEWZYX V2 \u2014 ONE-TIME RUN            \u2551")
    print(f"  \u2551  {start.strftime('%Y-%m-%d %H:%M:%S')}                             \u2551")
    print("  \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d")
    print()

    db.init_db()

    run_step(1, collect.collect_urls)
    run_step(2, extract.process_urls)
    run_step(3, process.process_content)

    ep = None

    def step4():
        global ep
        ep = episode.select_articles()

    run_step(4, step4)

    if not ep:
        print("\n  \u26a0\ufe0f  Not enough quality articles today. Skipping episode.\n")
    else:
        script_path = os.path.join(base, "data", "script.txt")
        run_step(5, lambda: episode.create_script(script_path, ep, t=0))

        audio_files = []
        def step6():
            global audio_files
            audio_files = tts.tts(script_path, t=0)
        run_step(6, step6)

        site_files = []
        def step7():
            global site_files
            site_files = episode.create_site(ep, t=0)
        run_step(7, step7)

        run_step(8, lambda: rss.update_all_episodes("website/feed.xml", max_episodes=500))

        def step9():
            all_files = [os.path.join("website", f) for f in site_files]
            all_files.extend(audio_files)
            all_files.append("website/feed.xml")
            all_files.append("website/today.mp3")
            upload.upload_files(all_files)
        run_step(9, step9)

        article_ids = [a["id"] for a in ep]
        db.mark_published(article_ids)

    elapsed = datetime.now() - start
    mins, secs = divmod(int(elapsed.total_seconds()), 60)
    print()
    print(f"  [\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588] 100%  ALL DONE \u2713")
    print()
    print("  \u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557")
    print(f"  \u2551  Completed in {mins}m {secs}s                          \u2551")
    print(f"  \u2551  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                             \u2551")
    print("  \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d")
    stats = db.get_stats()
    print(f"  DB: {stats['total']} articles | {stats['by_state']}")
    print()

except KeyboardInterrupt:
    sys.stdout = real_stdout
    print("\n\n  \u26d4 Cancelled. Safe to rerun.\n")
