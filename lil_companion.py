#!/usr/bin/env python3
"""
Agent Waf — Tom & Jerry AI Desktop Companions for Linux

Two pixel-art characters walk your screen. Tom (system agent) on the left,
Jerry (info agent) on the right. Double-click either to open their AI chat.

Install:  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-vte-2.91 python3-pil
Setup:    python3 setup_agents.py && python3 generate_sprites.py
Run:      python3 lil_companion.py
"""

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

import os, sys, random, argparse, signal, shutil
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango

HAS_VTE = False
try:
    gi.require_version("Vte", "2.91")
    from gi.repository import Vte
    HAS_VTE = True
except (ImportError, ValueError):
    pass

# ─── Configuration ─────────────────────────────────────────────────────────

SPRITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprites")
AGENT_DIR = os.path.join(os.path.expanduser("~"), ".tom-and-jerry")
PET_SIZE = 128
ANIMATION_FPS = 8
IDLE_FPS = 3
WALK_SPEED = 3
IDLE_CHANCE = 0.005
WALK_CHANCE = 0.01
BOTTOM_MARGIN = 48

# Tom's theme — cool blue-grays
TOM_THEME = {
    "bg": "#181C24", "fg": "#C0C8D8", "accent": "#6C8EBF",
    "border": "#252C38", "title": "#8CAAD4", "header_bg": "#1E2430",
    "cursor": "#6C8EBF", "dim": "#556070", "selection_bg": "#283248",
    "name": "Tom", "icon": "🐱",
}

# Jerry's theme — warm amber-browns
JERRY_THEME = {
    "bg": "#241C14", "fg": "#D8CCBC", "accent": "#D4944C",
    "border": "#342818", "title": "#E8A860", "header_bg": "#2C2018",
    "cursor": "#D4944C", "dim": "#887058", "selection_bg": "#3C2C1C",
    "name": "Jerry", "icon": "🐭",
}

# Character-specific thinking phrases
TOM_PHRASES = [
    "checking processes...", "scanning files...", "*yawn*",
    "running diagnostics...", "optimizing...", "cleaning up...",
    "Jerry's being noisy...", "system looks stable.", "analyzing logs...",
    "another cron job done.", "*stretches*", "disk space OK.",
]
JERRY_PHRASES = [
    "ooh what's this?", "searching...", "*sniff sniff*",
    "found something!", "that's interesting!", "Tom's napping again...",
    "let me check!", "fun fact loading...", "idea incoming!",
    "reading docs...", "*scurries around*", "eureka!",
]

# Banter — Tom and Jerry reference each other
TOM_BANTER = [
    "Jerry's being suspiciously quiet...",
    "I can hear Jerry typing over there.",
    "System's fine. Unlike Jerry's attention span.",
    "Another day, another log file.",
    "Jerry found 3 typos. I found 3 security holes.",
]
JERRY_BANTER = [
    "Tom looks grumpy today!",
    "I bet Tom's just running htop again.",
    "Hey Tom, I found a fun bug!",
    "Tom's so serious. Lighten up, cat!",
    "I'm faster than Tom at everything except napping.",
]


