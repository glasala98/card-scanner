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

## Testing

Install test dependencies then run the full suite:

```bash
pip install pytest
pytest tests/ -v
```

Expected output:

```
tests/test_cache.py::test_cache_miss_returns_none          PASSED
tests/test_cache.py::test_cache_hit_returns_data           PASSED
tests/test_cache.py::test_cache_different_keys_isolated    PASSED
tests/test_cache.py::test_cache_overwrite                  PASSED
tests/test_cache.py::test_cache_expires_after_ttl          PASSED
tests/test_cache.py::test_cache_valid_before_ttl           PASSED

tests/test_motion.py::test_none_frames_always_differ       PASSED
tests/test_motion.py::test_identical_frames_do_not_differ  PASSED
tests/test_motion.py::test_identical_copy_does_not_differ  PASSED
tests/test_motion.py::test_large_difference_triggers_motion PASSED
tests/test_motion.py::test_small_difference_below_threshold PASSED
tests/test_motion.py::test_small_difference_above_custom_threshold PASSED
tests/test_motion.py::test_noisy_region_triggers_motion    PASSED

tests/test_price_routing.py::test_routes_nhl               PASSED
tests/test_price_routing.py::test_routes_nba               PASSED
tests/test_price_routing.py::test_routes_nfl               PASSED
tests/test_price_routing.py::test_routes_mlb               PASSED
tests/test_price_routing.py::test_routes_pokemon           PASSED
tests/test_price_routing.py::test_routes_pokemon_accent    PASSED
tests/test_price_routing.py::test_routes_mtg               PASSED
tests/test_price_routing.py::test_routes_magic             PASSED
tests/test_price_routing.py::test_routes_yugioh            PASSED
tests/test_price_routing.py::test_routes_yugioh_dash       PASSED
tests/test_price_routing.py::test_unknown_game_defaults_to_sports PASSED
tests/test_price_routing.py::test_empty_game_defaults_to_sports   PASSED
tests/test_price_routing.py::test_lookup_error_returns_empty_dict PASSED

tests/test_claude_parsing.py::test_valid_card_detected     PASSED
tests/test_claude_parsing.py::test_no_card_detected        PASSED
tests/test_claude_parsing.py::test_strips_markdown_code_fence PASSED
tests/test_claude_parsing.py::test_strips_plain_code_fence PASSED
tests/test_claude_parsing.py::test_invalid_json_returns_not_detected PASSED
tests/test_claude_parsing.py::test_claude_api_exception_returns_not_detected PASSED
tests/test_claude_parsing.py::test_partial_response_survives PASSED

tests/test_server.py::test_overlay_returns_200             PASSED
tests/test_server.py::test_overlay_contains_poll_script    PASSED
tests/test_server.py::test_overlay_content_type_html       PASSED
tests/test_server.py::test_api_no_card_detected            PASSED
tests/test_server.py::test_api_card_detected               PASSED
tests/test_server.py::test_api_includes_display_seconds    PASSED
tests/test_server.py::test_api_response_is_json            PASSED
tests/test_server.py::test_api_state_isolation             PASSED

tests/test_modes.py::TestSports::test_returns_price_on_match          PASSED
tests/test_modes.py::TestSports::test_returns_no_price_on_empty       PASSED
tests/test_modes.py::TestSports::test_returns_no_price_when_fair_value_missing PASSED
tests/test_modes.py::TestSports::test_lookup_error_on_exception       PASSED
tests/test_modes.py::TestPokemon::test_returns_holofoil_price         PASSED
tests/test_modes.py::TestPokemon::test_falls_back_to_normal           PASSED
tests/test_modes.py::TestPokemon::test_falls_back_to_mid_when_no_market PASSED
tests/test_modes.py::TestPokemon::test_no_cards_returns_no_data       PASSED
tests/test_modes.py::TestPokemon::test_exception_returns_lookup_error PASSED
tests/test_modes.py::TestMTG::test_returns_usd_price                  PASSED
tests/test_modes.py::TestMTG::test_falls_back_to_foil                 PASSED
tests/test_modes.py::TestMTG::test_no_price_returns_no_data           PASSED
tests/test_modes.py::TestMTG::test_exception_returns_lookup_error     PASSED
tests/test_modes.py::TestYuGiOh::test_returns_tcgplayer_price         PASSED
tests/test_modes.py::TestYuGiOh::test_zero_price_returns_no_data      PASSED
tests/test_modes.py::TestYuGiOh::test_no_data_returns_no_price        PASSED
tests/test_modes.py::TestYuGiOh::test_exception_returns_lookup_error  PASSED

============= 54 passed in 1.23s =============
```

### What's tested

| Module | Tests | Coverage |
|--------|-------|----------|
| `scanner.py` — motion detection | 7 | `frames_differ()` with identical, similar, and very different frames |
| `scanner.py` — cache | 6 | miss, hit, TTL expiry, key isolation, overwrite |
| `scanner.py` — price routing | 13 | all 4 game types + aliases + unknown + error handling |
| `scanner.py` — Claude parsing | 7 | valid card, no card, markdown fences, bad JSON, API errors |
| `server.py` — Flask endpoints | 8 | `/overlay` HTML, `/api/current-card` state, JSON format |
| `modes/` — all 4 price APIs | 17 | happy path, empty results, fallbacks, network errors |

All tests mock network calls — no real API keys or internet connection needed.

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
└── tests/
│   ├── test_motion.py       # Motion detection unit tests
│   ├── test_cache.py        # Cache TTL unit tests
│   ├── test_price_routing.py # Game routing unit tests
│   ├── test_claude_parsing.py # Claude Vision response parsing tests
│   ├── test_server.py       # Flask endpoint tests
│   └── test_modes.py        # Price API mode tests
└── TODO.md             # Roadmap
```

## Roadmap

See [TODO.md](TODO.md) for the full feature roadmap (hotkeys, multi-card, style variants, etc.).
