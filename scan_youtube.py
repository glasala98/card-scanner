"""
Scan a YouTube video for trading cards — extracts frames at intervals,
identifies each card with Claude Vision, and looks up prices.

Usage:
    python scan_youtube.py <youtube_url>
    python scan_youtube.py <youtube_url> --interval 3
    python scan_youtube.py <youtube_url> --interval 3 --start 60 --end 120
    python scan_youtube.py <youtube_url> --json
    python scan_youtube.py <youtube_url> --demo   # push results to overlay server

Options:
    --interval  Seconds between frame samples (default: 5)
    --start     Start time in seconds (default: 0)
    --end       End time in seconds (default: full video)
    --json      Print raw JSON for each detection
    --demo      Push each detected card to the overlay server at localhost:5050
    --confidence Minimum confidence threshold 0.0-1.0 (default: 0.7)

Requirements:
    pip install yt-dlp opencv-python anthropic pillow python-dotenv
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

import cv2
import requests
from dotenv import load_dotenv

load_dotenv()


def download_video(url: str, out_path: str) -> bool:
    """Download video using yt-dlp to out_path."""
    print(f"Downloading video: {url}")
    result = subprocess.run(
        [
            "yt-dlp",
            "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
            "--merge-output-format", "mp4",
            "-o", out_path,
            "--no-playlist",
            "--quiet",
            "--progress",
            url,
        ],
        capture_output=False,
    )
    return result.returncode == 0


def extract_frames(video_path: str, interval: float, start: float, end: float):
    """Yield (timestamp, frame) tuples from video at given interval."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total_frames / fps

    end = min(end, duration) if end else duration
    t = start

    print(f"Video duration: {duration:.0f}s | Sampling {start:.0f}s → {end:.0f}s every {interval}s")
    print(f"Estimated frames to check: {int((end - start) / interval)}\n")

    while t <= end:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ret, frame = cap.read()
        if not ret:
            break
        yield t, frame
        t += interval

    cap.release()


def push_to_overlay(card_data: dict):
    """Push a detected card to the local overlay server."""
    try:
        requests.post("http://localhost:5050/api/inject", json=card_data, timeout=1)
    except Exception:
        pass  # overlay server not running — silently skip


def fmt_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def main():
    parser = argparse.ArgumentParser(description="Scan a YouTube video for trading cards.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--interval",    type=float, default=5,   help="Seconds between frame samples (default: 5)")
    parser.add_argument("--start",       type=float, default=0,   help="Start time in seconds")
    parser.add_argument("--end",         type=float, default=0,   help="End time in seconds (0 = full video)")
    parser.add_argument("--confidence",  type=float, default=0.7, help="Min confidence threshold (default: 0.7)")
    parser.add_argument("--json",  dest="as_json", action="store_true", help="Print raw JSON output")
    parser.add_argument("--demo",  action="store_true", help="Push results to overlay server at localhost:5050")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    from scanner import scan_frame, lookup_price

    detections = []

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "video.mp4")

        if not download_video(args.url, video_path):
            print("ERROR: yt-dlp failed to download the video.")
            print("Make sure yt-dlp is installed: pip install yt-dlp")
            sys.exit(1)

        print()

        for timestamp, frame in extract_frames(
            video_path,
            interval=args.interval,
            start=args.start,
            end=args.end if args.end else float("inf"),
        ):
            ts = fmt_time(timestamp)
            print(f"[{ts}] Scanning...", end=" ", flush=True)

            result = scan_frame(frame)
            confidence = result.get("confidence", 0.0)

            if not result.get("detected") or confidence < args.confidence:
                print(f"no card ({confidence:.0%})")
                continue

            name = result.get("name", "Unknown")
            game = result.get("game", "?")
            print(f"{game} — {name} ({confidence:.0%})")

            # Price lookup
            price_data = lookup_price(
                result.get("game", ""),
                name,
                result.get("set", ""),
                result.get("year", ""),
            )

            detection = {
                "timestamp": ts,
                "timestamp_seconds": timestamp,
                **result,
                **price_data,
            }
            detections.append(detection)

            label = price_data.get("price_label", "No price data")
            print(f"         Price: {label}")

            if args.demo:
                push_to_overlay({**result, **price_data, "detected": True})
                time.sleep(0.2)

            if args.as_json:
                print(json.dumps(detection, indent=2))

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=" * 55)
    print(f"  SCAN COMPLETE — {len(detections)} card(s) detected")
    print("=" * 55)

    if not detections:
        print("  No cards found. Try a lower --confidence or shorter --interval.")
        return

    # Deduplicate by name
    seen = {}
    for d in detections:
        name = d.get("name", "Unknown")
        if name not in seen:
            seen[name] = d

    print(f"  {'Time':>5}  {'Game':8}  {'Card':<30}  {'Price':>10}")
    print(f"  {'-'*5}  {'-'*8}  {'-'*30}  {'-'*10}")
    for d in seen.values():
        print(f"  {d['timestamp']:>5}  {d.get('game','?'):8}  {d.get('name','?'):<30}  {d.get('price_label','N/A'):>10}")

    if args.as_json:
        print("\nFull JSON:")
        print(json.dumps(list(seen.values()), indent=2))


if __name__ == "__main__":
    main()
