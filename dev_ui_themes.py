import tkinter as tk
import math
import random
from datetime import datetime


def hex_to_rgb(hex_color):
    hex_color = (hex_color or "#00E5FF").lstrip("#")
    if len(hex_color) != 6:
        return (0, 229, 255)
    try:
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (0, 229, 255)


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(
        max(0, min(255, int(rgb[0]))),
        max(0, min(255, int(rgb[1]))),
        max(0, min(255, int(rgb[2]))),
    )


def blend(c1, c2, t):
    t = max(0.0, min(1.0, float(t)))
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex((r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t))


class DeveloperUIEngine:
    """
    Renders and handles click interactions for the 4 custom Developer UI/UX designs:
      - 'chrono_compass'  : Cyan & Gold intricate astrolabe / compass HUD
      - 'sensor_array'    : 6-dial telemetry array + circuit traces + central radar
      - 'stark_schematic' : Exploded 3D gold/cyan Arc Reactor + spec sheet + interactive buttons
      - 'tactical_suite'  : Full multi-card JARVIS dashboard (Biometrics, Resources, Armor, Core)
    """

    def __init__(self):
        self.hitboxes = []  # List of (x1, y1, x2, y2, action_id, payload)
        self.phase = 0.0
        self.sweep_angle = 0.0

        # Interactive states across themes
        self.compass_locked = False
        self.compass_boost = 0.0
        self.sys_dials = [True, True, False, True, True, False]
        self.selected_dial = 0
        self.schematic_explode = 0.72
        self.schematic_target = 0.72
        self.schematic_spin = 0.0
        self.schematic_auto_rotate = True
        self.armor_buttons = [True, True, False, True]
        self.bio_bars = [random.randint(25, 85) for _ in range(18)]
        self.last_telemetry = {"cpu": 18, "ram": 42, "storage": 64, "hr": 72}

    def step(self, dt=0.03, is_speaking=False, rhythm=0.0):
        speed = 2.2 if is_speaking else 1.0
        self.phase += dt * speed
        if not self.compass_locked:
            self.sweep_angle += dt * (1.4 if is_speaking else 0.65)
        self.compass_boost = max(0.0, self.compass_boost - dt * 1.5)

        if self.schematic_auto_rotate:
            self.schematic_spin += dt * (1.2 if is_speaking else 0.55)
        self.schematic_explode += (self.schematic_target - self.schematic_explode) * min(1.0, dt * 6.0)

        if random.random() < 0.18:
            idx = random.randint(0, len(self.bio_bars) - 1)
            self.bio_bars[idx] = max(18, min(95, self.bio_bars[idx] + random.randint(-14, 14)))

    def handle_click(self, x, y, callbacks):
        """Returns True if an interactive HUD control handled the click."""
        for x1, y1, x2, y2, action, payload in reversed(self.hitboxes):
            if x1 <= x <= x2 and y1 <= y <= y2:
                self._execute_action(action, payload, callbacks)
                return True
        return False

    def _execute_action(self, action, payload, cb):
        if action == "compass_pulse":
            self.compass_boost = 1.0
            self.compass_locked = not self.compass_locked
            if cb.get("fx"):
                cb["fx"]("mode_switch")
        elif action == "toggle_dial":
            idx = int(payload)
            self.sys_dials[idx] = not self.sys_dials[idx]
            self.selected_dial = idx
            if cb.get("fx"):
                cb["fx"]("macro_run")
        elif action == "schematic_cmd":
            cmd = payload
            if cmd == "ASSEMBLE":
                self.schematic_target = 0.04
            elif cmd == "EXPLODE":
                self.schematic_target = 0.95
            elif cmd == "ROTATE":
                self.schematic_auto_rotate = not self.schematic_auto_rotate
            elif cmd == "PULSE":
                self.compass_boost = 1.0
                self.schematic_target = 0.45 if self.schematic_target > 0.7 else 0.85
            elif cmd == "SPEAK" and cb.get("speak_demo"):
                cb["speak_demo"]()
            elif cmd == "RESET":
                self.schematic_target = 0.65
                self.schematic_spin = 0.0
                self.schematic_auto_rotate = True
            if cb.get("fx"):
                cb["fx"]("arc_assemble")
        elif action == "armor_btn":
            idx = int(payload)
            self.armor_buttons[idx] = not self.armor_buttons[idx]
            if idx == 1 and cb.get("telemetry"):
                cb["telemetry"]()
            elif cb.get("fx"):
                cb["fx"]("mode_switch")
        elif action == "mic_trigger":
            if cb.get("listen"):
                cb["listen"]()

    def _register_box(self, x1, y1, x2, y2, action, payload=None):
        self.hitboxes.append((x1, y1, x2, y2, action, payload))

    # =========================================================================
    # THEME 1: CHRONO COMPASS (Image 1 - Cyan & Gold Astrolabe Core)
    # =========================================================================
    def draw_chrono_compass(self, canvas, w, h, accent, is_speaking, rhythm):
        self.hitboxes.clear()
        cx, cy = w / 2, h / 2
        pulse = rhythm if is_speaking else (0.12 * (0.5 + 0.5 * math.sin(self.phase * 1.4)))
        boost = max(pulse, self.compass_boost)
        max_r = min(w, h) * 0.41 * (1.0 + 0.06 * boost)

        cyan = blend("#00E5FF", "#E0FFFF", 0.35 + 0.5 * boost)
        cyan_dim = blend("#041019", "#00E5FF", 0.35)
        gold = blend("#D99B38", "#FCD34D", 0.3 + 0.4 * boost)
        gold_dim = blend("#0A0906", "#B47B2B", 0.42)

        # Outer radial golden spokes & pins
        spoke_count = 48
        for i in range(spoke_count):
            ang = (2 * math.pi * i) / spoke_count + self.sweep_angle * 0.15
            r_in = max_r * 0.86
            r_out = max_r * (1.03 if i % 4 == 0 else 0.95)
            x0, y0 = cx + math.cos(ang) * r_in, cy + math.sin(ang) * r_in
            x1, y1 = cx + math.cos(ang) * r_out, cy + math.sin(ang) * r_out
            canvas.create_line(x0, y0, x1, y1, fill=gold_dim if i % 2 else gold, width=1)
            if i % 3 == 0:
                canvas.create_oval(x1 - 2.2, y1 - 2.2, x1 + 2.2, y1 + 2.2, fill=gold, outline="")

        # Concentric gold & cyan rings
        for mult, col, w_line in [
            (0.90, gold_dim, 1),
            (0.84, gold, 2),
            (0.77, cyan_dim, 2),
            (0.67, cyan, 2),
            (0.54, gold_dim, 1),
            (0.43, cyan, 2),
            (0.28, gold, 1),
            (0.16, cyan, 2),
        ]:
            rr = max_r * mult
            canvas.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=col, width=w_line)

        # Glowing segmented cyan arcs
        for seg in range(6):
            start_deg = math.degrees(self.sweep_angle) + seg * 60
            r_arc = max_r * 0.72
            canvas.create_arc(
                cx - r_arc, cy - r_arc, cx + r_arc, cy + r_arc,
                start=start_deg, extent=26, style=tk.ARC,
                outline=cyan, width=4 + int(3 * boost)
            )

        # Bottom golden calibration scale ticks
        for t in range(-18, 19):
            ang = math.pi / 2 + t * 0.032
            r0 = max_r * 0.34
            r1 = max_r * (0.40 if t % 3 == 0 else 0.37)
            canvas.create_line(
                cx + math.cos(ang) * r0, cy + math.sin(ang) * r0,
                cx + math.cos(ang) * r1, cy + math.sin(ang) * r1,
                fill=gold, width=2 if t % 3 == 0 else 1
            )

        # Cardinal N/S/E/W cyan/gold directional pointers
        for idx, base_ang in enumerate([0, math.pi / 2, math.pi, 3 * math.pi / 2]):
            ang = base_ang + (0.0 if self.compass_locked else math.sin(self.phase * 0.5) * 0.05)
            tip_r = max_r * 0.80
            base_r = max_r * 0.68
            tx, ty = cx + math.cos(ang) * tip_r, cy + math.sin(ang) * tip_r
            lx, ly = cx + math.cos(ang - 0.08) * base_r, cy + math.sin(ang - 0.08) * base_r
            rx, ry = cx + math.cos(ang + 0.08) * base_r, cy + math.sin(ang + 0.08) * base_r
            canvas.create_polygon(tx, ty, lx, ly, rx, ry, fill="#04151F", outline=cyan, width=2)

        # Glowing power blocks on lower-left quadrant
        for b in range(5):
            ang = math.pi * 0.76 + b * 0.065
            bx = cx + math.cos(ang) * (max_r * 0.60)
            by = cy + math.sin(ang) * (max_r * 0.60)
            canvas.create_oval(bx - 5, by - 5, bx + 5, by + 5, fill=cyan, outline="#FFFFFF", width=1)

        # Crosshairs & center bright core
        canvas.create_line(cx - max_r * 0.92, cy, cx + max_r * 0.92, cy, fill=cyan_dim, width=1)
        canvas.create_line(cx, cy - max_r * 0.92, cx, cy + max_r * 0.92, fill=cyan_dim, width=1)
        core_r = max_r * (0.07 + 0.03 * boost)
        canvas.create_oval(cx - core_r * 1.8, cy - core_r * 1.8, cx + core_r * 1.8, cy + core_r * 1.8, outline=cyan, width=2)
        canvas.create_oval(cx - core_r, cy - core_r, cx + core_r, cy + core_r, fill=cyan, outline="#FFFFFF", width=2)

        status_txt = "LOCKED // CLICK TO UNLOCK" if self.compass_locked else "CHRONO COMPASS // CLICK CORE TO PULSE & LOCK"
        canvas.create_text(cx, h - 22, text=status_txt, fill=gold, font=("Consolas", 8, "bold"))
        self._register_box(cx - max_r * 0.5, cy - max_r * 0.5, cx + max_r * 0.5, cy + max_r * 0.5, "compass_pulse")

    # =========================================================================
    # THEME 2: SENSOR ARRAY (Image 2 - 6 Dials + Circuit Traces + Main Radar)
    # =========================================================================
    def draw_sensor_array(self, canvas, w, h, accent, is_speaking, rhythm):
        self.hitboxes.clear()
        pulse = rhythm if is_speaking else 0.1
        cyan = blend("#00E5FF", "#CFFAFE", 0.35 + 0.45 * pulse)
        cyan_mid = blend("#05131E", "#00E5FF", 0.48)
        cyan_dim = blend("#050D14", "#00E5FF", 0.22)

        # Corner brackets
        pad, br = 18, 16
        for x0, y0, dx, dy in [(pad, pad, br, br), (w - pad, pad, -br, br), (pad, h - pad, br, -br), (w - pad, h - pad, -br, -br)]:
            canvas.create_line(x0, y0, x0 + dx, y0, fill=cyan, width=2)
            canvas.create_line(x0, y0, x0, y0 + dy, fill=cyan, width=2)

        # Top targeting reticle box
        tx, ty = w / 2, 74
        canvas.create_rectangle(tx - 84, ty - 28, tx + 84, ty + 28, outline=cyan_mid, width=1)
        canvas.create_text(tx - 48, ty - 36, text="AZIMUTH 24.7", fill=cyan_mid, font=("Consolas", 7))
        canvas.create_text(tx + 48, ty - 36, text="ELEVATION 12.1", fill=cyan_mid, font=("Consolas", 7))
        for idx, ox in enumerate([-46, 0, 46]):
            rr = 14 if idx == 1 else 10
            canvas.create_oval(tx + ox - rr, ty - rr, tx + ox + rr, ty + rr, outline=cyan, width=1)
            canvas.create_line(tx + ox - rr - 4, ty, tx + ox + rr + 4, ty, fill=cyan_mid, width=1)
            canvas.create_line(tx + ox, ty - rr - 4, tx + ox, ty + rr + 4, fill=cyan_mid, width=1)

        # 6 Top Interactive Subsystem Dials (SYS 01 - SYS 06)
        dial_xs = [w * 0.14, w * 0.25, w * 0.36, w * 0.64, w * 0.75, w * 0.86]
        dial_y = 152
        dial_r = min(32, w * 0.036)
        for i, dx in enumerate(dial_xs):
            active = self.sys_dials[i]
            col = cyan if active else cyan_dim
            canvas.create_oval(dx - dial_r, dial_y - dial_r, dx + dial_r, dial_y + dial_r, outline=col, width=2)
            canvas.create_oval(dx - dial_r * 0.62, dial_y - dial_r * 0.62, dx + dial_r * 0.62, dial_y + dial_r * 0.62, outline=cyan_mid, width=1)
            # Segmented arcs inside dial
            for seg in range(4):
                st = math.degrees(self.sweep_angle * (1.2 if active else 0.2)) + seg * 90 + i * 20
                canvas.create_arc(
                    dx - dial_r * 0.8, dial_y - dial_r * 0.8, dx + dial_r * 0.8, dial_y + dial_r * 0.8,
                    start=st, extent=45, style=tk.ARC, outline=col, width=3
                )
            if active:
                canvas.create_oval(dx - 4, dial_y - 4, dx + 4, dial_y + 4, fill=cyan, outline="")
            canvas.create_text(dx, dial_y + dial_r + 14, text=f"SYS 0{i + 1}", fill=col, font=("Consolas", 7, "bold"))
            self._register_box(dx - dial_r, dial_y - dial_r, dx + dial_r, dial_y + dial_r + 18, "toggle_dial", i)

        # Left Signal Quality & Right System Core telemetry blocks
        mid_y = h * 0.56
        canvas.create_text(32, mid_y - 95, text="▍SIGNAL QUALITY", anchor="w", fill="#E2E8F0", font=("Consolas", 8, "bold"))
        for b in range(7):
            bw = 10 + ((b * 7 + int(self.phase * 6)) % 22)
            canvas.create_rectangle(34, mid_y - 78 + b * 7, 34 + bw, mid_y - 74 + b * 7, fill=cyan, outline="")
        canvas.create_text(32, mid_y - 12, text="STATUS: OPTIMAL\nNODE: 0x4A9\nFLOW RATE: 84.2", anchor="nw", fill=cyan_mid, font=("Consolas", 7))

        canvas.create_text(w - 32, mid_y - 95, text="SYSTEM CORE▐", anchor="e", fill="#E2E8F0", font=("Consolas", 8, "bold"))
        for b in range(7):
            bw = 10 + ((b * 5 + int(self.phase * 8)) % 22)
            canvas.create_rectangle(w - 34 - bw, mid_y - 78 + b * 7, w - 34, mid_y - 74 + b * 7, fill=cyan, outline="")
        canvas.create_text(w - 32, mid_y - 12, text="READY STATE\nUPLINK: SECURE\nLATENCY: 12ms", anchor="ne", fill=cyan_mid, font=("Consolas", 7))

        # Symmetrical Circuit Traces leading into Main Sensor Array
        cx, cy = w / 2, h * 0.62
        main_r = min(w, h) * 0.21 * (1.0 + 0.08 * pulse)

        for sign in (-1, 1):
            pts1 = [
                cx + sign * main_r * 0.9, cy - 10,
                cx + sign * main_r * 1.45, cy - 65,
                cx + sign * w * 0.34, cy - 65,
            ]
            pts2 = [
                cx + sign * main_r * 0.95, cy + 12,
                cx + sign * main_r * 1.45, cy + 58,
                cx + sign * w * 0.36, cy + 58,
            ]
            canvas.create_line(*pts1, fill=cyan, width=2)
            canvas.create_line(*pts2, fill=cyan_mid, width=2)
            canvas.create_oval(pts1[-2] - 4, pts1[-1] - 4, pts1[-2] + 4, pts1[-1] + 4, fill=cyan, outline="")
            canvas.create_oval(pts2[-2] - 4, pts2[-1] - 4, pts2[-2] + 4, pts2[-1] + 4, fill=cyan, outline="")

        # Central Main Sensor Array Radar
        canvas.create_text(cx, cy - main_r - 16, text="TRACKING ACTIVE", fill=cyan_mid, font=("Consolas", 7, "bold"))
        for mult, w_l, col in [(1.0, 1, cyan_dim), (0.82, 2, cyan), (0.62, 1, cyan_mid), (0.38, 2, cyan), (0.14, 2, "#FFFFFF")]:
            rr = main_r * mult
            canvas.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=col, width=w_l)

        for seg in range(8):
            st = math.degrees(-self.sweep_angle) + seg * 45
            canvas.create_arc(
                cx - main_r * 0.52, cy - main_r * 0.52, cx + main_r * 0.52, cy + main_r * 0.52,
                start=st, extent=24, style=tk.ARC, outline=cyan, width=5
            )

        # Rotating radar needle
        nx = cx + math.cos(self.sweep_angle * 1.3) * main_r * 0.85
        ny = cy + math.sin(self.sweep_angle * 1.3) * main_r * 0.85
        canvas.create_line(cx, cy, nx, ny, fill="#FFFFFF", width=2)
        canvas.create_oval(nx - 3, ny - 3, nx + 3, ny + 3, fill=cyan, outline="")
        canvas.create_text(cx, cy + main_r + 22, text="MAIN SENSOR ARRAY  (CLICK ANY SYS DIAL TO TOGGLE)", fill="#E2E8F0", font=("Consolas", 8, "bold"))

    # =========================================================================
    # THEME 3: STARK SCHEMATIC (Image 3 - Exploded Gold/Cyan Arc Reactor)
    # =========================================================================
    def draw_stark_schematic(self, canvas, w, h, accent, is_speaking, rhythm, recent_logs):
        self.hitboxes.clear()
        cx, cy = w * 0.48, h * 0.48
        pulse = rhythm if is_speaking else 0.0
        sep = self.schematic_explode + 0.06 * pulse
        scale_r = min(w, h) * 0.25 * (1.0 + 0.07 * pulse)

        gold_hi = "#FBBF24"
        gold_mid = "#B47B2B"
        gold_dark = "#5C3D14"
        cyan_glow = blend("#00E5FF", "#E0FFFF", 0.4 + 0.5 * pulse)
        cyan_ring = "#00E5FF"

        pitch = 0.44
        yaw = self.schematic_spin

        def proj(x, y, z):
            cyaw, syaw = math.cos(yaw), math.sin(yaw)
            x1 = x * cyaw + z * syaw
            z1 = -x * syaw + z * cyaw
            cpit, spit = math.cos(pitch), math.sin(pitch)
            y2 = y * cpit - z1 * spit
            z2 = y * spit + z1 * cpit
            fov = 3.4
            persp = fov / max(0.85, fov - z2)
            return cx + x1 * scale_r * persp, cy + y2 * scale_r * persp, z2

        def ring(rad, y_pos, n=28):
            return [proj(math.cos(2 * math.pi * i / n) * rad, y_pos, math.sin(2 * math.pi * i / n) * rad) for i in range(n)]

        # Vertical stack heights
        y_cap = -0.35 - sep * 0.85
        y_bezel = -0.22 - sep * 0.62
        y_blocks = -0.10 - sep * 0.40
        y_cage = 0.04 - sep * 0.12
        y_dish = 0.16 + sep * 0.16
        y_pins = 0.27 + sep * 0.44
        y_base = 0.42 + sep * 0.78

        items = []

        # 1. Lower ribbed gold cradle
        for i in range(16):
            ang = (2 * math.pi * i) / 16
            p_top = proj(math.cos(ang) * 0.82, y_base - 0.16, math.sin(ang) * 0.82)
            p_mid = proj(math.cos(ang) * 0.68, y_base + 0.04, math.sin(ang) * 0.68)
            p_bot = proj(math.cos(ang) * 0.36, y_base + 0.22, math.sin(ang) * 0.36)
            items.append((p_mid[2], "line", (p_top[0], p_top[1], p_mid[0], p_mid[1], gold_mid, 3)))
            items.append((p_bot[2], "line", (p_mid[0], p_mid[1], p_bot[0], p_bot[1], gold_hi, 3)))

        base_ring = ring(0.42, y_base + 0.20, 24)
        for i in range(24):
            p0, p1 = base_ring[i], base_ring[(i + 1) % 24]
            items.append(((p0[2] + p1[2]) * 0.5, "line", (p0[0], p0[1], p1[0], p1[1], gold_hi, 3)))

        # 2. Vertical pin collar
        pin_ring = ring(0.66, y_pins, 24)
        for i in range(24):
            p0, p1 = pin_ring[i], pin_ring[(i + 1) % 24]
            items.append(((p0[2] + p1[2]) * 0.5, "line", (p0[0], p0[1], p1[0], p1[1], gold_mid, 3)))
        for i in range(12):
            ang = (2 * math.pi * i) / 12
            pb = proj(math.cos(ang) * 0.56, y_pins + 0.02, math.sin(ang) * 0.56)
            pt = proj(math.cos(ang) * 0.56, y_pins - 0.14, math.sin(ang) * 0.56)
            items.append((pt[2], "line", (pb[0], pb[1], pt[0], pt[1], cyan_glow, 3)))

        # 3. Slotted gold/cyan turbine dish
        dish_outer = ring(0.84, y_dish, 28)
        dish_inner = ring(0.45, y_dish + 0.04, 28)
        for i in range(28):
            p0, p1 = dish_outer[i], dish_outer[(i + 1) % 28]
            items.append(((p0[2] + p1[2]) * 0.5, "line", (p0[0], p0[1], p1[0], p1[1], gold_hi, 2)))
            items.append(((dish_outer[i][2] + dish_inner[i][2]) * 0.5, "line", (dish_outer[i][0], dish_outer[i][1], dish_inner[i][0], dish_inner[i][1], cyan_ring if i % 2 == 0 else gold_dark, 2)))

        # 4. Luminous Cyan Core Ring + Copper Transformer Segments
        cyan_band = ring(0.76, y_cage, 28)
        for i in range(28):
            p0, p1 = cyan_band[i], cyan_band[(i + 1) % 28]
            items.append(((p0[2] + p1[2]) * 0.5, "line", (p0[0], p0[1], p1[0], p1[1], cyan_glow, 6 + int(3 * pulse))))

        for i in range(10):
            ang = (2 * math.pi * i) / 10
            c_top = proj(math.cos(ang) * 0.92, y_cage - 0.06, math.sin(ang) * 0.92)
            c_bot = proj(math.cos(ang) * 0.92, y_cage + 0.06, math.sin(ang) * 0.92)
            items.append((c_top[2], "line", (c_top[0], c_top[1], c_bot[0], c_bot[1], gold_hi, 6)))

        # 5. Upper Gold Bezel & Top Crown
        bez = ring(0.74, y_bezel, 28)
        cap = ring(0.44, y_cap, 24)
        for i in range(28):
            p0, p1 = bez[i], bez[(i + 1) % 28]
            items.append(((p0[2] + p1[2]) * 0.5, "line", (p0[0], p0[1], p1[0], p1[1], gold_hi, 3)))
        for i in range(24):
            p0, p1 = cap[i], cap[(i + 1) % 24]
            items.append(((p0[2] + p1[2]) * 0.5, "line", (p0[0], p0[1], p1[0], p1[1], gold_hi, 3)))

        items.sort(key=lambda x: x[0])
        for _, kind, pl in items:
            if kind == "line":
                canvas.create_line(pl[0], pl[1], pl[2], pl[3], fill=pl[4], width=pl[5])

        # Left Floating Spec Sheet (STARK INDUSTRIES // ARC REACTOR)
        sx, sy = 36, 95
        canvas.create_line(sx, sy, sx, sy + 86, fill=gold_hi, width=2)
        canvas.create_text(sx + 10, sy + 2, anchor="nw", text="STARK INDUSTRIES", fill=gold_mid, font=("Consolas", 7))
        canvas.create_text(sx + 10, sy + 14, anchor="nw", text="ARC REACTOR", fill=gold_hi, font=("Consolas", 11, "bold"))
        canvas.create_text(sx + 10, sy + 32, anchor="nw", text="MARK II   PALLADIUM CORE", fill="#64748B", font=("Consolas", 7))
        canvas.create_text(sx + 10, sy + 50, anchor="nw", text=f"EXPLODE: {int(self.schematic_explode * 100)}%\nOUTPUT: 3.2 GJ/s\nSTATUS: {'PULSING' if is_speaking else 'NOMINAL'}", fill="#CBD5E1", font=("Consolas", 7))

        # Right Scrolling System Terminal Feed
        lx = w - 255
        ly = h * 0.44
        feed = recent_logs[:8] if recent_logs else ["[SYS] Arc Reactor schematic online", "[CORE] Axial separation ready"]
        for idx, line in enumerate(feed):
            short_l = line if len(line) <= 38 else line[:35] + "..."
            canvas.create_text(lx, ly + idx * 14, anchor="nw", text=short_l, fill="#475569" if idx > 2 else "#94A3B8", font=("Consolas", 7))

        # Bottom Interactive Schematic Toolbar
        btns = ["ASSEMBLE", "EXPLODE", "ROTATE", "PULSE", "SPEAK", "RESET"]
        bw, bh, gap = 68, 24, 6
        total_w = len(btns) * bw + (len(btns) - 1) * gap
        start_x = cx - total_w / 2
        by = h - 54
        for idx, label in enumerate(btns):
            bx1 = start_x + idx * (bw + gap)
            bx2 = bx1 + bw
            is_hi = (label == "EXPLODE" and self.schematic_target > 0.6) or (label == "ASSEMBLE" and self.schematic_target < 0.2)
            fill_c = "#0C2D3E" if is_hi else "#07131C"
            out_c = cyan_ring if is_hi else "#163A4F"
            canvas.create_rectangle(bx1, by, bx2, by + bh, fill=fill_c, outline=out_c, width=1)
            canvas.create_text((bx1 + bx2) / 2, by + bh / 2, text=label, fill=cyan_glow if is_hi else "#94A3B8", font=("Consolas", 7, "bold"))
            self._register_box(bx1, by, bx2, by + bh, "schematic_cmd", label)

    # =========================================================================
    # THEME 4: TACTICAL SUITE (Image 4 - Multi-Panel Biometrics/Resources/Core)
    # =========================================================================
    def draw_tactical_suite(self, canvas, w, h, accent, is_speaking, rhythm, recent_logs):
        self.hitboxes.clear()
        pulse = rhythm if is_speaking else 0.0
        cyan = blend("#00E5FF", "#CFFAFE", 0.3 + 0.5 * pulse)
        cyan_mid = "#0E7490"
        border_c = "#123447"
        card_bg = "#060D14"

        # Top HUD header strip
        canvas.create_text(22, 18, anchor="nw", text="◈ JARVIS", fill="#E2E8F0", font=("Consolas", 10, "bold"))
        canvas.create_text(22, 34, anchor="nw", text="JUST A RATHER VERY INTELLIGENT SYSTEM", fill="#475569", font=("Consolas", 6))
        now_str = datetime.now().strftime("%H:%M:%S")
        canvas.create_text(w / 2, 24, text=f"SYSTEM STATUS: ● OPTIMAL    LOCAL TIME: {now_str}", fill=cyan, font=("Consolas", 8, "bold"))

        pad = 16
        top_y = 54
        col_w = min(230, w * 0.27)
        usable_h = h - top_y - 16
        card_h = (usable_h - 20) / 3

        def draw_card(x1, y1, x2, y2, title, tag):
            canvas.create_rectangle(x1, y1, x2, y2, fill=card_bg, outline=border_c, width=1)
            b = 8
            for cx0, cy0, dx, dy in [(x1, y1, b, b), (x2, y1, -b, b), (x1, y2, b, -b), (x2, y2, -b, -b)]:
                canvas.create_line(cx0, cy0, cx0 + dx, cy0, fill=cyan, width=2)
                canvas.create_line(cx0, cy0, cx0, cy0 + dy, fill=cyan, width=2)
            canvas.create_text(x1 + 10, y1 + 10, anchor="nw", text=title, fill="#94A3B8", font=("Consolas", 7, "bold"))
            canvas.create_text(x2 - 10, y1 + 10, anchor="ne", text=tag, fill="#475569", font=("Consolas", 6))

        # --- LEFT COLUMN: BIOMETRICS, SYSTEM RESOURCES, NETWORK ---
        lx1, lx2 = pad, pad + col_w
        # Card 1: Biometrics
        c1_y1, c1_y2 = top_y, top_y + card_h
        draw_card(lx1, c1_y1, lx2, c1_y2, "SYSTEM // BIOMETRICS", "VITAL_SIGNS")
        hr_val = self.last_telemetry["hr"] + (int(8 * pulse) if is_speaking else 0)
        canvas.create_text(lx1 + 12, c1_y1 + 30, anchor="nw", text=f"{hr_val} BPM", fill=cyan, font=("Consolas", 13, "bold"))
        bar_area_w = col_w - 24
        bw = bar_area_w / len(self.bio_bars)
        for i, val in enumerate(self.bio_bars):
            bh = (card_h * 0.32) * (val / 100.0)
            bx = lx1 + 12 + i * bw
            by_bot = c1_y2 - 12
            canvas.create_rectangle(bx, by_bot - bh, bx + max(2, bw - 2), by_bot, fill=cyan_mid if i % 2 else cyan, outline="")

        # Card 2: System Resources
        c2_y1, c2_y2 = c1_y2 + 10, c1_y2 + 10 + card_h
        draw_card(lx1, c2_y1, lx2, c2_y2, "SYSTEM // RESOURCES", "SYS_MON")
        for idx, (lbl, pct) in enumerate([
            ("CPU Load", self.last_telemetry["cpu"]),
            ("Memory", self.last_telemetry["ram"]),
            ("Storage", self.last_telemetry["storage"]),
        ]):
            ry = c2_y1 + 34 + idx * ((card_h - 44) / 3)
            canvas.create_text(lx1 + 12, ry, anchor="nw", text=lbl, fill="#CBD5E1", font=("Consolas", 7))
            canvas.create_text(lx2 - 12, ry, anchor="ne", text=f"{pct}%", fill=cyan, font=("Consolas", 7, "bold"))
            bar_y = ry + 13
            canvas.create_rectangle(lx1 + 12, bar_y, lx2 - 12, bar_y + 4, fill="#0D2230", outline="")
            fill_x = lx1 + 12 + (col_w - 24) * (pct / 100.0)
            canvas.create_rectangle(lx1 + 12, bar_y, fill_x, bar_y + 4, fill=cyan, outline="")

        # Card 3: Network
        c3_y1, c3_y2 = c2_y2 + 10, top_y + usable_h
        draw_card(lx1, c3_y1, lx2, c3_y2, "SYSTEM // NETWORK", "UPLINK")
        ncx, ncy = (lx1 + lx2) / 2, (c3_y1 + c3_y2) / 2 + 8
        nr = min(26, (c3_y2 - c3_y1) * 0.28)
        canvas.create_oval(ncx - nr, ncy - nr, ncx + nr, ncy + nr, outline=cyan, width=2)
        canvas.create_text(ncx, ncy, text="LINK ACTIVE", fill=cyan, font=("Consolas", 6, "bold"))

        # --- RIGHT COLUMN: ARMOR STATUS, SYSTEM LOGS, TERMINAL ---
        rx1, rx2 = w - pad - col_w, w - pad
        r1_y1, r1_y2 = top_y, top_y + card_h
        draw_card(rx1, r1_y1, rx2, r1_y2, "SYSTEM // ARMOR STATUS", "MARK_LXXXV")
        canvas.create_text(rx1 + 12, r1_y1 + 30, anchor="nw", text="POWER: 98%    STRUCTURAL: 100%", fill=cyan, font=("Consolas", 7, "bold"))
        btn_w = (col_w - 36) / 4
        btn_icons = ["🛡", "⚡", "📡", "⏻"]
        for i, ico in enumerate(btn_icons):
            bx1 = rx1 + 12 + i * (btn_w + 4)
            bx2 = bx1 + btn_w
            by1 = r1_y2 - 38
            by2 = r1_y2 - 12
            on = self.armor_buttons[i]
            canvas.create_rectangle(bx1, by1, bx2, by2, fill="#0B2A3A" if on else "#08141E", outline=cyan if on else border_c, width=1)
            canvas.create_text((bx1 + bx2) / 2, (by1 + by2) / 2, text=ico, fill=cyan if on else "#64748B", font=("Segoe UI", 9))
            self._register_box(bx1, by1, bx2, by2, "armor_btn", i)

        r2_y1, r2_y2 = r1_y2 + 10, r1_y2 + 10 + card_h * 1.25
        draw_card(rx1, r2_y1, rx2, r2_y2, "SYSTEM // LOGS", "IO_LOG")
        logs_show = recent_logs[:6] if recent_logs else ["SYSTEM INTEGRITY CHECK COMPLETE", "BIO-SYNC STABLE", "ARC REACTOR OPTIMAL"]
        for idx, entry in enumerate(logs_show):
            txt = entry if len(entry) <= 30 else entry[:27] + "..."
            canvas.create_text(rx1 + 10, r2_y1 + 28 + idx * 16, anchor="nw", text=f"> {txt}", fill="#94A3B8", font=("Consolas", 7))

        r3_y1, r3_y2 = r2_y2 + 10, top_y + usable_h
        draw_card(rx1, r3_y1, rx2, r3_y2, "SYSTEM // TERMINAL", "CMD_SHELL")
        canvas.create_text(rx1 + 10, r3_y1 + 30, anchor="nw", text="> jarvis --status --live\n  All subsystems nominal.", fill=cyan, font=("Consolas", 7))

        # --- CENTER RADAR & VOICE WAVEFORM ---
        ccx, ccy = w / 2, h * 0.48
        cr = min(w - 2 * col_w - 90, usable_h * 0.56) * 0.5 * (1.0 + 0.08 * pulse)
        cr = max(65, cr)

        canvas.create_oval(ccx - cr, ccy - cr, ccx + cr, ccy + cr, outline=border_c, width=1, dash=(4, 4))
        canvas.create_oval(ccx - cr * 0.82, ccy - cr * 0.82, ccx + cr * 0.82, ccy + cr * 0.82, outline=cyan_mid, width=1)
        canvas.create_oval(ccx - cr * 0.34, ccy - cr * 0.34, ccx + cr * 0.34, ccy + cr * 0.34, outline=cyan, width=2)

        for seg in range(2):
            st = math.degrees(self.sweep_angle) + seg * 180
            canvas.create_arc(
                ccx - cr * 0.82, ccy - cr * 0.82, ccx + cr * 0.82, ccy + cr * 0.82,
                start=st, extent=18, style=tk.ARC, outline=cyan, width=4
            )

        canvas.create_text(ccx, ccy, text="CORE\nACTIVE", fill=cyan, font=("Consolas", 9, "bold"))

        # Live Voice Equalizer Bars + AWAITING COMMAND Pill
        eq_y = ccy + cr + 26
        for b in range(-9, 10):
            amp = (0.25 + 0.75 * abs(math.sin(self.phase * 5.0 + b * 0.6))) * (1.0 if is_speaking else 0.25)
            eh = 4 + 16 * amp
            bx = ccx + b * 5
            canvas.create_line(bx, eq_y - eh / 2, bx, eq_y + eh / 2, fill=cyan, width=2)

        pill_y = eq_y + 24
        canvas.create_rectangle(ccx - 95, pill_y - 13, ccx + 95, pill_y + 13, fill="#071824", outline=cyan, width=1)
        canvas.create_text(ccx, pill_y, text="🎙 AWAITING COMMAND...", fill=cyan, font=("Consolas", 7, "bold"))
        self._register_box(ccx - 95, pill_y - 13, ccx + 95, pill_y + 13, "mic_trigger")