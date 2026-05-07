# 🎨 Razer Crimson Royale
**Custom Razer keyboard & mouse lighting via the Chroma REST API — no Chroma Studio needed.**

Built by [PopcornKitsilano](https://github.com/PopcornKitsilano)

---

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🖼️ What it looks like

Animated red → pink → magenta → purple → violet wave flowing across the keyboard, with 5 rotating patterns:
- **wave_lr** — left to right sweep
- **wave_rl** — right to left sweep
- **wave_tb** — top to bottom sweep
- **pulse** — whole keyboard pulses through colors together
- **diagonal** — diagonal color sweep

WASD, arrow keys, and Caps Lock are always locked to **bright red** for instant spotting during gameplay. Right Ctrl stays **hot pink**.

---

## ⚡ Why use this instead of Razer Synapse / Chroma Studio?

| | Razer Synapse / Chroma Studio | This Script |
|---|---|---|
| Per-key color control | ✅ but manual clicking | ✅ fully automatic |
| Animated patterns | Limited presets only | Custom code — anything possible |
| Overrides your lighting | Yes, constantly | You control when it runs |
| Locks specific keys (WASD) | Manual only | Always locked in code |
| Pattern speed control | No | Yes — change 2 numbers |
| Runs silently in background | No (full app) | Yes — just a CMD window |
| Open source / customizable | No | Yes — it's your code |
| Requires clicking around UI | Yes | No — one command |

**The biggest advantage:** Synapse's Chroma Studio treats your keyboard as a canvas you paint manually. This script programmatically controls every key every frame, so you can do things Chroma Studio simply cannot — like animated waves, per-key logic, game-reactive lighting, or anything else you can code.

---

## 🛠️ What you need

### Required software
- **Razer Synapse 4** — must be installed and running. Download from [razer.com/synapse](https://www.razer.com/synapse-4)
- **Python 3.8 or higher** — [python.org/downloads](https://www.python.org/downloads/)
- **requests library** — installed via pip (see below)

### Compatible hardware
Tested on:
- Razer Cynosa V2 (keyboard)
- Razer Basilisk (mouse)

Should work on any Razer Chroma-enabled device.

---

## 📦 Installation

### 1. Install Python
Download from [python.org](https://www.python.org/downloads/) and run the installer.

> ⚠️ **Important:** During installation, check the box that says **"Add Python to PATH"** before clicking Install. If you miss this, Python won't be found in CMD.

Verify it installed correctly:
```
python --version
```
You should see something like `Python 3.12.10`.

Alternatively, install via winget:
```
winget install --id Python.Python.3.12
```

### 2. Install the requests library
```
pip install requests
```

### 3. Clone this repo
```
git clone https://github.com/PopcornKitsilano/razer-crimson-royale
cd razer-crimson-royale
```

Or just download `razer_chroma_colors.py` directly.

---

## ▶️ Running the script

> ⚠️ **Must run as Administrator.** Right-click CMD → Run as administrator. Without this, the Chroma SDK may accept commands but not apply them physically.

```
python razer_chroma_colors.py
```

You should see:
```
Razer - CRIMSON ROYALE ANIMATED WAVE
========================================
Session: {'sessionid': 58943, 'uri': 'http://localhost:58943/chromasdk'}
URL: http://localhost:58943/chromasdk
Starting with pattern: wave_lr
Ctrl+C to stop.
```

Your keyboard and mouse will light up immediately.

Press **Ctrl+C** to stop. Colors revert to Synapse default when the script exits.

---

## 🌐 How to verify the Chroma REST API is running

The Chroma SDK runs a local REST API on your machine while Synapse is open. You can verify it is live by opening your browser and going to:

```
http://localhost:54235/razer/chromasdk
```

If the API is running, you will see a JSON response like this:
```json
{"core":"3.39.02","device":"3.40.02","version":"3.40.02"}
```

**Port 54235** is the fixed entry point for the Chroma SDK — this never changes. It is always `localhost:54235`. This is where the script registers itself as an app.

After registration, the SDK assigns your app its own **dynamic session port** (e.g. `localhost:58943`). All subsequent keyboard/mouse commands go to that session port, not 54235. The script handles this automatically.

If you visit your session URL in the browser (e.g. `http://localhost:58943/chromasdk`) it will say "not supported" — that is normal. It is an API endpoint, not a web page.

If `localhost:54235` returns nothing or an error, Razer Synapse is not running or the Chroma SDK service has not started yet. Restart Synapse and try again.

---

## 🔧 How the code works — full explanation

### The Chroma REST API

Razer Synapse exposes a local HTTP REST API called the **Chroma SDK**. Any application on your PC can talk to it to control lighting on your Razer devices. This is how games like Fortnite or Valorant sync their lighting effects — they use this exact same API.

The script bypasses Chroma Studio entirely and talks to the SDK directly using Python's `requests` library.

### Step 1 — App registration

Before sending any lighting commands, the script registers itself as a "Chroma app":

```python
APP_INFO = {
    "title": "Crimson Royale",
    "description": "Custom purple/red keyboard lighting",
    "author": {"name": "User", "contact": "user@example.com"},
    "device_supported": ["keyboard","mouse","mousepad","headset","chromalink"],
    "category": "application"
}

r = requests.post("http://localhost:54235/razer/chromasdk", json=APP_INFO)
session = r.json()
# Returns: {'sessionid': 58943, 'uri': 'http://localhost:58943/chromasdk'}
```

The SDK returns a **session URL** — a unique local port just for your app. All commands go there from now on. You will see "Crimson Royale (Chroma Apps)" appear in Synapse's lighting panel, confirming your app has taken control.

### Step 2 — Color encoding

Razer uses **BGR format** instead of the standard RGB. The byte order is reversed:

```python
def bgr(hex_color):
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (b << 16) | (g << 8) | r  # Blue in high byte, Red in low byte
```

So `#FF0000` (pure red in RGB) becomes `0x0000FF` in Razer's BGR. If you skip this and send raw RGB values, your colors will look completely wrong — reds become blues and vice versa.

### Step 3 — The keyboard grid

The Cynosa V2 keyboard is addressed as a **6 row × 22 column grid**. Each cell in the grid is a BGR integer representing the color of that key. Empty positions (gaps between key groups) are set to `0` (black/off).

```python
grid = [[0]*22 for _ in range(6)]
grid[2][2] = bgr("#FF0000")  # Row 2, Col 2 = W key = Red
grid[3][1] = bgr("#FF0000")  # Row 3, Col 1 = A key = Red
```

Row/column reference for key positions:
```
Row 0: ESC  F1-F12  PRTSCR SCRLK PAUSE
Row 1: `  1-0  -  =  BKSP  |  INS HOME PGUP  |  NUMLK / * -
Row 2: TAB  Q W E R T Y U I O P  [ ] \  |  DEL END PGDN  |  7 8 9 +
Row 3: CAPS  A S D F G H J K L  ; '  ENTER  |  4 5 6
Row 4: LSHIFT  Z X C V B N M  , . /  RSHIFT  |  UP  |  1 2 3 ENTER
Row 5: LCTRL WIN LALT  SPACE  RALT FN MENU RCTRL  |  LEFT DOWN RIGHT  |  0 . 
```

The grid is sent to the API using the `CHROMA_CUSTOM` effect:

```python
requests.put(
    f"{session_url}/keyboard",
    json={"effect": "CHROMA_CUSTOM", "param": grid}
)
```

### Step 4 — The gradient

Colors are generated by interpolating between defined color stops:

```python
STOPS = [
    (0.00, 255,   0,   0),   # Red
    (0.28, 255,   0, 160),   # Hot Pink
    (0.42, 255,   0, 255),   # Magenta
    (0.57, 180,   0, 255),   # Purple
    (0.71, 100,   0, 255),   # Deep Purple
    (0.85,  50,   0, 255),   # Blue Violet
    (1.00, 255,   0,   0),   # Red (loop back)
]
```

Each key's column position (0 to 1) is mapped into this gradient to get its color. The result is a smooth rainbow flowing left to right across the keyboard.

### Step 5 — Animation

The wave moves by shifting a global `offset` value each frame:

```python
offset = (offset + 0.05) % 1.0
```

Each key's gradient position becomes `(col_position - offset) % 1.0`. As offset increases each frame, the gradient appears to scroll across the keyboard. The script sleeps between frames to control speed:

```python
time.sleep(0.15)  # 0.15 seconds per frame = ~6 fps
```

### Step 6 — Patterns

Five patterns control how the gradient maps to key positions:

```python
if pattern == "wave_lr":
    pos = col/16.0 - offset          # left to right
elif pattern == "wave_rl":
    pos = 1.0 - col/16.0 - offset    # right to left
elif pattern == "wave_tb":
    pos = row/5.0 - offset           # top to bottom
elif pattern == "pulse":
    pos = offset                     # whole keyboard same color
elif pattern == "diagonal":
    pos = (col/16.0 + row/5.0)/2.0 - offset  # diagonal sweep
```

Patterns rotate automatically every `FRAMES_PER_PATTERN` frames.

### Step 7 — Heartbeat

The Chroma SDK requires a heartbeat ping every few seconds to keep the session alive. Without it, the SDK assumes your app crashed and reverts control back to Synapse:

```python
requests.put(f"{session_url}/heartbeat", timeout=3)
```

---

## ⚙️ Customization — what to change

### Animation speed

Find these two lines near the bottom of the main loop:

```python
offset = (offset + 0.05) % 1.0   # gradient jump per frame
time.sleep(0.15)                  # delay between frames
```

| Feel | offset step | sleep |
|------|------------|-------|
| Very slow | `0.01` | `0.5` |
| Slow | `0.02` | `0.3` |
| Default | `0.05` | `0.15` |
| Fast | `0.07` | `0.08` |
| Very fast | `0.1` | `0.05` |

### Pattern duration

```python
FRAMES_PER_PATTERN = 150   # frames before switching pattern
```
At 0.15s per frame, 150 frames ≈ 22 seconds. Change to `300` for ~45 seconds, `75` for ~11 seconds.

### Colors

Edit the `STOPS` list to change the gradient palette. Each stop is `(position, R, G, B)` where position is 0.0 to 1.0:

```python
STOPS = [
    (0.00, 255,   0,   0),   # change these RGB values
    (0.50, 100,   0, 255),   # add or remove stops
    (1.00, 255,   0,   0),   # always end same as start for smooth loop
]
```

### Locked keys

WASD, arrows, Caps Lock are defined as sets of `(row, col)` tuples:

```python
WASD   = {(2,2),(3,1),(3,2),(3,3)}
ARROWS = {(4,15),(5,14),(5,15),(5,16)}
CAPS   = {(3,0)}
RCTRL  = {(5,13)}
```

Change their colors here:
```python
for (r,c) in WASD|ARROWS|CAPS:
    grid[r][c] = RED       # change RED to any bgr() color
for (r,c) in RCTRL:
    grid[r][c] = HOTPINK   # change HOTPINK to any bgr() color
```

### Adding a new pattern

Add a new condition in `build_grid()`:

```python
elif pattern == "your_pattern_name":
    pos = math.sin(col/3.0 + offset * 6) * 0.5 + 0.5  # example: sine wave
```

Then add it to the patterns list:
```python
PATTERNS = ["wave_lr", "wave_rl", "wave_tb", "pulse", "diagonal", "your_pattern_name"]
```

---

## 🔄 Run on Windows startup (optional)

To have the lighting apply automatically every time you boot:

1. Press `Win + R` → type `shell:startup` → Enter
2. Create a new text file, rename it `razer_lighting.bat`
3. Edit it and add:
```batch
@echo off
cd C:\Users\YourUsername\Downloads
python razer_chroma_colors.py
```
4. Save it — it will run at every login

> Note: You may need to configure it to run as administrator for it to work correctly. Right-click the .bat file → Properties → Advanced → check "Run as administrator".

---

## 📁 Files

```
razer-crimson-royale/
├── razer_chroma_colors.py   # main script
└── README.md                # this file
```

---

## 🤝 Contributing

Feel free to fork, modify patterns, add new effects, or submit a PR. Ideas welcome:
- Reactive typing effects (key lights up on press)
- Game-specific profiles
- Audio-reactive lighting using mic input
- Health bar lighting for specific games

---

## 📄 License

MIT — do whatever you want with it.
