#!/usr/bin/env python3
"""Generate Tom & Jerry pixel-art sprites for Agent Waf.

Each character: 4 animations × 4 frames × 2 directions = 16 PNGs
Canvas: 32×32 pixel art, scaled 4x → 128×128 display.
"""

from PIL import Image, ImageDraw
import os
import shutil

SCALE = 4
W, H = 32, 32
T = (0, 0, 0, 0)


def px(draw, x, y, color, d=1):
    if d == -1:
        x = W - 1 - x
    draw.rectangle([x*SCALE, y*SCALE, (x+1)*SCALE-1, (y+1)*SCALE-1], fill=color)


def frame():
    img = Image.new("RGBA", (W*SCALE, H*SCALE), T)
    return img, ImageDraw.Draw(img)


# ━━━ TOM — Gray cat, big, slightly smug ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOM = {
    "body":       (140, 145, 155, 255),   # blue-gray
    "body_light": (175, 180, 192, 255),   # highlights
    "body_dark":  (105, 108, 118, 255),   # shadows
    "belly":      (195, 200, 210, 255),   # light chest
    "ear_outer":  (130, 135, 145, 255),
    "ear_inner":  (200, 140, 150, 255),   # pink
    "eye_white":  (240, 240, 230, 255),
    "eye_green":  (90, 180, 90, 255),     # green iris
    "eye_pupil":  (30, 30, 35, 255),
    "nose":       (190, 140, 140, 255),   # pink nose
    "mouth":      (80, 80, 90, 255),
    "whisker":    (210, 210, 220, 255),
    "paw":        (210, 215, 225, 255),   # white paws
    "tail_tip":   (115, 118, 128, 255),
}


def tom_walk(draw, phase, d=1):
    c = TOM
    P = lambda x, y, col: px(draw, x, y, col, d)

    # Tail (behind body, curves up)
    tail_y = [0, -1, -1, 0][phase]
    P(6, 16+tail_y, c["body_dark"])
    P(5, 15+tail_y, c["body"])
    P(4, 14+tail_y, c["body"])
    P(3, 13+tail_y, c["tail_tip"])

    # Body
    for x in range(9, 22):
        for y in range(13, 22):
            P(x, y, c["body"])
    # Shading
    for x in range(10, 21):
        P(x, 13, c["body_light"])
        P(x, 21, c["body_dark"])
    # Belly
    for x in range(12, 19):
        for y in range(17, 22):
            P(x, y, c["belly"])

    # Head (larger — Tom has a big head)
    for x in range(13, 26):
        for y in range(5, 14):
            P(x, y, c["body"])
    # Face lighter zone
    for x in range(15, 24):
        for y in range(7, 13):
            P(x, y, c["body_light"])
    # Muzzle
    for x in range(20, 26):
        for y in range(9, 13):
            P(x, y, c["belly"])

    # Ears — tall pointed
    P(14, 2, c["ear_outer"]); P(15, 2, c["ear_outer"])
    P(14, 3, c["ear_outer"]); P(15, 3, c["ear_inner"]); P(16, 3, c["ear_outer"])
    P(14, 4, c["ear_outer"]); P(15, 4, c["ear_inner"]); P(16, 4, c["body"])
    P(22, 2, c["ear_outer"]); P(23, 2, c["ear_outer"])
    P(21, 3, c["ear_outer"]); P(22, 3, c["ear_inner"]); P(23, 3, c["ear_outer"])
    P(21, 4, c["body"]);      P(22, 4, c["ear_inner"]); P(23, 4, c["ear_outer"])

    # Eyes — Tom's smug look
    P(17, 8, c["eye_white"]); P(18, 8, c["eye_green"]); P(19, 8, c["eye_pupil"])
    P(22, 8, c["eye_white"]); P(23, 8, c["eye_green"]); P(24, 8, c["eye_pupil"])
    # Eyebrows (slight smug angle)
    P(17, 7, c["body_dark"]); P(18, 7, c["body_dark"])
    P(23, 7, c["body_dark"]); P(24, 7, c["body_dark"])

    # Nose + mouth
    P(24, 10, c["nose"]); P(25, 10, c["nose"])
    P(25, 11, c["mouth"])
    # Whiskers
    P(26, 9, c["whisker"]); P(27, 9, c["whisker"])
    P(26, 11, c["whisker"]); P(27, 11, c["whisker"])

    # Tongue on frame 2
    if phase == 2:
        P(25, 12, c["ear_inner"])

    # Legs — walk cycle
    offsets = [(0,1,-1,0), (1,0,0,-1), (0,-1,1,0), (-1,0,0,1)][phase]
    for dy in range(4):
        P(18, 22+dy+offsets[0], c["body_dark"])
        P(16, 22+dy+offsets[1], c["body"])
        P(11, 22+dy+offsets[2], c["body_dark"])
        P(13, 22+dy+offsets[3], c["body"])
    P(18, 25+offsets[0], c["paw"])
    P(16, 25+offsets[1], c["paw"])
    P(11, 25+offsets[2], c["paw"])
    P(13, 25+offsets[3], c["paw"])