def hex_to_rgba(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    return Gdk.RGBA(r, g, b, 1.0)


def find_cli_binary(name):
    home = os.path.expanduser("~")
    for path in [
        os.path.join(home, ".local", "bin", name),
        os.path.join(home, ".npm-global", "bin", name),
        f"/usr/local/bin/{name}", f"/usr/bin/{name}",
    ]:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    old = os.environ.get("PATH", "")
    os.environ["PATH"] = os.path.join(home, ".local", "bin") + ":" + old
    result = shutil.which(name)
    os.environ["PATH"] = old
    return result


def resolve_claude():
    if shutil.which("claude"):
        return "claude"
    found = find_cli_binary("claude")
    return found


# ─── SpriteSheet ───────────────────────────────────────────────────────────

class SpriteSheet:
    def __init__(self, character):
        self.animations = {}
        char_dir = os.path.join(SPRITE_DIR, character)
        if not os.path.isdir(char_dir):
            print(f"ERROR: sprites/{character}/ not found. Run generate_sprites.py")
            sys.exit(1)
        for name in ["walk_right", "walk_left", "idle_right", "idle_left"]:
            frames = []
            for i in range(8):
                path = os.path.join(char_dir, f"{name}_{i}.png")
                if os.path.exists(path):
                    pb = GdkPixbuf.Pixbuf.new_from_file(path)
                    pb = pb.scale_simple(PET_SIZE, PET_SIZE, GdkPixbuf.InterpType.NEAREST)
                    frames.append(pb)
            if frames:
                self.animations[name] = frames
        if not self.animations:
            print(f"ERROR: No sprites for '{character}'!")
            sys.exit(1)

    def get_frame(self, anim, idx):
        frames = self.animations.get(anim, [])
        return frames[idx % len(frames)] if frames else None


# ─── ThinkingBubble ────────────────────────────────────────────────────────

class ThinkingBubble(Gtk.Window):
    def __init__(self, theme):
        super().__init__(type=Gtk.WindowType.POPUP)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.theme = theme
        self.label = Gtk.Label()
        for side in ['start', 'end']:
            getattr(self.label, f'set_margin_{side}')(14)
        self.label.set_margin_top(8)
        self.label.set_margin_bottom(8)
        self.add(self.label)
        css = f"""
        window {{ background-color: {theme['header_bg']}; border: 1px solid {theme['accent']}; border-radius: 14px; }}
        label {{ color: {theme['fg']}; font-family: 'Ubuntu Mono', monospace; font-size: 13px; font-weight: 600; }}
        """
        cp = Gtk.CssProvider()
        cp.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), cp, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)
        self.hide_timeout = None

    def show_phrase(self, x, y, phrase):
        self.label.set_text(phrase)
        self.show_all()
        w, h = self.get_size()
        self.move(x - w // 2 + PET_SIZE // 2, y - h - 10)
        if self.hide_timeout:
            GLib.source_remove(self.hide_timeout)
        self.hide_timeout = GLib.timeout_add(3000, self._hide)

    def _hide(self):
        self.hide()
        self.hide_timeout = None
        return False


# ─── ChatWindow ────────────────────────────────────────────────────────────

class ChatWindow(Gtk.Window):
    def __init__(self, theme, claude_bin, agent_cwd):
        super().__init__(title=f"Agent Waf — {theme['name']}")
        self.set_default_size(740, 540)
        self.set_skip_taskbar_hint(False)
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.theme = theme
        self.claude_bin = claude_bin
        self.agent_cwd = agent_cwd
        self._build_ui()
        self.connect("delete-event", lambda w, e: (self.hide(), True)[-1])

    def _build_ui(self):
        t = self.theme
        # Unique CSS class per character to avoid collisions
        cls = f"waf-{t['name'].lower()}"
        css = f"""
        .{cls} {{ background-color: {t['bg']}; }}
        .{cls}-header {{ background-color: {t['header_bg']}; border-bottom: 1px solid {t['border']}; padding: 10px 18px; }}
        .{cls}-title {{ color: {t['title']}; font-family: 'Ubuntu Mono', monospace; font-size: 15px; font-weight: 700; }}
        .{cls}-dim {{ color: {t['dim']}; font-family: 'Ubuntu Mono', monospace; font-size: 12px; }}
        .{cls}-dot {{ color: {t['accent']}; font-size: 10px; }}
        """
        cp = Gtk.CssProvider()
        cp.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), cp, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2)

        self.get_style_context().add_class(cls)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.get_style_context().add_class(f"{cls}-header")
        dot = Gtk.Label(label="●")
        dot.get_style_context().add_class(f"{cls}-dot")
        header.pack_start(dot, False, False, 0)
        title = Gtk.Label(label=f"{t['icon']} {t['name']}")
        title.get_style_context().add_class(f"{cls}-title")
        header.pack_start(title, False, False, 0)
        role = "System agent" if t['name'] == "Tom" else "Info agent"
        rlabel = Gtk.Label(label=f"[{role}]")
        rlabel.get_style_context().add_class(f"{cls}-dim")
        header.pack_end(rlabel, False, False, 8)
        vbox.pack_start(header, False, False, 0)

        if HAS_VTE:
            self.terminal = Vte.Terminal()
            self.terminal.set_color_background(hex_to_rgba(t['bg']))
            self.terminal.set_color_foreground(hex_to_rgba(t['fg']))
            self.terminal.set_color_cursor(hex_to_rgba(t['cursor']))
            self.terminal.set_color_cursor_foreground(hex_to_rgba(t['bg']))
            self.terminal.set_color_highlight(hex_to_rgba(t['selection_bg']))
            self.terminal.set_color_highlight_foreground(hex_to_rgba(t['fg']))
            palette = [
                hex_to_rgba(t['bg']),  hex_to_rgba("#E06C75"),
                hex_to_rgba("#98C379"), hex_to_rgba("#E5C07B"),
                hex_to_rgba("#61AFEF"), hex_to_rgba("#C678DD"),
                hex_to_rgba("#56B6C2"), hex_to_rgba("#ABB2BF"),
                hex_to_rgba(t['dim']), hex_to_rgba("#E06C75"),
                hex_to_rgba("#98C379"), hex_to_rgba("#E5C07B"),
                hex_to_rgba("#61AFEF"), hex_to_rgba("#C678DD"),
                hex_to_rgba("#56B6C2"), hex_to_rgba(t['fg']),
            ]
            self.terminal.set_colors(hex_to_rgba(t['fg']), hex_to_rgba(t['bg']), palette)
            self.terminal.set_font(Pango.FontDescription.from_string("Ubuntu Mono 13"))
            self.terminal.set_scroll_on_output(True)
            self.terminal.set_scroll_on_keystroke(True)
            self.terminal.set_scrollback_lines(10000)
            self.terminal.set_cursor_blink_mode(Vte.CursorBlinkMode.ON)
            self.terminal.set_cursor_shape(Vte.CursorShape.BLOCK)
            self.terminal.set_can_focus(True)
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scroll.add(self.terminal)
            vbox.pack_start(scroll, True, True, 0)
            self.terminal.connect("child-exited", lambda t, s: GLib.timeout_add(800, self.spawn_shell))
        else:
            lbl = Gtk.Label(label="Install gir1.2-vte-2.91 for embedded terminal")
            lbl.set_valign(Gtk.Align.CENTER)
            vbox.pack_start(lbl, True, True, 0)

    def spawn_shell(self):
        if not HAS_VTE:
            return False
        home = os.path.expanduser("~")
        shell = os.environ.get("SHELL", "/bin/bash")
        env = os.environ.copy()
        for p in [os.path.join(home, ".local", "bin"), os.path.join(home, ".npm-global", "bin")]:
            if p not in env.get("PATH", ""):
                env["PATH"] = p + ":" + env.get("PATH", "")
        env["TERM"] = "xterm-256color"
        env_list = [f"{k}={v}" for k, v in env.items()]

        if self.claude_bin:
            cmd = [shell, "-l", "-c", f"cd {self.agent_cwd} && exec {self.claude_bin}"]
        else:
            cmd = [shell, "-l", "-c", f"cd {self.agent_cwd} && exec {shell}"]

        self.terminal.spawn_async(
            Vte.PtyFlags.DEFAULT, home, cmd, env_list,
            GLib.SpawnFlags.DEFAULT, None, None, -1, None, None)
        return False

    def focus_terminal(self):
        if HAS_VTE and hasattr(self, 'terminal'):
            self.terminal.grab_focus()
        return False


