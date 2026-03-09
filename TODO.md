# Card Scanner — OBS Live Stream Overlay

Real-time card identification overlay for OBS. Hold a card up to your webcam,
Claude Vision identifies it, price is pulled from the relevant API, and it
displays on stream as a browser source overlay.

---

## Architecture

```
card-scanner/
├── scanner.py        # Main loop: webcam capture → motion detect → Claude Vision → price lookup
├── server.py         # Flask server: serves overlay.html + /api/current-card endpoint
├── overlay.html      # OBS Browser Source overlay (polls /api/current-card every 500ms)
├── config.json       # Webcam index, API keys, active mode, overlay style
├── modes/
│   ├── sports.py     # Sports cards → CardDB API (NHL/NBA/NFL/MLB)
│   ├── pokemon.py    # Pokémon TCG → pokemontcg.io API
│   ├── mtg.py        # Magic: The Gathering → Scryfall API
│   └── yugioh.py     # Yu-Gi-Oh → YGOPRODeck API
└── requirements.txt
```

---

## TODO

### Phase 1 — Core Pipeline
- [ ] `scanner.py` — webcam capture loop using OpenCV
- [ ] Motion detection — only fire Claude when frame changes significantly (card appears)
- [ ] Claude Vision integration — identify card name, set, sport/game type
- [ ] Result caching — same card within 30s returns instantly without re-calling Claude
- [ ] `server.py` — Flask serving current card state at `/api/current-card`
- [ ] `config.json` — webcam index, API keys, active mode

### Phase 2 — Price Lookup Modes
- [ ] `modes/sports.py` — query CardDB API at southwestsportscards.ca/api for price data
- [ ] `modes/pokemon.py` — pokemontcg.io API (free, no key needed for basic use)
- [ ] `modes/mtg.py` — Scryfall API (free, no key needed)
- [ ] `modes/yugioh.py` — YGOPRODeck API (free, no key needed)
- [ ] Auto-detect game type from Claude response (Claude identifies sport vs Pokémon vs MTG etc.)

### Phase 3 — OBS Overlay
- [ ] `overlay.html` — dark themed card overlay panel (Bloomberg-style to match CardDB)
  - Card name + set + year
  - Market value (raw + graded if available)
  - Card image (from eBay/TCG API)
  - Animated slide-in when card detected, fade-out after 8 seconds
- [ ] OBS Browser Source setup instructions
- [ ] Overlay style variants (corner widget, full panel, minimal)

### Phase 4 — Polish
- [ ] Hot-key to manually trigger scan (for when motion detection misses)
- [ ] Hot-key to clear overlay
- [ ] Mode switcher — cycle through Sports/Pokémon/MTG/YuGiOh live
- [ ] Confidence threshold — only show overlay if Claude is >80% confident
- [ ] Multi-card support — detect multiple cards in frame simultaneously

---

## API Sources

| Mode | API | Cost |
|------|-----|------|
| Sports | southwestsportscards.ca/api | Free (own DB) |
| Pokémon | api.pokemontcg.io | Free tier |
| MTG | api.scryfall.com | Free |
| Yu-Gi-Oh | db.ygoprodeck.com/api | Free |

## Dependencies
- `opencv-python` — webcam capture + motion detection
- `anthropic` — Claude Vision API
- `flask` — overlay server
- `requests` — price API calls
- `pillow` — image processing

## OBS Setup
1. Run `python server.py`
2. OBS → Sources → Add → Browser Source
3. URL: `http://localhost:5050/overlay`
4. Width: 400, Height: 300
5. Position overlay in corner of scene
