# Card Scanner — OBS Overlay

Live trading card identifier for OBS streams. Points a webcam at a card, uses Claude Vision to identify it, and displays the card name + price as a browser source overlay.

## Supported Games

| Game | Price Source |
|------|-------------|
| Sports Cards | CardDB API (southwestsportscards.ca) |
| Pokémon TCG | pokemontcg.io |
| Magic: The Gathering | Scryfall |
| Yu-Gi-Oh | YGOPRODeck |

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure `.env`
Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_key_here
```

### 3. Configure `config.json`
```json
{
  "webcam_index": 0,
  "motion_threshold": 30,
  "motion_min_area": 5000,
  "cooldown_seconds": 5,
  "overlay_display_seconds": 8,
  "carddb_api_url": "https://southwestsportscards.ca/api",
  "flask_port": 5050
}
```
- `webcam_index` — camera device index (0 = default webcam, 1 = next, etc.)
- `motion_threshold` — pixel difference sensitivity for motion detection
- `cooldown_seconds` — minimum seconds between Claude API calls
- `overlay_display_seconds` — how long the card overlay stays visible after detection

### 4. Start the scanner
```bash
python scanner.py   # webcam capture + Claude Vision
python server.py    # Flask overlay server (separate terminal)
```

### 5. Add to OBS
1. OBS → Sources → `+` → **Browser Source**
2. URL: `http://localhost:5050/overlay`
3. Width: `400`, Height: `200`
4. Enable: **Refresh browser when scene becomes active**
5. Position the source where you want the overlay to appear

## How It Works

```
Webcam → Motion Detection → Claude Vision → Price Lookup → OBS Browser Source
```

1. `scanner.py` captures webcam frames and watches for motion
2. When motion is detected and a card is held steady, a frame is sent to Claude Vision
3. Claude returns the card game, name, set, year, and confidence
4. The appropriate price API is queried based on game type
5. `server.py` serves the result at `/api/current-card`
6. The OBS browser source at `localhost:5050/overlay` polls every 500ms and animates the card info in

## Project Structure

```
card-scanner/
├── scanner.py          # Webcam loop + Claude Vision + price routing
├── server.py           # Flask server (OBS browser source)
├── scan_reference.py   # Standalone: scan a saved image file
├── config.json         # Webcam index, thresholds, ports
├── requirements.txt
├── .env                # ANTHROPIC_API_KEY (git-ignored)
├── modes/
│   ├── sports.py       # CardDB API
│   ├── pokemon.py      # pokemontcg.io
│   ├── mtg.py          # Scryfall
│   └── yugioh.py       # YGOPRODeck
└── TODO.md             # Roadmap
```

## Roadmap

See [TODO.md](TODO.md) for the full feature roadmap (hotkeys, multi-card, style variants, etc.).