def tom_idle(draw, f, d=1):
    c = TOM
    P = lambda x, y, col: px(draw, x, y, col, d)

    # Tail wagging
    wag = [-1, 0, 1, 0][f]
    P(6, 17+wag, c["body_dark"])
    P(5, 16+wag, c["body"])
    P(4, 15+wag, c["tail_tip"])

    # Sitting body
    for x in range(9, 22):
        for y in range(14, 25):
            P(x, y, c["body"])
    for x in range(12, 19):
        for y in range(20, 25):
            P(x, y, c["belly"])

    # Head
    for x in range(13, 26):
        for y in range(5, 15):
            P(x, y, c["body"])
    for x in range(15, 24):
        for y in range(8, 14):
            P(x, y, c["body_light"])
    for x in range(20, 26):
        for y in range(10, 14):
            P(x, y, c["belly"])

    # Ears
    P(14, 2, c["ear_outer"]); P(15, 2, c["ear_outer"])
    P(14, 3, c["ear_outer"]); P(15, 3, c["ear_inner"]); P(16, 3, c["ear_outer"])
    P(14, 4, c["ear_outer"]); P(15, 4, c["ear_inner"]); P(16, 4, c["body"])
    ear_tilt = -1 if f == 1 else 0
    P(22, 2+ear_tilt, c["ear_outer"]); P(23, 2+ear_tilt, c["ear_outer"])
    P(21, 3+ear_tilt, c["ear_outer"]); P(22, 3+ear_tilt, c["ear_inner"]); P(23, 3+ear_tilt, c["ear_outer"])
    P(21, 4+ear_tilt, c["body"]);      P(22, 4+ear_tilt, c["ear_inner"]); P(23, 4+ear_tilt, c["ear_outer"])

    # Eyes — blink on frame 3
    if f == 3:
        P(18, 9, c["body_dark"]); P(23, 9, c["body_dark"])
    else:
        P(17, 9, c["eye_white"]); P(18, 9, c["eye_green"]); P(19, 9, c["eye_pupil"])
        P(22, 9, c["eye_white"]); P(23, 9, c["eye_green"]); P(24, 9, c["eye_pupil"])
    P(17, 8, c["body_dark"]); P(18, 8, c["body_dark"])
    P(23, 8, c["body_dark"]); P(24, 8, c["body_dark"])

    P(24, 11, c["nose"]); P(25, 11, c["nose"])
    P(26, 10, c["whisker"]); P(27, 10, c["whisker"])
    P(26, 12, c["whisker"]); P(27, 12, c["whisker"])

    # Sitting legs
    for x in range(10, 14):
        P(x, 25, c["body_dark"]); P(x, 26, c["paw"])
    for x in range(16, 20):
        P(x, 25, c["body_dark"]); P(x, 26, c["paw"])