# ─── DesktopPet ────────────────────────────────────────────────────────────

class DesktopPet(Gtk.Window):
    def __init__(self, character, theme, phrases, banter, claude_bin,
                 x_min, x_max, screen_height):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.character = character
        self.theme = theme
        self.phrases = phrases
        self.banter = banter
        self.claude_bin = claude_bin
        self.x_min = x_min
        self.x_max = x_max

        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_app_paintable(True)
        self.set_default_size(PET_SIZE, PET_SIZE)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.stick()
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.sprites = SpriteSheet(character)
        self.state = "walk"
        self.direction = 1
        self.frame_index = 0
        self.x = x_min + (x_max - x_min) // 4
        self.y = screen_height - PET_SIZE - BOTTOM_MARGIN
        self.dragging = False
        self.drag_offset = (0, 0)

        self.image = Gtk.Image()
        self.add(self.image)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect("button-press-event", self._on_click)
        self.connect("button-release-event", lambda w, e: setattr(self, 'dragging', False))
        self.connect("motion-notify-event", self._on_motion)
        self.connect("draw", self._on_draw)

        self.bubble = ThinkingBubble(theme)
        self.chat_window = None
        self.agent_cwd = os.path.join(AGENT_DIR, character)

        self.move(self.x, self.y)
        self.anim_timer = GLib.timeout_add(1000 // ANIMATION_FPS, self._animate)
        GLib.timeout_add(random.randint(6000, 12000), self._random_thought)
        self._update_frame()

    def _on_draw(self, widget, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(0)
        cr.paint()
        cr.set_operator(2)
        return False

    def _update_frame(self):
        anim = ("walk_" if self.state == "walk" else "idle_") + \
               ("right" if self.direction == 1 else "left")
        f = self.sprites.get_frame(anim, self.frame_index)
        if f:
            self.image.set_from_pixbuf(f)

    def _animate(self):
        self.frame_index += 1
        if self.state == "walk":
            self.x += WALK_SPEED * self.direction
            if self.x >= self.x_max - PET_SIZE:
                self.direction = -1
                self.x = self.x_max - PET_SIZE
            elif self.x <= self.x_min:
                self.direction = 1
                self.x = self.x_min
            if random.random() < IDLE_CHANCE:
                self.state = "idle"
                self.frame_index = 0
                GLib.source_remove(self.anim_timer)
                self.anim_timer = GLib.timeout_add(1000 // IDLE_FPS, self._animate)
        else:
            if random.random() < WALK_CHANCE:
                self.state = "walk"
                self.frame_index = 0
                if random.random() < 0.3:
                    self.direction *= -1
                GLib.source_remove(self.anim_timer)
                self.anim_timer = GLib.timeout_add(1000 // ANIMATION_FPS, self._animate)
        if not self.dragging:
            self.move(self.x, self.y)
        self._update_frame()
        return True

    def _random_thought(self):
        if self.state == "idle" and random.random() < 0.5:
            # 30% chance of banter, 70% normal phrase
            if random.random() < 0.3:
                phrase = random.choice(self.banter)
            else:
                phrase = random.choice(self.phrases)
            self.bubble.show_phrase(self.x, self.y, phrase)
        # Re-schedule with some randomness
        GLib.timeout_add(random.randint(6000, 15000), self._random_thought)
        return False

    def _on_click(self, widget, event):
        if event.button == 1:
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self._open_chat()
            else:
                self.dragging = True
                self.drag_offset = (event.x_root - self.x, event.y_root - self.y)
                self.bubble.show_phrase(self.x, self.y,
                    random.choice(self.phrases))
        elif event.button == 3:
            self._show_menu(event)

    def _on_motion(self, widget, event):
        if self.dragging:
            self.x = int(event.x_root - self.drag_offset[0])
            self.y = int(event.y_root - self.drag_offset[1])
            self.move(self.x, self.y)

    def _open_chat(self):
        if self.chat_window is None:
            self.chat_window = ChatWindow(self.theme, self.claude_bin, self.agent_cwd)
            self.chat_window.show_all()
            self.chat_window.spawn_shell()
            GLib.timeout_add(200, self.chat_window.focus_terminal)
        else:
            self.chat_window.show_all()
            self.chat_window.present()
            GLib.timeout_add(100, self.chat_window.focus_terminal)
        name = self.theme['name']
        self.bubble.show_phrase(self.x, self.y,
            f"{name} reporting in!" if name == "Tom" else "Let's go!")

    def _show_menu(self, event):
        menu = Gtk.Menu()
        t = self.theme
        css = f"""
        menu {{ background-color: {t['header_bg']}; border: 1px solid {t['border']}; border-radius: 8px; padding: 4px 0; }}
        menu menuitem {{ color: {t['fg']}; font-family: 'Ubuntu Mono', monospace; font-size: 13px; padding: 6px 16px; border-radius: 4px; margin: 1px 4px; }}
        menu menuitem:hover {{ background-color: {t['selection_bg']}; color: {t['accent']}; }}
        menu separator {{ background-color: {t['border']}; margin: 4px 8px; min-height: 1px; }}
        """
        cp = Gtk.CssProvider()
        cp.load_from_data(css.encode())
        def style(w):
            w.get_style_context().add_provider(cp, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 10)
            if isinstance(w, Gtk.Container): w.forall(style)

        chat = Gtk.MenuItem(label=f"{t['icon']}  Chat with {t['name']}")
        chat.connect("activate", lambda w: self._open_chat())
        menu.append(chat)
        flip = Gtk.MenuItem(label="↔  Flip direction")
        flip.connect("activate", lambda w: (setattr(self, 'direction', self.direction * -1), self._update_frame()))
        menu.append(flip)
        menu.append(Gtk.SeparatorMenuItem())
        quit_item = Gtk.MenuItem(label="👋  Quit all")
        quit_item.connect("activate", lambda w: Gtk.main_quit())
        menu.append(quit_item)
        menu.show_all()
        style(menu)
        menu.popup_at_pointer(event)


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="🐱🐭 Agent Waf — Tom & Jerry AI Companions")
    parser.add_argument("--no-chat", action="store_true", help="Disable AI chat")
    args = parser.parse_args()

    # Check agent directories exist
    if not os.path.isdir(os.path.join(AGENT_DIR, "tom")):
        print("⚠️  Agent directories not found. Running setup...")
        import subprocess
        subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "setup_agents.py")])

    # Check sprites exist
    if not os.path.isdir(os.path.join(SPRITE_DIR, "tom")):
        print("⚠️  Sprites not found. Run: python3 generate_sprites.py")
        sys.exit(1)

    # Find claude binary
    claude_bin = None if args.no_chat else resolve_claude()
    if not args.no_chat and not claude_bin:
        print("⚠️  'claude' not found. Chat will open a regular shell.")
        print("   Install: curl -fsSL https://claude.ai/install.sh | bash\n")

    # Get screen geometry
    display = Gdk.Display.get_default()
    monitor = display.get_primary_monitor() or display.get_monitor(0)
    geom = monitor.get_geometry()
    sw, sh = geom.width, geom.height
    mid = sw // 2

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Create Tom (left half)
    tom = DesktopPet(
        character="tom", theme=TOM_THEME,
        phrases=TOM_PHRASES, banter=TOM_BANTER,
        claude_bin=claude_bin,
        x_min=0, x_max=mid, screen_height=sh)

    # Create Jerry (right half)
    jerry = DesktopPet(
        character="jerry", theme=JERRY_THEME,
        phrases=JERRY_PHRASES, banter=JERRY_BANTER,
        claude_bin=claude_bin,
        x_min=mid, x_max=sw, screen_height=sh)

    # Connect quit to both
    tom.connect("destroy", Gtk.main_quit)
    jerry.connect("destroy", Gtk.main_quit)

    tom.show_all()
    jerry.show_all()

    status = f"claude → {claude_bin}" if claude_bin else "shell (claude not found)"
    print(f"🐱🐭 Agent Waf is running!")
    print(f"   Tom (left)  — system & productivity")
    print(f"   Jerry (right) — info & fun")
    print(f"   Chat: {status}")
    print(f"   Double-click a character → open their chat")
    print(f"   Right-click → menu  |  Ctrl+C → quit\n")

    Gtk.main()


if __name__ == "__main__":
    main()
