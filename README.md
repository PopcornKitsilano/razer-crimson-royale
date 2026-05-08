# Razer Crimson Royale — Ultimate Spectrum Engine v4.0

Custom animated RGB lighting engine for Razer keyboards and mice, built entirely in Python.
Communicates directly with the Razer Chroma REST API without using Chroma Studio, iCUE, SignalRGB, or any other third-party lighting software.

Built by [PopcornKitsilano](https://github.com/PopcornKitsilano)

---

## Why this project exists

Every major RGB lighting platform — Razer Chroma Studio, Corsair iCUE, SignalRGB, OpenRGB — shares the same fundamental limitation: they are GUI applications. To change an effect, you open the software, navigate menus, click buttons, and configure settings through a graphical interface. You cannot script them. You cannot define a custom playlist programmatically. You cannot write code that says "run effect 3 for 40 seconds, then effect 7 for 20 seconds, then loop." You are always working within whatever the software lets you do.

This project eliminates that entirely. It is a single Python script that talks directly to the hardware-level REST API that Razer Synapse exposes on your local machine. Everything is controlled through a terminal menu that runs when you launch the script. You type your choices — which effects, in what order, at what speed, in which direction, for how long — and the engine executes them. No clicking. No navigating menus. No GUI. Just a script and a terminal.

The result is a lighting engine that can do things no existing RGB software can do out of the box:
- Run 20 different animated effects sourced from Razer, Corsair iCUE, SignalRGB, and OpenRGB in a single script
- Accept a user-defined playlist in any order at runtime
- Control speed with a single multiplier that affects every effect uniformly
- Reverse the direction of any directional effect
- Lock specific keys (WASD, arrow keys, Caps Lock, Right Ctrl) to fixed colors that persist through every effect regardless of what the animation is doing
- Run as a lightweight background process consuming almost no resources

---

## How this compares to existing lighting software

### Razer Chroma Studio
Chroma Studio is a canvas-based editor. You paint colors onto a visual keyboard layout by hand. It supports a small number of built-in animated effects (wave, breathing, reactive, starlight, spectrum cycling) but these cannot be combined, sequenced, or scripted. Speed control is limited to a slider with no numeric precision. There is no concept of a playlist. You cannot say "play aurora for 30 seconds then switch to ripple." You paint and save a static profile. This engine does everything Chroma Studio does and adds 14 effects Chroma Studio does not have, with full runtime configurability.

### Corsair iCUE
iCUE is a heavier application with more effects than Chroma Studio, including per-column breathing and lightning effects. It is device-locked to Corsair hardware and cannot be used on Razer devices. Its effects cannot be scripted or ordered programmatically. This engine replicates every iCUE effect that was worth replicating and makes them available on Razer hardware.

### SignalRGB
SignalRGB has the best effect library of any consumer RGB software, including aurora borealis, rainfall, comet streaks, and diagonal wave patterns that most other platforms lack. It supports a wide range of hardware brands. However it requires installation of a background service, a full GUI application, and account creation. Effects are configured through the GUI and cannot be ordered or scripted. This engine takes the most interesting SignalRGB effects and implements them from scratch in pure Python math.

### OpenRGB
OpenRGB is open source and hardware-agnostic. It has fewer effects but supports color shift and radial burst patterns. It is still a GUI application. This engine includes the OpenRGB effects that are not covered by the other platforms.

### This engine
One Python file. One terminal. 20 effects. Full control over order, speed, direction, and duration through a menu that runs in seconds. No installation beyond Python and one pip package. No account. No background service beyond Razer Synapse which you need anyway to drive Razer hardware. Runs as administrator, takes control of the hardware directly, and gives it back when you press Ctrl+C.

---

## Effect list — all 20, with technical explanation

The following effects are implemented. Each is a pure Python function that takes a time value `t`, a speed multiplier `sp`, and a direction boolean `fwd`, and returns a fully computed 6x22 integer grid representing the color of every key on the keyboard. The math behind each one is explained in detail.

---

### 01. Wave Left to Right

Source platform: Razer, iCUE, SignalRGB, OpenRGB — present on every platform.

The color at each key is determined by mapping its column position (0 to 1) into a spectrum gradient, then subtracting a time offset that increases each frame. As the offset increases, every key's color position shifts forward in the spectrum, creating the appearance of colors flowing left to right across the keyboard.

```python
pos = c/16.0 - t * sp * 0.4
grid[r][c] = spectrum(pos)
```

Column 0 (leftmost) always has a slightly earlier spectrum position than column 16 (rightmost). The gradient between them produces the visible wave. The time term `t * sp * 0.4` moves that gradient forward each frame.

Direction reversal flips the column term: `1.0 - c/16.0 - t * sp * 0.4`. This makes colors appear to flow right to left instead.

---

### 02. Wave Right to Left

Source platform: Razer, SignalRGB.

Identical to Wave Left to Right but the column position term is inverted. Colors that were on the right appear on the left and vice versa. The wave flows from right to left.

Direction toggle reverses it back to left-to-right, making this effect and effect 01 mirrors of each other when direction is set to reverse.

---

### 03. Wave Top to Bottom

Source platform: Razer, iCUE.

Instead of mapping column position into the spectrum, row position is used. Row 0 (top, function key row) gets the earliest spectrum position. Row 5 (bottom, spacebar row) gets the latest. Colors flow downward. Speed and direction controls work identically to the horizontal waves.

```python
pos = r/5.0 - t * sp * 0.4
```

---

### 04. Wave Bottom to Top

Source platform: iCUE (exclusive direction — Razer only offers top-to-bottom natively).

The same as wave top to bottom but the row term is inverted: `1.0 - r/5.0`. Colors flow upward from the spacebar row toward the function key row. This direction is not available in Razer Chroma Studio natively.

---

### 05. Diagonal NW to SE

Source platform: SignalRGB.

Both the column position and row position are combined into a single gradient position by averaging them. This creates a gradient that runs diagonally from the top-left corner of the keyboard to the bottom-right corner. The wave sweeps in that diagonal direction.

```python
pos = (c/16.0 + r/5.0) * 0.5 - t * sp * 0.35
```

Keys in the top-left corner (Esc, Tab area) share similar gradient positions with each other, and keys toward the bottom-right corner (numpad, Shift area) share similar positions with each other. The 0.5 multiplier normalizes the combined position back to the 0–1 range.

---

### 06. Diagonal NE to SW

Source platform: SignalRGB.

The column term is inverted before being combined with the row term. This flips the diagonal axis from NW-SE to NE-SW. The wave sweeps from the top-right corner (F12, numpad area) toward the bottom-left corner (Ctrl, Shift area).

```python
pos = (1.0 - c/16.0 + r/5.0) * 0.5 - t * sp * 0.35
```

---

### 07. Vortex / Spiral

Source platform: SignalRGB — not available in Razer Chroma Studio or iCUE.

This is the most mathematically complex of the directional effects. The color at each key is determined by its angle relative to the center of the keyboard, plus a distance component that causes the gradient to spiral outward rather than rotate as a solid block.

```python
cx, cy = COLS/2.0, ROWS/2.0
angle = math.atan2(r - cy, c - cx) / (2 * math.pi)   # 0.0 to 1.0 around full circle
dist  = math.sqrt((c-cx)**2 + (r-cy)**2) * 0.07       # radial distance, scaled
pos   = angle + dist - t * sp * 0.3
```

`atan2` returns the angle in radians from the center point to each key. Dividing by 2*pi normalizes it to 0–1. Adding the distance term makes keys further from the center have a different color position than keys at the same angle but closer in, creating the spiral appearance rather than a simple rotation. The time term rotates the entire spiral.

Direction toggle negates the angle term, reversing the rotation from clockwise to counterclockwise.

---

### 08. Radial Burst / Ping Wave

Source platform: OpenRGB.

Colors radiate outward from the center of the keyboard in concentric rings, like a stone dropped in water producing ripples. Unlike the Ripple effect (effect 12) which generates random expanding rings from random points, Radial Burst is a continuous steady outward radiation from a fixed center point.

```python
dist = math.sqrt((c-cx)**2 + (r-cy)**2) * 0.1
pos  = dist - t * sp * 0.4
```

Keys at the same distance from the center share the same color at any given moment, forming visible concentric color rings. The time term moves these rings outward continuously. Direction reversal pulls them inward toward the center instead.

---

### 09. Breathing / Pulse

Source platform: Razer, iCUE — one of the oldest RGB effects.

The entire keyboard fades in and out between full brightness and black using a sine wave for the brightness value. The sine wave produces a natural, smooth fade rather than a linear one, which is why breathing effects look organic rather than mechanical.

```python
bri = (math.sin(t * sp * 1.5) * 0.5 + 0.5) ** 2
```

The `** 2` squares the brightness value. This makes the dark phase longer than the bright phase — the keyboard spends more time near black and pulses to full brightness briefly, which looks more natural than a symmetric in/out fade. A slight spectrum position drift is added so the color slowly shifts while breathing rather than staying static.

This effect does not use the direction toggle as breathing has no meaningful spatial direction.

---

### 10. Per-Column Breathing

Source platform: iCUE — not available in Razer Chroma Studio natively.

Each column of the keyboard breathes independently with a phase offset proportional to its column position. The leftmost column peaks first, then the next column, then the next, creating a ripple of brightness that flows across the keyboard while each individual column fades in and out.

```python
phase = c / COLS * math.pi * 2           # column c gets a unique phase
bri   = (math.sin(t * sp * 1.2 + phase) * 0.5 + 0.5) ** 2
```

At any given moment, some columns are bright and others are dim, producing a shimmering horizontal wave of brightness layered on top of the spectrum gradient. This is distinct from the directional wave effects because the color positions stay fixed — only the brightness oscillates per column.

---

### 11. Starlight

Source platform: Razer exclusive — not available in iCUE, SignalRGB, or OpenRGB natively.

55 keys are selected at script startup with random positions, random peak brightness speeds, random phase offsets, and random hue values from the red/purple/blue family. Each key independently fades in and out according to its own sine wave, creating the appearance of stars twinkling at different rates.

```python
bri = (math.sin(t * speed * sp + phase) * 0.5 + 0.5) ** 3
```

Cubing the brightness value (** 3 rather than ** 2) makes the twinkling more extreme — keys spend most of their time near black and flash to full brightness briefly, like actual stars rather than slow breathing LEDs. Keys that are not in the star set remain black, giving the dark background that makes the twinkling visible.

The star positions are regenerated when the effect is selected in the playlist, so each run of the effect looks different.

---

### 12. Ripple

Source platform: Razer exclusive.

At random intervals (between 1.5 and 3 seconds divided by the speed multiplier), a new ripple origin point is created at a random keyboard position. Each origin spawns an expanding circular ring of color that fades as it grows.

```python
radius    = age * 7.0              # ring expands at 7 units per second of age
brightness = max(0, 1.0 - age/3.0) # fades to black over 3 seconds
dist      = math.sqrt((c-rx)**2 + (r-ry)**2)
diff      = abs(dist - radius)
if diff < 1.8:
    intensity = (1.0 - diff/1.8) * brightness
```

The ring is drawn by finding all keys whose distance from the origin is within 1.8 units of the current radius. Keys exactly at the ring edge get full intensity; keys slightly inside or outside get proportionally less intensity, producing a soft ring rather than a hard circle. The color of each ripple is randomly selected from the red/purple/blue palette. Multiple ripples can exist simultaneously and overlap by blending colors.

The background is a dark purple (HSV 270 degrees, brightness 0.1) rather than black, which makes the rings visible against a colored base rather than appearing on a completely dark keyboard.

---

### 13. Comet Streaks

Source platform: SignalRGB.

Five comets travel horizontally across the keyboard, each on its own row, each with its own speed, tail length, and color. The head of each comet is white (full RGB saturation) and the tail fades through the comet's assigned hue to black.

```python
bri = ((tail_length - i) / tail_length) ** 1.5
# i=0 is the head (white), i=1 onward is the tail with decreasing brightness
```

The 1.5 exponent on the brightness falloff makes the tail dense near the head and fade quickly toward the end, producing the characteristic comet shape where the bright core is prominent and the tail thins rapidly.

When a comet reaches the right edge of the keyboard it reappears at the left edge on a new random row with a new random color, creating continuous motion. Direction reversal makes all comets travel right to left instead.

---

### 14. Aurora Borealis

Source platform: SignalRGB — not available in Razer Chroma Studio or iCUE.

Three independent sine waves are evaluated at each key position and averaged together. Because the three waves have different frequencies and different rates of change, their combination produces organic, non-repeating undulations across the keyboard.

```python
w1 = math.sin(c * 0.35 + t * sp * 0.55) * 0.5 + 0.5
w2 = math.sin(c * 0.65 - t * sp * 0.35 + r * 0.4) * 0.5 + 0.5
w3 = math.sin(c * 0.18 + t * sp * 0.20 + r * 0.6) * 0.5 + 0.5
mix = (w1 + w2 + w3) / 3.0
```

The mixed value determines both the hue and the brightness of each key. Hue ranges from 140 degrees (teal-green) through to 300 degrees (magenta-purple), with brightness between 0.35 and 1.0. This produces the characteristic aurora color palette of greens, teals, and purples that shift and flow across the keyboard in a way that looks like actual aurora curtains.

The three waves move at different speeds and in slightly different directions, so the pattern never visibly repeats. Wave 2 includes a row component (`r * 0.4`) and wave 3 includes a stronger row component (`r * 0.6`), which creates vertical variation in addition to horizontal variation so the aurora flows in two dimensions simultaneously.

---

### 15. Fire

Source platform: iCUE, SignalRGB.

Fire is produced by combining keyboard row position (intensity increases toward the bottom of the keyboard where fire originates) with three layered sine waves that simulate the flicker of flames.

```python
intensity = (ROWS - r) / ROWS     # bottom row = 1.0, top row = 0.0
noise = (math.sin(c * 1.9 + t * sp * 3.6) * 0.12 +
         math.sin(c * 0.7 - t * sp * 5.4) * 0.08 +
         math.sin(c * 3.1 + t * sp * 2.7) * 0.05)
val = max(0.0, min(1.0, intensity + noise))
```

The three noise waves have different frequencies (c * 1.9, c * 0.7, c * 3.1) and different movement speeds, so they combine to produce irregular, non-periodic flickering that avoids the mechanical appearance of a single sine wave. The val result determines the color:

- Below 0.3: dark red (black fading to deep red)
- 0.3 to 0.6: red to orange
- 0.6 to 1.0: orange to yellow-white

This three-stage color mapping produces realistic fire where the base is dark red, the mid flame is orange, and the hottest tips approach yellow-white.

---

### 16. Matrix Rain

Source platform: OpenRGB, SignalRGB.

16 independent drop columns are maintained. Each drop falls from the top of the keyboard to the bottom, leaving a green trail behind it. The head of each drop is bright white-green and the trail fades to black over a length of 3 to 6 rows.

```python
bri = (trail_length - i) / trail_length
grid[head_row][column]   = bgr(200, 255, 200)  # white-green head
grid[trail_row][column]  = hsv(120, 1.0, bri * 0.85)  # green trail
```

When a drop reaches the bottom it resets to the top on a randomly selected column with a new random speed. Multiple drops can share a column at the same time. Direction reversal makes drops fall upward — from the spacebar row toward the function key row — which produces a visually interesting inversion of the classic effect.

This effect intentionally uses green rather than the red/purple/blue palette of other effects because it is a direct recreation of the Matrix rain aesthetic, where green is definitional to the reference.

---

### 17. Lightning

Source platform: iCUE exclusive — not available in Razer Chroma Studio or SignalRGB natively.

At random intervals (2 to 5 seconds) a lightning bolt strikes a random column of the keyboard. The bolt persists for 0.6 seconds and fades rapidly. Each row of the bolt has a slight horizontal jitter applied using a sine function to make the bolt look jagged rather than a straight vertical line.

```python
jitter = int(math.sin(r * 4.3 + column) * 1.2)
```

The jitter is deterministic for each (row, column) pair — the same bolt always has the same shape — but different bolts at different columns produce different shapes, so each strike looks distinct. The color of each strike is randomly selected (yellow, cyan, purple, red, or magenta). The column adjacent to the bolt receives a dimmer version of the color to simulate the ambient glow of real lightning.

---

### 18. Color Shift

Source platform: OpenRGB.

The entire keyboard slowly cycles through the full spectrum together. At any given moment every key on the keyboard is approximately the same color, and that color advances through the spectrum over time. A slight row-based offset means the top row is always slightly ahead of the bottom row in the spectrum cycle, preventing the keyboard from appearing as a completely uniform block of color.

```python
pos = t * sp * 0.2          # overall spectrum position advances slowly
grid[r][c] = spectrum(pos + r * 0.03)   # each row slightly offset
```

This is the simplest effect in terms of computation but produces one of the most visually clean results — the keyboard flows through every color in the spectrum in a slow, even progression.

---

### 19. Rainfall / Drip

Source platform: SignalRGB exclusive — not available in Razer Chroma Studio, iCUE, or OpenRGB.

20 independent raindrops fall from the top of the keyboard. Each drop is 3 keys tall with brightness decreasing from head to tail. When a drop reaches the bottom row a brief splash is rendered on the adjacent columns at reduced brightness, simulating the moment of impact.

```python
# Splash on impact
if row_position >= ROWS - 1:
    for adjacent_col in [column - 1, column + 1]:
        grid[ROWS - 1][adjacent_col] = hsv(hue, 0.6, 0.5)
```

The splash is a single-frame effect on the two keys flanking the impact point. Because drops fall at different speeds and reset at different times, the splash moments are staggered and unpredictable, making the rainfall feel organic rather than synchronized.

Drop colors are drawn from the red/purple/blue palette (hues 240, 270, 300, 0, 330) rather than blue-only, which fits the overall palette of the engine while keeping the rainfall visual clear. Direction reversal makes drops fall upward with the splash occurring at the top row.

---

### 20. Spectrum Cycle

Source platform: Razer, iCUE — one of the oldest and most widely implemented RGB effects.

The simplest continuously animated effect: the entire keyboard slowly advances through the full visible spectrum. Every key is the same color at any moment. Unlike Color Shift (effect 18), there is no per-row offset — the keyboard is a single uniform color block that cycles.

```python
pos = t * sp * 0.15
grid[r][c] = spectrum(pos)    # same pos for all keys
```

The speed multiplier is scaled more gently here (0.15 compared to 0.4 for the wave effects) because a slowly cycling spectrum cycle at normal speed is already quite fast visually. The 0.15 factor makes the default speed feel like a slow, meditative color drift through the full spectrum.

---

## The color engine — full spectrum with red/purple/blue priority

All 20 effects use the same underlying color engine. Colors are generated in HSV (Hue-Saturation-Value) space and converted to Razer's BGR integer format.

### Why HSV instead of RGB

RGB interpolation produces ugly, desaturated midpoints. Interpolating from red (255,0,0) to blue (0,0,255) through RGB passes through unsaturated purple-grey in the middle. HSV interpolation stays on the color wheel — interpolating from red (0 degrees) to blue (240 degrees) passes through vivid orange, yellow, green, and cyan, all at full saturation.

### Why BGR not RGB

Razer's Chroma SDK uses BGR byte order (Blue-Green-Red) rather than the standard RGB order. The conversion is:

```python
def bgr(r, g, b):
    return (b << 16) | (g << 8) | r
```

Blue occupies the high byte, red the low byte. Sending raw RGB values without this conversion produces completely wrong colors — pure red appears as pure blue, greens appear correct (they occupy the middle byte in both formats).

### The spectrum stop table

The visible spectrum is mapped onto a 0.0–1.0 position scale using a stop table that controls how much of the spectrum range each hue occupies:

```
Position 0.00 → Hue 0    (Red)
Position 0.32 → Hue 240  (Blue)
Position 0.50 → Hue 270  (Purple)
Position 0.70 → Hue 300  (Magenta)
Position 0.86 → Hue 330  (Rose)
Position 1.00 → Hue 0    (Red, loops)

Green (120) appears at position 0.19
Cyan  (180) appears at position 0.22
```

Red, purple, and blue each occupy large ranges (0.00–0.07 for red, 0.32–0.50 for blue, 0.50–0.70 for purple). Green and cyan occupy narrow ranges (0.19–0.22 combined), so they pass through briefly rather than dominating. The full spectrum is still present — no hue is excluded — but the weighting produces a palette that reads as primarily red/purple/blue with occasional green and cyan flashes.

---

## How the Chroma REST API works

Razer Synapse exposes a local HTTP REST API on port 54235 while it is running. This API is used by games like Fortnite and Valorant to sync keyboard lighting with in-game events. This project uses the exact same API.

### Verifying the API is active

Open a browser and navigate to:

```
http://localhost:54235/razer/chromasdk
```

If Synapse is running you will see a JSON response:
```json
{"core":"3.39.02","device":"3.40.02","version":"3.40.02"}
```

If nothing loads: Synapse is not running, or the Chroma SDK service has not started. Restart Synapse and wait 10 seconds.

### Port 54235 vs session port

Port 54235 is the permanent fixed registration endpoint. It never changes. The script sends one POST request to this port to register itself as a Chroma application.

The API responds with a dynamic session URL on a different port specific to this session:
```json
{"sessionid": 58943, "uri": "http://localhost:58943/chromasdk"}
```

All subsequent keyboard and mouse commands go to that session URL (`http://localhost:58943/chromasdk`), not 54235. The session port changes every time you run the script. The script handles this automatically.

If you visit the session URL in a browser it will display "not supported" — this is expected. It is an HTTP API endpoint, not a web page.

### Registration requirements

Two things cause registration to fail with error 87:

1. The `contact` field in APP_INFO must not be an empty string. Even a placeholder value like `"user@example.com"` is required.
2. The `device_supported` list must include all five device types: `keyboard`, `mouse`, `mousepad`, `headset`, `chromalink`. Listing only `keyboard` and `mouse` causes rejection.

### Synapse permission

For the colors to appear physically on the hardware (not just in the API response), two conditions must be met:

1. The script must run as Administrator.
2. In Razer Synapse, the device lighting tab must be set to "Advanced Effects" mode, and the option to allow third-party apps must be enabled. When the script is running, Synapse will display "Chroma Spectrum Engine (Chroma Apps)" in the lighting panel confirming that the script has taken control.

### Heartbeat

The Chroma SDK requires a heartbeat request every few seconds to keep the session alive. Without it, the SDK assumes the controlling application has crashed and hands lighting control back to Synapse:

```python
requests.put(f"{session_url}/heartbeat", timeout=3)
```

The engine sends a heartbeat every 25 frames (~3.5 seconds at 7 fps).

---

## The keyboard grid

The Razer Cynosa V2 keyboard is addressed as a 6-row by 22-column integer grid. Each cell contains a BGR integer. Cells corresponding to physical gaps between key groups (the gap between F4 and F5, the gap between the main keyboard and numpad, etc.) are set to 0 (off).

```
Row 0  col 0    : ESC
Row 0  col 2-5  : F1-F4
Row 0  col 6-9  : F5-F8
Row 0  col 10-13: F9-F12
Row 0  col 14-16: PrtScr, ScrlLk, Pause

Row 1  col 0    : grave/tilde
Row 1  col 1-10 : 1 through 0
Row 1  col 11-12: minus, equals
Row 1  col 13   : Backspace
Row 1  col 14-16: Insert, Home, PageUp
Row 1  col 18-21: NumLk, Num/, Num*, Num-

Row 2  col 0    : Tab
Row 2  col 1-13 : Q through backslash
Row 2  col 14-16: Delete, End, PageDown
Row 2  col 18-21: Num7, Num8, Num9, Num+

Row 3  col 0    : Caps Lock
Row 3  col 1-11 : A through apostrophe
Row 3  col 13   : Enter
Row 3  col 18-20: Num4, Num5, Num6

Row 4  col 0    : Left Shift
Row 4  col 2-13 : Z through Right Shift
Row 4  col 15   : Up Arrow
Row 4  col 18-21: Num1, Num2, Num3, NumEnter

Row 5  col 0-2  : Left Ctrl, Win, Left Alt
Row 5  col 6    : Space
Row 5  col 10-13: Right Alt, Fn, Menu, Right Ctrl
Row 5  col 14-16: Left Arrow, Down Arrow, Right Arrow
Row 5  col 18   : Num0
Row 5  col 20   : Num decimal
```

Gap positions that are always set to 0: `(0,1)`, `(0,17-21)`, `(1,17)`, `(2,17)`, `(3,12)`, `(3,14-17)`, `(3,21)`, `(4,1)`, `(4,12)`, `(4,14)`, `(4,16-17)`, `(5,3-5)`, `(5,7-9)`, `(5,17)`, `(5,19)`, `(5,21)`.

The grid is sent to the hardware using the CHROMA_CUSTOM effect type:

```python
requests.put(
    f"{session_url}/keyboard",
    json={"effect": "CHROMA_CUSTOM", "param": grid}
)
```

---

## The interactive terminal menu

When the script runs it clears the terminal and displays the full effect list with numbering. It then asks four questions in sequence:

### Question 1 — Mode
```
[1] Single effect (loop one effect forever)
[2] Playlist (your custom order)
[3] All effects in default order
```

Option 1 loops one effect indefinitely. Option 2 lets you type effect numbers in any order separated by spaces — for example `14 7 1 12 20` plays aurora, vortex, wave L-to-R, ripple, then spectrum cycle in that order before looping. Option 3 runs all 20 effects in the order they appear in the list.

### Question 2 — Speed
```
1 = Ultra slow (hypnotic)
2 = Slow (recommended starting point)
3 = Medium
4 = Fast
5 = Very fast
Or enter a custom decimal e.g. 0.15 or 0.8
```

Speed presets map to internal multipliers: 1=0.15, 2=0.3, 3=0.6, 4=1.2, 5=2.5. The multiplier is passed directly to every effect function. Because all 20 effects use the same `sp` parameter in the same structural position, changing the speed value uniformly scales every effect. Custom decimals allow precise control — 0.2 for a very slow meditative cycle, 1.0 for normal speed, 2.0 for fast.

### Question 3 — Duration
```
Seconds per effect before switching [default 35]:
```

In playlist or all-effects mode, the engine counts frames and switches to the next effect after this many seconds. At 7 fps, 35 seconds = 245 frames. The duration applies equally to every effect in the playlist.

### Question 4 — Direction
```
1 = Forward (default)
2 = Reverse
```

For effects marked [DIR] in the list, direction determines whether the animation flows in the natural direction (left-to-right, top-to-bottom, clockwise, outward) or the reversed direction. Effects without spatial direction (breathing, starlight, fire, lightning, rainfall when direction is not meaningful) ignore this setting.

After all four questions the script displays a summary:
```
PLAYLIST:
  1. Aurora Borealis
  2. Vortex / Spiral
  3. Wave L to R

Speed:     0.3x
Duration:  35s per effect
Direction: Forward

Connecting to Chroma SDK...
Connected! Session: http://localhost:58943/chromasdk

  Playing: Aurora Borealis  [1/3]
```

And then the lighting starts immediately.

---

## Installation

### Step 1 — Install Python

Download from https://www.python.org/downloads/ and run the installer.

During installation check the box labeled "Add Python to PATH" before clicking Install. Without this, the `python` command will not be recognized in Command Prompt.

Verify the installation:
```
python --version
```
Expected output: `Python 3.12.x` or similar.

Alternatively install via winget:
```
winget install --id Python.Python.3.12
```

### Step 2 — Install requests

```
pip install requests
```

This is the only external dependency. Everything else uses Python's standard library.

### Step 3 — Download the script

```
git clone https://github.com/PopcornKitsilano/razer-crimson-royale
cd razer-crimson-royale
```

Or download `razer_chroma_colors.py` directly from the repository.

---

## Running the script

Open Command Prompt as Administrator. Right-click the Command Prompt icon and select "Run as administrator". Without administrator privileges, the Chroma SDK accepts commands and returns success responses, but the hardware does not respond.

```
cd C:\Users\YourUsername\Downloads
python razer_chroma_colors.py
```

The interactive menu will appear immediately.

Press Ctrl+C at any time to stop. The script sends a DELETE request to close the Chroma session cleanly, which returns lighting control to Synapse.

---

## Updating the repository

To push changes to GitHub after modifying the script or README:

```
cd C:\Users\Daggerhead69\Downloads
git add razer_chroma_colors.py README.md
git commit -m "describe what changed"
git push
```

To replace only the README:

```
cd C:\Users\Daggerhead69\Downloads
git add README.md
git commit -m "Update README"
git push
```

To check what has changed before committing:

```
git status
git diff README.md
```

---

## Customization reference

### Changing WASD and arrow key colors

At the top of the script:
```python
RED     = hex_bgr("#FF0000")   # color for WASD, arrows, Caps Lock
HOTPINK = hex_bgr("#FF0066")   # color for Right Ctrl
```
Replace the hex values with any color. The change applies to every effect automatically because all 20 effect functions call `stamp(grid)` at the end, which applies these color assignments after the effect computation.

### Changing the color palette

Edit the `HUE_STOPS` list. Each entry is a tuple of `(position, hue)` where position is 0.0–1.0 and hue is 0–360 degrees on the color wheel. Position values must be in ascending order and the list must start at 0.0 and end at 1.0 with the same hue to ensure the spectrum loops smoothly.

To make the palette purely red-to-purple with no green or cyan:
```python
HUE_STOPS = [
    (0.00,   0),   # Red
    (0.25, 330),   # Rose
    (0.50, 300),   # Magenta
    (0.75, 270),   # Purple
    (1.00,   0),   # Red (loop)
]
```

### Adding a new effect

Write a function that matches this signature:
```python
def my_effect(t, sp, fwd):
    g = G()                          # creates empty 6x22 grid
    for r in range(ROWS):
        for c in range(COLS):
            g[r][c] = spectrum(...)  # compute color for this key
    return stamp(g)                  # apply special keys and gaps
```

Then add one line to `ALL_EFFECTS`:
```python
("My Effect Name", my_effect, "direction"),   # "direction" or "speed"
```

It will appear automatically in the terminal menu numbered in its position in the list.

### Adjusting effect duration default

Change the `duration` default in the `ask_playlist` function:
```python
raw = input("  Seconds per effect before switching [default 35]: ").strip()
if raw == "": duration = 35; break    # change 35 to your preferred default
```

---

## Files

```
razer-crimson-royale/
├── razer_chroma_colors.py    # complete engine, all 20 effects, interactive menu
└── README.md                 # this file
```

---

## License

MIT. Use it, modify it, distribute it, build on it.
