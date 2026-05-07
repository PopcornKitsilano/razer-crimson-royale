"""
╔══════════════════════════════════════════════════════════╗
║     RAZER CHROMA — ULTIMATE SPECTRUM ENGINE v4.0         ║
║     by PopcornKitsilano                                  ║
║                                                          ║
║  20 effects | User-defined order | Speed control         ║
║  Direction control | Single or playlist mode             ║
╚══════════════════════════════════════════════════════════╝
"""

import requests, time, math, random, sys, os

BASE_URL = "http://localhost:54235/razer/chromasdk"
APP_INFO = {
    "title": "Chroma Spectrum Engine",
    "description": "Ultimate RGB engine",
    "author": {"name": "PopcornKitsilano", "contact": "user@example.com"},
    "device_supported": ["keyboard","mouse","mousepad","headset","chromalink"],
    "category": "application"
}

ROWS, COLS = 6, 22

# ── COLOR ENGINE ──────────────────────────────────────────────────────────────

def bgr(r, g, b):
    r,g,b = max(0,min(255,int(r))), max(0,min(255,int(g))), max(0,min(255,int(b)))
    return (b<<16)|(g<<8)|r

def hex_bgr(h):
    h = h.lstrip('#')
    return bgr(int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

def hsv(h, s=1.0, v=1.0):
    h = h % 360
    c = v*s; x = c*(1-abs((h/60)%2-1)); m = v-c
    if   h<60:  r,g,b=c,x,0
    elif h<120: r,g,b=x,c,0
    elif h<180: r,g,b=0,c,x
    elif h<240: r,g,b=0,x,c
    elif h<300: r,g,b=x,0,c
    else:       r,g,b=c,0,x
    return bgr((r+m)*255,(g+m)*255,(b+m)*255)

def lerp(c1, c2, t):
    t=max(0.0,min(1.0,t))
    b1,g1,r1=(c1>>16)&0xFF,(c1>>8)&0xFF,c1&0xFF
    b2,g2,r2=(c2>>16)&0xFF,(c2>>8)&0xFF,c2&0xFF
    return bgr(r1+(r2-r1)*t,g1+(g2-g1)*t,b1+(b2-b1)*t)

def dim(c, v):
    b,g,r=(c>>16)&0xFF,(c>>8)&0xFF,c&0xFF
    return bgr(r*v,g*v,b*v)

HUE_STOPS = [
    (0.00,0),(0.07,15),(0.12,30),(0.16,60),(0.19,120),(0.22,180),
    (0.26,210),(0.32,240),(0.40,255),(0.50,270),(0.60,285),
    (0.70,300),(0.78,315),(0.86,330),(0.93,345),(1.00,0),
]

def spectrum(pos):
    pos = pos % 1.0
    for i in range(len(HUE_STOPS)-1):
        p0,h0=HUE_STOPS[i]; p1,h1=HUE_STOPS[i+1]
        if p0<=pos<=p1:
            t=(pos-p0)/(p1-p0) if p1>p0 else 0
            dh=h1-h0
            if abs(dh)>180: dh=dh-360 if dh>0 else dh+360
            return hsv(h0+dh*t)
    return hex_bgr("#FF0000")

# ── KEY LAYOUT ────────────────────────────────────────────────────────────────

WASD   = {(2,2),(3,1),(3,2),(3,3)}
ARROWS = {(4,15),(5,14),(5,15),(5,16)}
CAPS   = {(3,0)}
RCTRL  = {(5,13)}
GAPS   = {
    (0,1),(0,17),(0,18),(0,19),(0,20),(0,21),
    (1,17),(2,17),(3,12),(3,14),(3,15),(3,16),(3,17),(3,21),
    (4,1),(4,12),(4,14),(4,16),(4,17),
    (5,3),(5,4),(5,5),(5,7),(5,8),(5,9),(5,17),(5,19),(5,21),
}
RED=hex_bgr("#FF0000"); HOTPINK=hex_bgr("#FF0066"); BLACK=0

def stamp(grid):
    for(r,c)in GAPS:
        if 0<=r<ROWS and 0<=c<COLS: grid[r][c]=BLACK
    for(r,c)in WASD|ARROWS|CAPS:
        if 0<=r<ROWS and 0<=c<COLS: grid[r][c]=RED
    for(r,c)in RCTRL:
        if 0<=r<ROWS and 0<=c<COLS: grid[r][c]=HOTPINK
    return grid

def G(): return [[BLACK]*COLS for _ in range(ROWS)]

# ── EFFECTS (speed + direction aware) ────────────────────────────────────────

def wave_lr(t,sp,fwd):
    g=G(); s=sp*0.4; d=1 if fwd else -1
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=spectrum(c/16.0*d - t*s)
    return stamp(g)

def wave_rl(t,sp,fwd):
    g=G(); s=sp*0.4; d=1 if fwd else -1
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=spectrum((1.0-c/16.0)*d - t*s)
    return stamp(g)

def wave_tb(t,sp,fwd):
    g=G(); s=sp*0.4; d=1 if fwd else -1
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=spectrum(r/5.0*d - t*s)
    return stamp(g)

def wave_bt(t,sp,fwd):
    g=G(); s=sp*0.4; d=1 if fwd else -1
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=spectrum((1.0-r/5.0)*d - t*s)
    return stamp(g)

def diag_nwse(t,sp,fwd):
    g=G(); s=sp*0.35; d=1 if fwd else -1
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=spectrum((c/16.0+r/5.0)*0.5*d - t*s)
    return stamp(g)

def diag_nesw(t,sp,fwd):
    g=G(); s=sp*0.35; d=1 if fwd else -1
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=spectrum((1.0-c/16.0+r/5.0)*0.5*d - t*s)
    return stamp(g)

def vortex(t,sp,fwd):
    g=G(); s=sp*0.3; d=1 if fwd else -1
    cx,cy=COLS/2.0,ROWS/2.0
    for r in range(ROWS):
        for c in range(COLS):
            angle=math.atan2(r-cy,c-cx)/(2*math.pi)
            dist=math.sqrt((c-cx)**2+(r-cy)**2)*0.07
            g[r][c]=spectrum(angle*d+dist - t*s)
    return stamp(g)

def radial(t,sp,fwd):
    g=G(); s=sp*0.4; d=1 if fwd else -1
    cx,cy=COLS/2.0,ROWS/2.0
    for r in range(ROWS):
        for c in range(COLS):
            dist=math.sqrt((c-cx)**2+(r-cy)**2)*0.1
            g[r][c]=spectrum(dist*d - t*s)
    return stamp(g)

def breathing(t,sp,fwd):
    g=G(); s=sp*1.5
    bri=(math.sin(t*s)*0.5+0.5)**2
    pos=t*sp*0.15
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=dim(spectrum(pos+c/80.0),bri)
    return stamp(g)

def col_breathing(t,sp,fwd):
    g=G(); s=sp*1.2
    for r in range(ROWS):
        for c in range(COLS):
            phase=c/COLS*math.pi*2
            bri=(math.sin(t*s+phase)*0.5+0.5)**2
            g[r][c]=dim(spectrum(c/16.0+t*sp*0.05),bri)
    return stamp(g)

_stars=[(random.randint(0,ROWS-1),random.randint(0,COLS-1),
         random.uniform(0,math.pi*2),random.uniform(0.8,2.5),
         random.choice([0,270,300,240,330,15])) for _ in range(55)]

def starlight(t,sp,fwd):
    g=G(); s=sp*1.5
    for r2,c2,phase,speed,hue in _stars:
        bri=(math.sin(t*speed*s+phase)*0.5+0.5)**3
        g[r2][c2]=hsv(hue,1.0,bri)
    return stamp(g)

_ripples=[]; _next_rip=[0.0]

def ripple(t,sp,fwd):
    g=G()
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=hsv(270,1.0,0.1)
    if t>_next_rip[0]:
        _ripples.append([random.uniform(2,COLS-3),random.uniform(0,ROWS-1),
                         t,random.choice([0,300,270,240,330,15])])
        _next_rip[0]=t+random.uniform(1.5/sp,3.0/sp)
        _ripples[:]=[rp for rp in _ripples if t-rp[2]<3.0/sp]
    for rx,ry,st,hue in _ripples:
        age=(t-st)*sp
        if age<0 or age>3.0: continue
        radius=age*7.0; bri=max(0,1.0-age/3.0)
        for r in range(ROWS):
            for c in range(COLS):
                dist=math.sqrt((c-rx)**2+(r-ry)**2)
                diff=abs(dist-radius)
                if diff<1.8:
                    intensity=(1.0-diff/1.8)*bri
                    g[r][c]=lerp(g[r][c],hsv(hue,1.0,intensity),intensity)
    return stamp(g)

_comets=[[random.randint(0,ROWS-1),random.uniform(0,COLS),
          random.uniform(1.5,3.5),random.randint(6,12),
          random.choice([0,300,270,240,330])] for _ in range(5)]

def comet(t,sp,fwd):
    g=G()
    DT_=1.0/7
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=hsv(260,1.0,0.07)
    for cm in _comets:
        row,hx,spd,tlen,hue=cm
        cm[1]+=(spd*sp*DT_*(1 if fwd else -1))
        if cm[1]>COLS+tlen: cm[1]=-tlen; cm[0]=random.randint(0,ROWS-1); cm[4]=random.choice([0,300,270,240,330])
        if cm[1]<-tlen:     cm[1]=COLS+tlen; cm[0]=random.randint(0,ROWS-1)
        head=int(cm[1])
        step=1 if fwd else -1
        for i in range(tlen):
            c2=head-i*step
            if 0<=c2<COLS:
                bri=((tlen-i)/tlen)**1.5
                g[row][c2]=bgr(255,255,255) if i==0 else hsv(hue,1.0,bri)
    return stamp(g)

def aurora(t,sp,fwd):
    g=G(); s=sp*0.5; d=1 if fwd else -1
    for r in range(ROWS):
        for c in range(COLS):
            w1=math.sin(c*0.35+t*s*1.1*d)*0.5+0.5
            w2=math.sin(c*0.65-t*s*0.7*d+r*0.4)*0.5+0.5
            w3=math.sin(c*0.18+t*s*0.4*d+r*0.6)*0.5+0.5
            mix=(w1+w2+w3)/3.0
            g[r][c]=hsv(140+mix*160,1.0,0.35+mix*0.65)
    return stamp(g)

def fire(t,sp,fwd):
    g=G(); s=sp*3.0
    for r in range(ROWS):
        for c in range(COLS):
            intensity=(ROWS-r)/ROWS
            noise=(math.sin(c*1.9+t*s*1.2)*0.12+
                   math.sin(c*0.7-t*s*1.8)*0.08+
                   math.sin(c*3.1+t*s*0.9)*0.05)
            val=max(0.0,min(1.0,intensity+noise))
            if   val<0.3: col=bgr(val/0.3*180,0,0)
            elif val<0.6: t2=(val-0.3)/0.3; col=bgr(180+t2*75,t2*70,0)
            else:          t2=(val-0.6)/0.4; col=bgr(255,70+t2*185,t2*40)
            g[r][c]=col
    return stamp(g)

_drops=[[random.randint(0,COLS-1),random.uniform(0,ROWS),
         random.uniform(0.6,1.8),random.randint(3,6)] for _ in range(16)]

def matrix(t,sp,fwd):
    g=G(); DT_=1.0/7
    for drop in _drops:
        dc,hr,spd,tlen=drop
        drop[1]+=spd*sp*DT_*6*(1 if fwd else -1)
        if drop[1]>ROWS+tlen: drop[0]=random.randint(0,COLS-1); drop[1]=0; drop[2]=random.uniform(0.6,1.8)
        if drop[1]<-tlen:     drop[0]=random.randint(0,COLS-1); drop[1]=ROWS+tlen
        head=int(drop[1])%ROWS
        for i in range(tlen):
            r2=head-i
            if 0<=r2<ROWS:
                bri=(tlen-i)/tlen
                g[r2][dc]=bgr(200,255,200) if i==0 else hsv(120,1.0,bri*0.85)
    return stamp(g)

_bolts=[]; _next_bolt=[0.0]

def lightning(t,sp,fwd):
    g=G()
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=hsv(245,1.0,0.08)
    if t>_next_bolt[0]:
        _bolts.append([random.randint(1,COLS-2),t,random.choice([55,200,270,0,300])])
        _next_bolt[0]=t+random.uniform(2.0,5.0)
        _bolts[:]=[b for b in _bolts if t-b[1]<0.6]
    for bc,bt,hue in _bolts:
        age=t-bt
        if age<0 or age>0.6: continue
        bri=1.0-age/0.6
        for r in range(ROWS):
            jitter=int(math.sin(r*4.3+bc)*1.2)
            c2=bc+jitter
            if 0<=c2<COLS:
                g[r][c2]=hsv(hue,0.2,bri)
                if c2+1<COLS: g[r][c2+1]=hsv(hue,0.5,bri*0.4)
    return stamp(g)

def color_shift(t,sp,fwd):
    g=G(); s=sp*0.2; d=1 if fwd else -1
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=spectrum(t*s*d+r*0.03)
    return stamp(g)

_rain=[[random.randint(0,COLS-1),random.uniform(0,ROWS*2),
        random.uniform(0.8,2.0),random.choice([240,270,300,0,330])] for _ in range(20)]

def rainfall(t,sp,fwd):
    g=G(); DT_=1.0/7
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=hsv(260,0.8,0.08)
    for drop in _rain:
        dc,dr,spd,hue=drop
        drop[1]+=spd*sp*DT_*5*(1 if fwd else -1)
        if drop[1]>ROWS+2: drop[0]=random.randint(0,COLS-1); drop[1]=random.uniform(-2,0); drop[2]=random.uniform(0.8,2.0)
        if drop[1]<-2:     drop[0]=random.randint(0,COLS-1); drop[1]=ROWS+2
        r2=int(drop[1])
        for i in range(3):
            rr=r2-i
            if 0<=rr<ROWS: g[rr][dc]=hsv(hue,1.0,(3-i)/3.0)
        if r2>=ROWS-1:
            for dc2 in [dc-1,dc+1]:
                if 0<=dc2<COLS: g[ROWS-1][dc2]=hsv(hue,0.6,0.5)
    return stamp(g)

def spectrum_cycle(t,sp,fwd):
    g=G(); s=sp*0.15; d=1 if fwd else -1
    for r in range(ROWS):
        for c in range(COLS): g[r][c]=spectrum(t*s*d+r*0.03)
    return stamp(g)

# ── EFFECT REGISTRY ───────────────────────────────────────────────────────────

ALL_EFFECTS = [
    ("Wave L→R",          wave_lr,       "direction"),
    ("Wave R→L",          wave_rl,       "direction"),
    ("Wave T→B",          wave_tb,       "direction"),
    ("Wave B→T",          wave_bt,       "direction"),
    ("Diagonal NW→SE",    diag_nwse,     "direction"),
    ("Diagonal NE→SW",    diag_nesw,     "direction"),
    ("Vortex / Spiral",   vortex,        "direction"),
    ("Radial Burst",      radial,        "direction"),
    ("Breathing",         breathing,     "speed"),
    ("Column Breathing",  col_breathing, "speed"),
    ("Starlight",         starlight,     "speed"),
    ("Ripple",            ripple,        "speed"),
    ("Comet Streaks",     comet,         "direction"),
    ("Aurora Borealis",   aurora,        "direction"),
    ("Fire",              fire,          "speed"),
    ("Matrix Rain",       matrix,        "direction"),
    ("Lightning",         lightning,     "speed"),
    ("Color Shift",       color_shift,   "direction"),
    ("Rainfall",          rainfall,      "direction"),
    ("Spectrum Cycle",    spectrum_cycle,"direction"),
]

# ── MENU ──────────────────────────────────────────────────────────────────────

def clear(): os.system('cls' if os.name=='nt' else 'clear')

def print_header():
    print("╔══════════════════════════════════════════════════════╗")
    print("║       RAZER CHROMA — ULTIMATE SPECTRUM ENGINE        ║")
    print("║                  by PopcornKitsilano                 ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

def print_effects():
    print("  AVAILABLE EFFECTS:")
    print("  ─────────────────────────────────────────────────────")
    for i,(name,_,ctrl) in enumerate(ALL_EFFECTS):
        tag = "[DIR]" if ctrl=="direction" else "[SPD]"
        print(f"  {i+1:>2}. {name:<22} {tag}")
    print()
    print("  [DIR] = supports direction toggle (forward/reverse)")
    print("  [SPD] = speed-only effect")
    print()

def ask_playlist():
    """Ask user to define their playlist and settings"""
    clear()
    print_header()
    print_effects()

    print("═" * 56)
    print("  SETUP")
    print("═" * 56)
    print()

    # Mode
    print("  [1] Single effect (loop one effect)")
    print("  [2] Playlist (your custom order)")
    print("  [3] All effects in default order")
    print()
    while True:
        mode = input("  Choose mode (1/2/3): ").strip()
        if mode in ("1","2","3"): break
        print("  Please enter 1, 2 or 3.")

    # Build effect list
    if mode == "1":
        print()
        while True:
            try:
                n = int(input(f"  Choose effect number (1-{len(ALL_EFFECTS)}): ").strip())
                if 1 <= n <= len(ALL_EFFECTS): break
            except: pass
            print(f"  Enter a number between 1 and {len(ALL_EFFECTS)}.")
        playlist = [n-1]

    elif mode == "2":
        print()
        print("  Enter effect numbers in the order you want them.")
        print("  Separate with spaces or commas. Example: 1 5 3 7 2")
        print()
        while True:
            raw = input("  Your order: ").strip().replace(","," ")
            try:
                nums = [int(x)-1 for x in raw.split()]
                if nums and all(0<=n<len(ALL_EFFECTS) for n in nums):
                    playlist = nums
                    break
            except: pass
            print(f"  Invalid. Use numbers 1-{len(ALL_EFFECTS)} separated by spaces.")

    else:
        playlist = list(range(len(ALL_EFFECTS)))

    # Speed
    print()
    print("  SPEED")
    print("  ─────────────────────────────────────")
    print("  1 = Ultra slow (hypnotic)")
    print("  2 = Slow       (current default)")
    print("  3 = Medium")
    print("  4 = Fast")
    print("  5 = Very fast")
    print("  Or enter a custom decimal e.g. 0.15 or 0.8")
    print()
    speed_map = {"1":0.15,"2":0.3,"3":0.6,"4":1.2,"5":2.5}
    while True:
        raw = input("  Speed (1-5 or custom): ").strip()
        if raw in speed_map:
            speed = speed_map[raw]; break
        try:
            speed = float(raw)
            if speed > 0: break
        except: pass
        print("  Invalid. Enter 1-5 or a positive decimal.")

    # Duration per effect
    print()
    while True:
        raw = input("  Seconds per effect before switching [default 35]: ").strip()
        if raw == "": duration = 35; break
        try:
            duration = int(raw)
            if duration > 0: break
        except: pass
        print("  Enter a positive number.")

    # Direction (for directional effects)
    print()
    print("  DIRECTION (for wave/diagonal/vortex/comet/matrix etc.)")
    print("  1 = Forward  (default)")
    print("  2 = Reverse")
    print()
    while True:
        raw = input("  Direction (1/2): ").strip()
        if raw in ("1","2"): forward = (raw=="1"); break
        print("  Enter 1 or 2.")

    return playlist, speed, duration, forward

# ── MOUSE ─────────────────────────────────────────────────────────────────────

def mouse_frame(t, sp, fwd):
    g=[]
    s=sp*0.3; d=1 if fwd else -1
    for r in range(9):
        row=[]
        for c in range(7):
            row.append(spectrum((c/6.0+r/8.0)*0.5*d - t*s))
        g.append(row)
    return g

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    playlist, speed, duration, forward = ask_playlist()

    clear()
    print_header()
    print("  PLAYLIST:")
    for i,idx in enumerate(playlist):
        print(f"    {i+1}. {ALL_EFFECTS[idx][0]}")
    print()
    print(f"  Speed:     {speed}x")
    print(f"  Duration:  {duration}s per effect")
    print(f"  Direction: {'Forward' if forward else 'Reverse'}")
    print()

    # Register with Chroma SDK
    print("  Connecting to Chroma SDK...")
    try:
        r = requests.post(BASE_URL, json=APP_INFO, timeout=5)
        s = r.json()
        url = s.get("uri") or s.get("url")
        if not url:
            print("  ERROR: No session URL. Is Razer Synapse running?")
            input("  Press Enter to exit.")
            return
        print(f"  Connected! Session: {url}")
    except Exception as e:
        print(f"  ERROR: {e}")
        input("  Press Enter to exit.")
        return

    FPS = 7
    DT  = 1.0/FPS
    FRAMES_PER_EFFECT = int(duration * FPS)

    t=0.0; frame=0; eff_frame=0; pl_idx=0
    single = len(playlist)==1

    print()
    cur_name = ALL_EFFECTS[playlist[pl_idx]][0]
    print(f"  ▶  Now playing: {cur_name}")
    if not single:
        print(f"  Effect {pl_idx+1}/{len(playlist)}")
    print("  Ctrl+C to stop\n")

    try:
        while True:
            loop_start = time.time()

            eff_idx = playlist[pl_idx]
            name, fn, _ = ALL_EFFECTS[eff_idx]
            grid = fn(t, speed, forward)

            # Keyboard
            try:
                requests.put(f"{url}/keyboard",
                    json={"effect":"CHROMA_CUSTOM","param":grid}, timeout=3)
            except: pass

            # Mouse every 3 frames
            if frame % 3 == 0:
                try:
                    mg = mouse_frame(t, speed, forward)
                    r2 = requests.put(f"{url}/mouse",
                        json={"effect":"CHROMA_CUSTOM2","param":mg}, timeout=3)
                    if r2.json().get("result") != 0: raise Exception()
                except:
                    try:
                        requests.put(f"{url}/mouse",
                            json={"effect":"CHROMA_STATIC",
                                  "param":{"color":spectrum(t*speed*0.3)}}, timeout=3)
                    except: pass

            # Heartbeat every 25 frames
            if frame % 25 == 0:
                try: requests.put(f"{url}/heartbeat", timeout=3)
                except: pass

            t += DT; frame += 1; eff_frame += 1

            if not single and eff_frame >= FRAMES_PER_EFFECT:
                eff_frame = 0
                pl_idx = (pl_idx+1) % len(playlist)
                new_name = ALL_EFFECTS[playlist[pl_idx]][0]
                print(f"  ▶  {new_name}  [{pl_idx+1}/{len(playlist)}]")

            elapsed = time.time()-loop_start
            time.sleep(max(0, DT-elapsed))

    except KeyboardInterrupt:
        print("\n\n  Stopped.")

    try:
        requests.delete(url, timeout=3)
        print("  Session closed.")
    except: pass

    print()
    input("  Press Enter to exit.")

if __name__ == "__main__":
    main()
