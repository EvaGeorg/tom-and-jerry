# 🐱🐭  Tom & Jerry - Linux  AI Desktop Companions

Two pixel-art AI characters live on your Linux desktop. **Tom** (a gray cat) handles system and productivity tasks. **Jerry** (a brown mouse) handles information and fun. Double-click either one to open their AI chat terminal.

Inspired by [lil agents](https://github.com/ryanstephen/lil-agents) by [@Ryan__Stephen](https://x.com/Ryan__Stephen) — reimagined for Linux with Python, GTK3, and dual-character specialization.

## Demo

```
┌──────────────────────────────────────────────────────┐
│                    Your screen                        │
│                                                       │
│    🐱 Tom ←────── left half ──────┤                   │
│                                   │                   │
│                    ├───── right half ──────→ 🐭 Jerry │
│                                                       │
│   "checking processes..."          "ooh what's this?" │
└──────────────────────────────────────────────────────┘
```

## Features

- **Two AI-powered characters** walking your screen simultaneously
- **Tom (system agent)** — CPU/RAM monitoring, file management, scripts, automation
- **Jerry (info agent)** — search, summaries, explanations, fun facts, creative help
- **Separate screen zones** — Tom walks the left half, Jerry walks the right half
- **Character-specific chat windows** — cool blue theme for Tom, warm amber for Jerry
- **Light banter** — they occasionally reference each other in speech bubbles
- **CLAUDE.md personalities** — each agent has its own personality and task focus
- **Transparent overlay** — pixel art floats above everything
- **Draggable** — click and drag to reposition either character
- **No accounts, no telemetry** — runs entirely locally

## Requirements

- **Ubuntu/Debian Linux** (or any distro with GTK3)
- **Python 3.8+**
- **PyGObject** (GTK3 bindings)
- **Pillow** (for sprite generation)
- **Vte** (for embedded terminal)
- **Claude Code CLI** (for AI chat — optional, falls back to shell)

## Installation

### 1. Install system dependencies

```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    gir1.2-vte-2.91 python3-pil

# Fedora
sudo dnf install python3-gobject gtk3 vte291 python3-pillow

# Arch
sudo pacman -S python-gobject gtk3 vte3 python-pillow
```

### 2. Clone and set up

```bash
git clone https://github.com/EvaGeorg/tom-and-jerry.git
cd agent-waf
```

### 3. Setup agent personalities

```bash
python3 setup_agents.py
```

This creates `~/.agent-waf/` with personality files:
- `tom/CLAUDE.md` — System agent personality and task instructions
- `jerry/CLAUDE.md` — Info agent personality and task instructions
- `shared/` — Shared space both agents can access

### 4. Generate pixel art sprites

```bash
python3 generate_sprites.py
```

### 5. Install Claude Code CLI (optional)

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Requires a Claude Pro, Max, or Teams subscription. Without it, the chat windows will open a regular shell instead.

### 6. Run!

```bash
python3 lil_companion.py
```

## Usage

| Action | What happens |
|--------|-------------|
| **Double-click Tom** | Opens Tom's chat (system tasks) |
| **Double-click Jerry** | Opens Jerry's chat (info tasks) |
| **Click + drag** | Move a character around |
| **Right-click** | Context menu (chat, flip, quit) |
| **Single click** | Character says a phrase |

## How It Works

### The characters

**Tom** walks the left half of your screen. His chat terminal launches `claude` in `~/.tom-and-jerry/tom/`, where a `CLAUDE.md` file tells Claude to behave as a reliable, slightly sarcastic system agent. Ask him to check CPU usage, find files, run scripts, or clean up disk space.

**Jerry** walks the right half. His chat launches in `~/.tom-and-jerry/jerry/`, where his `CLAUDE.md` makes Claude a curious, playful info agent. Ask him to summarize documents, explain concepts, brainstorm ideas, or tell you a fun fact.

### The banter

Tom and Jerry occasionally show speech bubbles that reference each other:
- Tom: *"Jerry's being suspiciously quiet..."*
- Jerry: *"Tom looks grumpy today!"*
- Tom: *"Jerry found 3 typos. I found 3 security holes."*
- Jerry: *"I bet Tom's just running htop again."*

### Architecture

```
tom-and-jerry/
├── lil_companion.py       # Main app — 2 pets, 2 chat windows, banter
├── generate_sprites.py    # Pixel art generator — Tom + Jerry
├── setup_agents.py        # Creates ~/.agent-waf/ personality files
├── sprites/
│   ├── tom/               # 16 PNG frames (walk + idle × 4 × 2 dirs)
│   └── jerry/             # 16 PNG frames
└── README.md

~/.tom-and-jerry/              # Created by setup_agents.py
├── tom/
│   └── CLAUDE.md          # "You are Tom, a system-focused agent..."
├── jerry/
│   └── CLAUDE.md          # "You are Jerry, an info-focused agent..."
└── shared/                # Shared space for both agents
```

### How specialization works

Claude Code reads a `CLAUDE.md` file in its working directory for context. By launching each character's chat in a different directory with a different `CLAUDE.md`, we get genuinely different agent behaviors from the same CLI — no API keys required.

## Customization

### Edit personalities

```bash
# Customize Tom's behavior
nano ~/.tom-and-jerry/tom/CLAUDE.md

# Customize Jerry's behavior
nano ~/.tom-and-jerry/jerry/CLAUDE.md
```

### Custom sprites

Replace PNGs in `sprites/tom/` or `sprites/jerry/`. Each character needs:
- `walk_right_0.png` through `walk_right_3.png`
- `walk_left_0.png` through `walk_left_3.png`
- `idle_right_0.png` through `idle_right_3.png`
- `idle_left_0.png` through `idle_left_3.png`

Each frame: 128×128 pixels, RGBA PNG, transparent background.

### Autostart on login

Create `~/.config/autostart/tom-and-jerry.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Tom and Jerry
Comment=Tom & Jerry AI Desktop Companions
Exec=python3 /path/to/agent-waf/lil_companion.py
Hidden=false
X-GNOME-Autostart-enabled=true
```

## Troubleshooting

**Characters not transparent / black background**
- You need a compositing window manager (most modern desktops have one)
- On X11 without compositing: install `picom` or `xcompmgr`

**Chat opens but can't type**
- Make sure `gir1.2-vte-2.91` is installed
- The terminal needs focus — click inside the terminal area

**Claude not found**
- Install: `curl -fsSL https://claude.ai/install.sh | bash`
- Verify: `claude --version`
- The app searches `~/.local/bin` automatically

**Sprites not found**
- Run `python3 generate_sprites.py` first
- Check that `sprites/tom/` and `sprites/jerry/` directories exist

## Current Limitations

This is a **desktop pet with CLI wrapping**, not a true AI agent (yet). The characters don't have their own brain — they open Claude Code in themed terminals. Real agent capabilities (autonomous actions, persistent memory, custom tools, proactive notifications) would require switching from CLI wrapping to the Claude API directly. See the roadmap below.

## Roadmap

- [ ] **v3: Real agents** — Replace CLI wrapping with Claude API calls (`pip install anthropic`)
- [ ] **Custom chat UI** — Replace Vte terminal with a GTK chat widget
- [ ] **Tools** — Tom: `psutil`, `subprocess`, file ops. Jerry: file search, text summary
- [ ] **Memory** — Persistent conversation history across sessions
- [ ] **Autonomous triggers** — Tom monitors system, Jerry watches for interesting events
- [ ] **Tom ↔ Jerry communication** — They can talk to each other about your tasks

## Credits

Inspired by [lil agents](https://github.com/ryanstephen/lil-agents) by Ryan Stephen — tiny AI companions for macOS. Tom and Jerry is a Linux reimplementation with dual-character specialization using Python + GTK3.

## License

MIT