# ━━━ JERRY — Small brown mouse, big ears, cheerful ━━━━━━━━━━━━━━━━━━━━━━

JERRY = {
    "body":       (190, 130, 70, 255),    # warm brown
    "body_light": (220, 165, 100, 255),   # highlights
    "body_dark":  (150, 95, 45, 255),     # shadows
    "belly":      (240, 215, 170, 255),   # cream
    "ear_outer":  (180, 120, 65, 255),
    "ear_inner":  (225, 165, 155, 255),   # pink inner
    "eye":        (35, 30, 25, 255),      # big dark eyes
    "eye_shine":  (255, 255, 255, 255),   # sparkle
    "nose":       (210, 130, 130, 255),   # pink
    "whisker":    (200, 180, 160, 255),
    "paw":        (230, 195, 145, 255),
    "tail":       (195, 140, 90, 255),    # long thin tail
}


def jerry_walk(draw, phase, d=1):
    c = JERRY
    P = lambda x, y, col: px(draw, x, y, col, d)

    # Tail — long and curvy (behind body)
    tail_y = [0, -1, 0, 1][phase]
    P(7, 18+tail_y, c["tail"])
    P(6, 17+tail_y, c["tail"])
    P(5, 17+tail_y, c["tail"])
    P(4, 16+tail_y, c["tail"])
    P(3, 16+tail_y, c["body_dark"])

    # Body (smaller than Tom — Jerry is a mouse!)
    for x in range(11, 21):
        for y in range(16, 23):
            P(x, y, c["body"])
    for x in range(12, 20):
        P(x, 16, c["body_light"])
    for x in range(13, 19):
        for y in range(20, 23):
            P(x, y, c["belly"])

    # Head (round, big for a mouse)
    for x in range(16, 26):
        for y in range(10, 17):
            P(x, y, c["body"])
    for x in range(18, 24):
        for y in range(12, 16):
            P(x, y, c["body_light"])
    # Snout
    for x in range(24, 27):
        for y in range(13, 16):
            P(x, y, c["belly"])
    P(26, 14, c["nose"])

    # Big round ears (Jerry's signature!)
    # Left ear — big circle
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if abs(dx) + abs(dy) <= 1:
                P(16+dx, 7+dy, c["ear_outer"])
                P(16+dx, 7+dy, c["ear_outer"] if abs(dx)+abs(dy)==1 else c["ear_inner"])
    P(16, 7, c["ear_inner"])
    P(15, 7, c["ear_outer"]); P(17, 7, c["ear_outer"])
    P(16, 6, c["ear_outer"]); P(16, 8, c["ear_outer"])

    # Right ear
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if abs(dx) + abs(dy) <= 1:
                P(24+dx, 7+dy, c["ear_outer"])
    P(24, 7, c["ear_inner"])
    P(23, 7, c["ear_outer"]); P(25, 7, c["ear_outer"])
    P(24, 6, c["ear_outer"]); P(24, 8, c["ear_outer"])

    # Eyes — big and expressive (Jerry's charm)
    P(19, 12, c["eye"]); P(20, 12, c["eye"])
    P(20, 11, c["eye_shine"])
    P(23, 12, c["eye"]); P(24, 12, c["eye"])
    P(24, 11, c["eye_shine"])

    # Whiskers
    P(27, 13, c["whisker"]); P(28, 14, c["whisker"])

    # Happy mouth on frame 1
    if phase == 1:
        P(25, 15, c["body_dark"])

    # Legs — shorter than Tom's
    offsets = [(0,1,-1,0), (1,0,0,-1), (0,-1,1,0), (-1,0,0,1)][phase]
    for dy in range(3):
        P(18, 23+dy+offsets[0], c["body_dark"])
        P(16, 23+dy+offsets[1], c["body"])
        P(13, 23+dy+offsets[2], c["body_dark"])
        P(15, 23+dy+offsets[3], c["body"])
    P(18, 25+offsets[0], c["paw"])
    P(16, 25+offsets[1], c["paw"])
    P(13, 25+offsets[2], c["paw"])
    P(15, 25+offsets[3], c["paw"])


