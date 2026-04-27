"""
Razer Chroma - CRIMSON ROYALE ANIMATED
- Fast visible wave animation
- Pattern shifts every 30 seconds
- Mouse lighting fixed
"""
import requests, time, math

BASE_URL = "http://localhost:54235/razer/chromasdk"

APP_INFO = {
    "title": "Crimson Royale",
    "description": "Custom purple/red keyboard lighting",
    "author": {"name": "User", "contact": "user@example.com"},
    "device_supported": ["keyboard","mouse","mousepad","headset","chromalink"],
    "category": "application"
}

def bgr(h):
    h = h.lstrip('#')
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return (b<<16)|(g<<8)|r

def bgr_rgb(r,g,b):
    r,g,b = max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b))
    return (b<<16)|(g<<8)|r

RED     = bgr("#FF0000")
HOTPINK = bgr("#FF0066")
BK      = 0

# Color palette - red/pink/purple/violet family
STOPS = [
    (0.00, 255,   0,   0),   # Red
    (0.14, 255,   0,  80),   # Red-Pink
    (0.28, 255,   0, 160),   # Hot Pink
    (0.42, 255,   0, 255),   # Magenta
    (0.57, 180,   0, 255),   # Purple-Pink
    (0.71, 100,   0, 255),   # Purple
    (0.85, 50,    0, 255),   # Blue Violet
    (1.00, 255,   0,   0),   # Red (loop)
]

def get_color(pos):
    pos = pos % 1.0
    for i in range(len(STOPS)-1):
        p0,r0,g0,b0 = STOPS[i]
        p1,r1,g1,b1 = STOPS[i+1]
        if p0 <= pos <= p1:
            t = (pos-p0)/(p1-p0)
            return bgr_rgb(int(r0+(r1-r0)*t), int(g0+(g1-g0)*t), int(b0+(b1-b0)*t))
    return RED

WASD   = {(2,2),(3,1),(3,2),(3,3)}
ARROWS = {(4,15),(5,14),(5,15),(5,16)}
CAPS   = {(3,0)}
RCTRL  = {(5,13)}
GAPS   = {(0,1),(3,12),(3,14),(3,15),(3,16),(3,17),(3,21),
          (4,1),(4,12),(4,14),(4,16),(4,17),
          (5,3),(5,4),(5,5),(5,7),(5,8),(5,9),(5,17),(5,19),(5,21),(1,17),(2,17)}

PATTERNS = ["wave_lr", "wave_rl", "wave_tb", "pulse", "diagonal"]

def build_grid(offset, pattern):
    grid = [[BK]*22 for _ in range(6)]

    for row in range(6):
        for col in range(22):
            if pattern == "wave_lr":
                # Left to right wave
                pos = col/16.0 - offset
            elif pattern == "wave_rl":
                # Right to left wave
                pos = 1.0 - col/16.0 - offset
            elif pattern == "wave_tb":
                # Top to bottom wave
                pos = row/5.0 - offset
            elif pattern == "pulse":
                # Whole keyboard pulses through colors together
                pos = offset
            elif pattern == "diagonal":
                # Diagonal wave
                pos = (col/16.0 + row/5.0)/2.0 - offset
            else:
                pos = col/16.0 - offset

            grid[row][col] = get_color(pos)

    # Clear gaps
    for (r,c) in GAPS:
        if 0<=r<6 and 0<=c<22:
            grid[r][c] = BK

    # Lock special keys
    for (r,c) in WASD|ARROWS|CAPS:
        grid[r][c] = RED
    for (r,c) in RCTRL:
        grid[r][c] = HOTPINK

    return grid

def build_mouse_grid(offset):
    """Basilisk mouse - 9 rows x 7 cols"""
    grid = []
    for row in range(9):
        r = []
        for col in range(7):
            pos = (col/6.0 + row/8.0)/2.0 - offset
            r.append(get_color(pos))
        grid.append(r)
    return grid

def main():
    print("Razer - CRIMSON ROYALE ANIMATED WAVE")
    print("="*40)
    print("Fast wave + pattern shifts every 30s")
    print()

    # Register
    try:
        r = requests.post(BASE_URL, json=APP_INFO, timeout=5)
        session = r.json()
        print(f"Session: {session}")
        session_url = session.get("uri") or session.get("url")
        if not session_url:
            print("No session URL. Exiting.")
            return
        print(f"URL: {session_url}")
    except Exception as e:
        print(f"Registration failed: {e}")
        return

    offset = 0.0
    frame  = 0
    pattern_index = 0
    pattern_frame = 0
    FRAMES_PER_PATTERN = 150  # ~30 seconds at 0.2s per frame

    print(f"\nStarting with pattern: {PATTERNS[pattern_index]}")
    print("Ctrl+C to stop.\n")

    try:
        while True:
            pattern = PATTERNS[pattern_index]

            # Build and send keyboard
            grid = build_grid(offset, pattern)
            try:
                requests.put(
                    f"{session_url}/keyboard",
                    json={"effect":"CHROMA_CUSTOM","param":grid},
                    timeout=3
                )
            except: pass

            # Build and send mouse - try CHROMA_CUSTOM2 first
            mouse_grid = build_mouse_grid(offset)
            try:
                r = requests.put(
                    f"{session_url}/mouse",
                    json={"effect":"CHROMA_CUSTOM2","param":mouse_grid},
                    timeout=3
                )
                if r.json().get("result") != 0:
                    raise Exception("custom2 failed")
            except:
                # Fallback - static color that matches current wave position
                try:
                    requests.put(
                        f"{session_url}/mouse",
                        json={"effect":"CHROMA_STATIC","param":{"color":get_color(offset)}},
                        timeout=3
                    )
                except: pass

            # Heartbeat every 10 frames
            if frame % 10 == 0:
                try:
                    requests.put(f"{session_url}/heartbeat", timeout=3)
                except: pass

            # Advance animation
            offset = (offset + 0.05) % 1.0
            frame += 1
            pattern_frame += 1

            # Switch pattern every FRAMES_PER_PATTERN frames
            if pattern_frame >= FRAMES_PER_PATTERN:
                pattern_frame = 0
                pattern_index = (pattern_index + 1) % len(PATTERNS)
                print(f"Pattern changed: {PATTERNS[pattern_index]}")

            time.sleep(0.15)  # ~6 fps - fast enough to see movement

    except KeyboardInterrupt:
        print("\nStopping...")

    try:
        requests.delete(session_url, timeout=3)
        print("Session closed.")
    except: pass

if __name__ == "__main__":
    main()
