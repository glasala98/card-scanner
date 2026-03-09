"""
Card Scanner — overlay server
------------------------------
Serves the OBS browser source overlay and the /api/current-card endpoint.

Run this first, then run scanner.py in a separate terminal.

    python server.py
"""

import os
import time
import json
from flask import Flask, jsonify, render_template_string
from scanner import current_card, _state_lock, CONFIG

app = Flask(__name__)
DISPLAY_SECONDS = CONFIG.get("overlay_display_seconds", 8)


OVERLAY_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: transparent;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    color: #fff;
    width: 420px;
  }

  #card-overlay {
    background: linear-gradient(135deg, rgba(10,20,30,0.92) 0%, rgba(0,30,40,0.92) 100%);
    border: 1px solid #00d4aa;
    border-radius: 10px;
    padding: 14px 18px;
    display: none;
    animation: slideIn 0.3s ease;
    backdrop-filter: blur(8px);
  }

  #card-overlay.visible { display: block; }

  @keyframes slideIn {
    from { transform: translateX(-20px); opacity: 0; }
    to   { transform: translateX(0);     opacity: 1; }
  }

  .game-badge {
    display: inline-block;
    background: #00d4aa;
    color: #000;
    font-size: 10px;
    font-weight: bold;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }

  .card-name {
    font-size: 18px;
    font-weight: bold;
    color: #fff;
    line-height: 1.2;
  }

  .card-meta {
    font-size: 12px;
    color: #8899aa;
    margin-top: 3px;
  }

  .price-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-top: 10px;
    border-top: 1px solid rgba(0,212,170,0.2);
    padding-top: 8px;
  }

  .price-label { font-size: 11px; color: #8899aa; }

  .price-value {
    font-size: 22px;
    font-weight: bold;
    color: #00d4aa;
    font-variant-numeric: tabular-nums;
  }

  .variant-badge {
    margin-left: auto;
    font-size: 10px;
    background: rgba(0,212,170,0.15);
    border: 1px solid #00d4aa44;
    color: #00d4aa;
    padding: 2px 8px;
    border-radius: 4px;
  }
</style>
</head>
<body>
<div id="card-overlay">
  <div class="game-badge" id="game-badge">NHL</div>
  <div class="card-name" id="card-name">Connor McDavid</div>
  <div class="card-meta" id="card-meta">2024-25 · Upper Deck Young Guns</div>
  <div class="price-row">
    <span class="price-label">Market</span>
    <span class="price-value" id="price-value">$142.00</span>
    <span class="variant-badge" id="variant-badge">RC</span>
  </div>
</div>

<script>
let hideTimer = null;

async function poll() {
  try {
    const r = await fetch('/api/current-card');
    const data = await r.json();
    const overlay = document.getElementById('card-overlay');

    if (data.detected) {
      document.getElementById('game-badge').textContent  = (data.game || 'CARD').toUpperCase();
      document.getElementById('card-name').textContent   = data.name || '';
      document.getElementById('card-meta').textContent   = [data.year, data.set].filter(Boolean).join(' · ');
      document.getElementById('price-value').textContent = data.price_label || 'N/A';
      document.getElementById('variant-badge').textContent = data.variant || '';

      overlay.classList.add('visible');

      if (hideTimer) clearTimeout(hideTimer);
      hideTimer = setTimeout(() => overlay.classList.remove('visible'), data.display_seconds * 1000);
    }
  } catch(e) {}
}

setInterval(poll, 500);
poll();
</script>
</body>
</html>"""


@app.route("/overlay")
def overlay():
    return render_template_string(OVERLAY_HTML)


@app.route("/api/current-card")
def api_current_card():
    with _state_lock:
        data = dict(current_card)
    data["display_seconds"] = DISPLAY_SECONDS
    return jsonify(data)


if __name__ == "__main__":
    port = CONFIG.get("overlay_port", 5050)
    print(f"Overlay server running at http://localhost:{port}/overlay")
    print("Add this URL as a Browser Source in OBS (400x300)\n")
    app.run(host="0.0.0.0", port=port, debug=False)