def jerry_idle(draw, f, d=1):
    c = JERRY
    P = lambda x, y, col: px(draw, x, y, col, d)

    # Tail curled
    wag = [-1, 0, 1, 0][f]
    P(7, 20+wag, c["tail"])
    P(6, 19+wag, c["tail"])
    P(5, 19+wag, c["tail"])
    P(4, 18+wag, c["body_dark"])

    # Sitting body
    for x in range(11, 21):
        for y in range(17, 25):
            P(x, y, c["body"])
    for x in range(13, 19):
        for y in range(22, 25):
            P(x, y, c["belly"])

    # Head
    for x in range(16, 26):
        for y in range(11, 18):
            P(x, y, c["body"])
    for x in range(18, 24):
        for y in range(13, 17):
            P(x, y, c["body_light"])
    for x in range(24, 27):
        for y in range(14, 17):
            P(x, y, c["belly"])
    P(26, 15, c["nose"])

    # Ears
    P(16, 8, c["ear_outer"]); P(15, 8, c["ear_outer"]); P(17, 8, c["ear_outer"])
    P(16, 7, c["ear_outer"]); P(16, 9, c["ear_outer"]); P(16, 8, c["ear_inner"])
    ear_bounce = -1 if f == 2 else 0
    P(24, 8+ear_bounce, c["ear_outer"]); P(23, 8+ear_bounce, c["ear_outer"]); P(25, 8+ear_bounce, c["ear_outer"])
    P(24, 7+ear_bounce, c["ear_outer"]); P(24, 9+ear_bounce, c["ear_outer"]); P(24, 8+ear_bounce, c["ear_inner"])

    # Eyes — blink on frame 3
    if f == 3:
        P(19, 13, c["body_dark"]); P(23, 13, c["body_dark"])
    else:
        P(19, 13, c["eye"]); P(20, 13, c["eye"]); P(20, 12, c["eye_shine"])
        P(23, 13, c["eye"]); P(24, 13, c["eye"]); P(24, 12, c["eye_shine"])

    P(27, 14, c["whisker"]); P(28, 15, c["whisker"])

    # Sitting legs
    for x in range(12, 15):
        P(x, 25, c["body_dark"]); P(x, 26, c["paw"])
    for x in range(17, 20):
        P(x, 25, c["body_dark"]); P(x, 26, c["paw"])


# ━━━ Generation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHARACTERS = {
    "tom":   {"walk": tom_walk, "idle": tom_idle},
    "jerry": {"walk": jerry_walk, "idle": jerry_idle},
}


def generate_character(name, funcs, sprite_dir):
    out = os.path.join(sprite_dir, name)
    os.makedirs(out, exist_ok=True)
    for d_val, d_name in [(1, "right"), (-1, "left")]:
        for i in range(4):
            img, draw = frame()
            funcs["walk"](draw, i, d_val)
            img.save(os.path.join(out, f"walk_{d_name}_{i}.png"))
        for i in range(4):
            img, draw = frame()
            funcs["idle"](draw, i, d_val)
            img.save(os.path.join(out, f"idle_{d_name}_{i}.png"))
    print(f"  ✓ {name}: 16 frames → sprites/{name}/")


def main():
    sprite_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprites")
    os.makedirs(sprite_dir, exist_ok=True)

    print("🎨 Generating Tom & Jerry sprites...\n")
    for name, funcs in CHARACTERS.items():
        generate_character(name, funcs, sprite_dir)

    print(f"\n✓ Done! Characters: {', '.join(CHARACTERS.keys())}")


if __name__ == "__main__":
    main()
