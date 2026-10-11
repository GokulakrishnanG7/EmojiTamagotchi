#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMOJI TAMAGOTCHI  -  a console virtual pet survival game
=========================================================
Adopt an emoji pet and keep it alive, happy and healthy.
Every stat slowly declines. If ANY stat reaches 0, the game is over.

Run:   python tamagotchi.py        (or double-click EmojiTamagotchi.exe)
Music: drop .wav / .mp3 / .ogg files into the  music  folder next to this file.
Only the Python standard library is required (pygame is optional, for mp3/ogg).
"""

import json
import os
import random
import sys
import time

APP_NAME = "Emoji Tamagotchi"
TICKS_PER_DAY = 8          # one action = one tick = 3 in-game hours
IDLE_SECONDS = 20          # real seconds of waiting before extra time passes
MAX_IDLE_TICKS = 3


# --------------------------------------------------------------------------
#  Paths (work both as a script and as a PyInstaller .exe)
# --------------------------------------------------------------------------
def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE = base_dir()
MUSIC_DIR = os.path.join(BASE, "music")
SAVE_FILE = os.path.join(BASE, "tamagotchi_save.json")
FAST = os.environ.get("TAMA_FAST") == "1"      # skips animations (used for testing)


# --------------------------------------------------------------------------
#  Terminal helpers
# --------------------------------------------------------------------------
class C:
    R = "\033[0m"
    B = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GRN = "\033[92m"
    YEL = "\033[93m"
    BLU = "\033[94m"
    MAG = "\033[95m"
    CYN = "\033[96m"
    WHT = "\033[97m"


class QuitGame(Exception):
    pass


def setup_terminal():
    for stream in (sys.stdout, sys.stdin):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if os.name == "nt":
        os.system("")                       # enables ANSI colours in cmd / PowerShell
        try:
            os.system("title Emoji Tamagotchi")
        except Exception:
            pass


def clear():
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="")
    else:
        print("\n" * 2)


def pause(seconds):
    if not FAST:
        time.sleep(seconds)


def ask(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        raise QuitGame()


def animate(frames, delay=0.4):
    """Play a tiny one-line animation."""
    for frame in frames:
        print("\r\033[K  " + frame, end="", flush=True)
        pause(delay)
    print()


LINE = C.DIM + "  " + "━" * 46 + C.R


def banner():
    print(C.CYN + C.B)
    print("   ╔══════════════════════════════════════════╗")
    print("   ║" + C.YEL + "   🐣  E M O J I   T A M A G O T C H I  🐣" + C.CYN + "   ║")
    print("   ╚══════════════════════════════════════════╝" + C.R)


# --------------------------------------------------------------------------
#  Music
# --------------------------------------------------------------------------
class Music:
    EXT = (".mp3", ".ogg", ".wav")

    def __init__(self):
        self.backend = None
        self.pg = None
        self.winsound = None
        self.enabled = True
        self.index = 0
        self._init_backend()
        self.tracks = self._find_tracks()

    def _init_backend(self):
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        try:
            import pygame                                   # optional
            pygame.mixer.init()
            self.pg = pygame
            self.backend = "pygame"
            return
        except Exception:
            self.pg = None
        if os.name == "nt":
            try:
                import winsound
                self.winsound = winsound
                self.backend = "winsound"
            except Exception:
                self.backend = None

    def _find_tracks(self):
        try:
            files = sorted(f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(self.EXT))
        except OSError:
            files = []
        if self.backend == "winsound":                      # winsound only plays .wav
            files = [f for f in files if f.lower().endswith(".wav")]
        user_files = [f for f in files if not f.startswith("_")]
        chosen = user_files or files                        # "_default_theme.wav" is the fallback
        return [os.path.join(MUSIC_DIR, f) for f in chosen]

    @property
    def available(self):
        return self.backend is not None and bool(self.tracks)

    def start(self):
        if not (self.available and self.enabled):
            return
        path = self.tracks[self.index % len(self.tracks)]
        try:
            if self.backend == "pygame":
                self.pg.mixer.music.load(path)
                self.pg.mixer.music.set_volume(0.5)
                self.pg.mixer.music.play(-1)
            else:
                self.winsound.PlaySound(
                    path, self.winsound.SND_FILENAME | self.winsound.SND_ASYNC | self.winsound.SND_LOOP)
        except Exception:
            self.backend = None                             # give up quietly, game keeps running

    def stop(self):
        try:
            if self.backend == "pygame":
                self.pg.mixer.music.stop()
            elif self.backend == "winsound":
                self.winsound.PlaySound(None, self.winsound.SND_PURGE)
        except Exception:
            pass

    def toggle(self):
        if not self.available:
            return self.status_text()
        self.enabled = not self.enabled
        if self.enabled:
            self.start()
        else:
            self.stop()
        return self.status_text()

    def next_track(self):
        if not self.available:
            return self.status_text()
        self.index = (self.index + 1) % len(self.tracks)
        self.enabled = True
        self.stop()
        self.start()
        return self.status_text()

    def status_text(self):
        if self.backend is None:
            return "🔇 No audio backend (Windows: built in for .wav, others: pip install pygame)"
        if not self.tracks:
            return "🔇 No music files found in the 'music' folder"
        if not self.enabled:
            return "🔇 Music OFF"
        name = os.path.basename(self.tracks[self.index % len(self.tracks)])
        return "🎵 Music ON  ·  " + name


# --------------------------------------------------------------------------
#  Pet data
# --------------------------------------------------------------------------
SPECIES = {
    "1": {"name": "Puppy",  "emoji": "🐶", "cry": "Woof woof!"},
    "2": {"name": "Kitten", "emoji": "🐱", "cry": "Meow~"},
    "3": {"name": "Dragon", "emoji": "🐲", "cry": "Rawr!"},
    "4": {"name": "Bunny",  "emoji": "🐰", "cry": "*wiggles nose*"},
    "5": {"name": "Panda",  "emoji": "🐼", "cry": "*happy munching*"},
    "6": {"name": "Fox",    "emoji": "🦊", "cry": "Yip yip!"},
}

STATS = [
    ("hunger",  "🍖", "Fullness "),
    ("happy",   "💖", "Happiness"),
    ("energy",  "⚡", "Energy   "),
    ("hygiene", "🧼", "Hygiene  "),
    ("health",  "💚", "Health   "),
]
STAT_KEYS = [s[0] for s in STATS]
FOUR = ["hunger", "happy", "energy", "hygiene"]

DIFFICULTY = {"1": ("Easy", 0.7), "2": ("Normal", 1.0), "3": ("Hard", 1.35)}

DEATH_REASON = {
    "hunger":  "starved 🍽️",
    "happy":   "died of a broken heart 💔",
    "energy":  "collapsed from exhaustion 😴",
    "hygiene": "got far too dirty 🦠",
    "health":  "became too unwell 🏥",
}

REQUIRED_KEYS = set(STAT_KEYS) | {"name", "species", "diff", "ticks", "sick", "wins"}


def new_pet(name, species, diff):
    return {"name": name, "species": species, "diff": diff, "ticks": 0, "sick": False, "wins": 0,
            "hunger": 80, "happy": 80, "energy": 80, "hygiene": 80, "health": 100}


def clamp(v):
    return max(0, min(100, int(v)))


def change(p, **kw):
    for k, v in kw.items():
        p[k] = clamp(p[k] + v)


def stage_of(p):
    t = p["ticks"]
    if t < 8:
        return "Baby", "🍼"
    if t < 24:
        return "Child", "🎈"
    if t < 48:
        return "Teen", "🎧"
    return "Adult", "👑"


def mood(p):
    if p["sick"]:
        return "🤒", "feels sick... it needs medicine!"
    low = min(STAT_KEYS, key=lambda k: p[k])
    if p[low] < 25:
        return {
            "hunger":  ("😫", "is starving!"),
            "happy":   ("😢", "is really sad..."),
            "energy":  ("🥱", "is exhausted..."),
            "hygiene": ("🤢", "is filthy!"),
            "health":  ("😵", "looks very weak!"),
        }[low]
    avg = sum(p[k] for k in STAT_KEYS) / len(STAT_KEYS)
    if avg >= 80:
        return "🤩", "is thrilled!"
    if avg >= 60:
        return "😊", "is happy."
    if avg >= 40:
        return "😐", "is doing okay."
    return "🙁", "isn't feeling great."


def check_dead(p):
    """Return the stat key that hit zero, or None."""
    for k in STAT_KEYS:
        if p[k] <= 0:
            return k
    return None


def scaled(p, lo, hi):
    """Stat loss per turn: grows with difficulty and (slowly) with the pet's age."""
    mult = DIFFICULTY.get(p["diff"], ("Normal", 1.0))[1]
    mult *= min(2.0, 1 + p["ticks"] / 120)
    return max(1, round(random.randint(lo, hi) * mult))


def tick(p, n=1, sleeping=False):
    """Advance time. Returns a list of event messages."""
    out = []
    for _ in range(n):
        p["ticks"] += 1
        if sleeping:
            change(p, hunger=-scaled(p, 2, 3), happy=-random.randint(0, 2),
                   energy=random.randint(13, 17), hygiene=-random.randint(1, 2))
        else:
            change(p, hunger=-scaled(p, 4, 6), happy=-scaled(p, 3, 5),
                   energy=-scaled(p, 3, 5), hygiene=-scaled(p, 3, 4))

        if not p["sick"]:
            chance = 0.20 if p["hygiene"] < 35 else 0.02
            if random.random() < chance:
                p["sick"] = True
                out.append("🤒 Oh no! Your pet caught a bug. Give it medicine!")

        damage = 6 if p["sick"] else 0
        damage += 3 * sum(1 for k in FOUR if p[k] < 20)
        if damage:
            change(p, health=-damage)
        elif all(p[k] >= 50 for k in FOUR):
            change(p, health=2)

        if check_dead(p):
            break
    return out


RANDOM_EVENTS = [
    ("🐦 A little bird sang a song for your pet!  (+happiness)", {"happy": 6}),
    ("🦋 Your pet chased a butterfly!  (+happiness, -energy)", {"happy": 5, "energy": -3}),
    ("🍎 Your pet found a snack on the floor!  (+fullness)", {"hunger": 8}),
    ("🌧️ Splash! Your pet jumped in a puddle.  (+happiness, -hygiene)", {"happy": 4, "hygiene": -8}),
    ("🤧 Achoo! Your pet sneezed.  (-health)", {"health": -3}),
    ("🌈 A rainbow appeared!  (+happiness)", {"happy": 7}),
]


def random_event(p):
    if random.random() < 0.15:
        text, deltas = random.choice(RANDOM_EVENTS)
        change(p, **deltas)
        return [text]
    return []


# --------------------------------------------------------------------------
#  Saving / loading
# --------------------------------------------------------------------------
def load_data():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError
    except Exception:
        data = {}
    pet = data.get("pet")
    if not (isinstance(pet, dict) and REQUIRED_KEYS.issubset(pet.keys()) and pet["species"] in SPECIES):
        data["pet"] = None
    data.setdefault("best_ticks", 0)
    data.setdefault("best_name", "")
    return data


def save_data(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------
#  Drawing
# --------------------------------------------------------------------------
def bar(v, width=20):
    v = clamp(v)
    filled = round(v / 100 * width)
    color = C.GRN if v > 60 else C.YEL if v > 30 else C.RED
    return f"{color}{'█' * filled}{C.DIM}{'░' * (width - filled)}{C.R} {v:3d}"


def draw(p, notes, music):
    clear()
    sp = SPECIES[p["species"]]
    stage, decor = stage_of(p)
    abs_hours = 8 + p["ticks"] * 3
    hour, day = abs_hours % 24, 1 + abs_hours // 24
    night = hour >= 21 or hour < 6
    sky = "🌙  ✨   ⭐   ✨  🌙" if night else "🌞   ☁️    ☁️    🌤️"
    face, mood_text = mood(p)
    diff_name = DIFFICULTY.get(p["diff"], ("Normal", 1.0))[0]

    banner()
    print(f"\n  {C.B}{sp['emoji']} {p['name']}{C.R} the {sp['name']}  ·  {stage} {decor}  ·  {C.DIM}{diff_name}{C.R}")
    print(f"  {C.DIM}Day {day}  ·  {hour:02d}:00  ·  Survived {p['ticks'] / TICKS_PER_DAY:.1f} days{C.R}")
    print(LINE)
    print(f"\n      {sky}\n")
    pad = " " * random.choice([6, 9, 12, 15])
    zzz = " 💤" if (p["energy"] < 40 and night) else ""
    print(f"{pad}{sp['emoji']}{decor}  {face}{zzz}\n")
    if face in ("🤩", "😊"):
        print(f"{pad}{C.CYN}💬 \"{sp['cry']}\"{C.R}")
    else:
        print(f"{pad}{C.YEL}💬 {p['name']} {mood_text}{C.R}")
    print()
    print(LINE)
    for key, emoji, label in STATS:
        warn = f"  {C.RED}{C.B}⚠️ LOW!{C.R}" if p[key] < 25 else ""
        print(f"  {emoji} {label} {bar(p[key])}{warn}")
    if p["sick"]:
        print(f"  {C.RED}{C.B}🤒 SICK — health is dropping every turn!{C.R}")
    print(LINE)
    for n in notes:
        print(f"  {n}")
    if notes:
        print(LINE)
    print(f"  {C.B}[1]{C.R} 🍖 Feed    {C.B}[2]{C.R} 🎾 Play     {C.B}[3]{C.R} 😴 Sleep")
    print(f"  {C.B}[4]{C.R} 🛁 Clean   {C.B}[5]{C.R} 💊 Medicine {C.B}[6]{C.R} 🤗 Cuddle")
    print(f"  {C.B}[M]{C.R} 🎵 Music   {C.B}[N]{C.R} ⏭️  Track    {C.B}[H]{C.R} ❓ Help")
    print(f"  {C.B}[S]{C.R} 💾 Save    {C.B}[Q]{C.R} 🚪 Save & Quit")
    print(f"  {C.DIM}{music.status_text()}{C.R}")
    print(LINE)


def show_help():
    clear()
    banner()
    print(f"""
  {C.B}HOW TO PLAY{C.R}
  Your pet has 5 stats. Every action you take lets time pass
  (3 in-game hours), and the stats slowly drop. If {C.RED}ANY stat hits 0{C.R},
  your pet is gone. Waiting too long at the menu also lets time pass!

  🍖 {C.B}Feed{C.R}      Meal, snack or treat. Don't feed a full pet (tummy ache!).
  🎾 {C.B}Play{C.R}      Fetch, guess-the-number or rock-paper-scissors.
              Fun, but it costs energy and makes your pet dirty.
  😴 {C.B}Sleep{C.R}     Restores lots of energy (takes 3 turns). Not when wide awake.
  🛁 {C.B}Clean{C.R}     Raises hygiene. A dirty pet gets sick more easily.
  💊 {C.B}Medicine{C.R}  Cures sickness. Don't give it to a healthy pet!
  🤗 {C.B}Cuddle{C.R}    A cheap, quick way to boost happiness.

  💚 {C.B}Health{C.R} falls when the pet is sick or when other stats are very low,
  and recovers slowly when everything is going well.

  🎵 Put your own music in the {C.B}music{C.R} folder (.wav, .mp3, .ogg).
""")
    ask("  Press Enter to go back ▶ ")


# --------------------------------------------------------------------------
#  Actions  (each returns (messages, ticks_to_pass, sleeping) or None)
# --------------------------------------------------------------------------
def act_feed(p):
    e = SPECIES[p["species"]]["emoji"]
    print(f"\n  {C.B}What should {p['name']} eat?{C.R}")
    print("   1) 🍲 Meal   (+30 fullness)")
    print("   2) 🍪 Snack  (+15 fullness, +6 happiness)")
    print("   3) 🍰 Treat  (+10 fullness, +18 happiness, slightly unhealthy)")
    print("   0) Back")
    c = ask("  ▶ ")
    if c not in ("1", "2", "3"):
        return None
    food = {"1": "🍲", "2": "🍪", "3": "🍰"}[c]
    animate([f"{e} {food}", f"{e}  {food}", f"{e}😋", f"{e}😋 nom nom!"], 0.4)
    if p["hunger"] >= 90:
        change(p, health=-8, happy=-6)
        return ([f"🤢 {p['name']} was already full and got a tummy ache!  (-health, -happiness)"], 1, False)
    if c == "1":
        change(p, hunger=30, happy=2)
        msg = f"🍲 {p['name']} ate a hearty meal.  (+fullness)"
    elif c == "2":
        change(p, hunger=15, happy=6)
        msg = f"🍪 Crunch! {p['name']} loved the snack.  (+fullness, +happiness)"
    else:
        change(p, hunger=10, happy=18, hygiene=-4, health=-2)
        msg = f"🍰 Sugar rush! {p['name']} is delighted but sticky.  (+happiness, -hygiene, -health)"
    return ([msg], 1, False)


def minigame_guess(p):
    secret = random.randint(1, 5)
    print(f"\n  🎲 {C.B}Guess the number!{C.R} {p['name']} is thinking of a number from 1 to 5. You have 2 tries.")
    for attempt in (1, 2):
        while True:
            g = ask(f"  Try {attempt}/2 ▶ ")
            if g.isdigit() and 1 <= int(g) <= 5:
                g = int(g)
                break
            print("  Please type a number between 1 and 5.")
        if g == secret:
            animate([f"{SPECIES[p['species']]['emoji']}🎉 Correct!"], 0.5)
            return True
        if attempt == 1:
            print(f"  {'⬆️  Higher!' if g < secret else '⬇️  Lower!'}")
    print(f"  😅 It was {secret}!")
    return False


def minigame_rps(p):
    names = {"r": "✊ rock", "p": "✋ paper", "s": "✌️  scissors"}
    beats = {"r": "s", "s": "p", "p": "r"}
    wins = losses = 0
    print(f"\n  ✊✋✌️  {C.B}Rock - Paper - Scissors{C.R}  (best of 3 rounds)")
    for rnd in (1, 2, 3):
        while True:
            m = ask(f"  Round {rnd}/3  [r]ock [p]aper [s]cissors ▶ ").lower()
            if m in beats:
                break
            print("  Please type r, p or s.")
        pet_move = random.choice(list(beats))
        print(f"  You: {names[m]}   vs   {p['name']}: {names[pet_move]}")
        if m == pet_move:
            print("  🤝 Draw!")
        elif beats[m] == pet_move:
            wins += 1
            print("  ✅ You win this round!")
        else:
            losses += 1
            print("  ❌ Your pet wins this round!")
    return wins > losses


def act_play(p):
    e = SPECIES[p["species"]]["emoji"]
    if p["energy"] < 15:
        return ([f"😴 {p['name']} is too tired to play. Let it sleep!"], 0, False)
    print(f"\n  {C.B}What should you play?{C.R}")
    print("   1) 🎾 Fetch")
    print("   2) 🎲 Guess the number (mini-game)")
    print("   3) ✊ Rock-Paper-Scissors (mini-game)")
    print("   0) Back")
    c = ask("  ▶ ")
    if c == "1":
        animate([f"{e}   🎾", f"{e}  🎾", f"{e} 🎾", f"🎾{e}", f"{e}🎉 Got it!"], 0.35)
        change(p, happy=20, energy=-12, hygiene=-5, hunger=-5)
        return ([f"🎾 What a game of fetch!  (+happiness, -energy, -hygiene, -fullness)"], 1, False)
    if c in ("2", "3"):
        won = minigame_guess(p) if c == "2" else minigame_rps(p)
        change(p, energy=-8, hunger=-3)
        if won:
            p["wins"] += 1
            change(p, happy=30)
            return ([f"🏆 You won! {p['name']} is overjoyed!  (+30 happiness)"], 1, False)
        change(p, happy=12)
        return ([f"🎈 Good game! {p['name']} had fun anyway.  (+12 happiness)"], 1, False)
    return None


def act_sleep(p):
    e = SPECIES[p["species"]]["emoji"]
    if p["energy"] >= 90:
        return ([f"👀 {p['name']} isn't sleepy at all! Try playing instead."], 0, False)
    animate([f"{e} 🌙", f"{e}😪 🌙", f"{e}😴 💤", f"{e}😴 💤💤", f"{e}😴 💤💤💤"], 0.5)
    animate([f"{e}😊 ☀️ Good morning!"], 0.5)
    return ([f"😴 {p['name']} had a long nap.  (+energy, slightly hungrier)"], 3, True)


def act_clean(p):
    e = SPECIES[p["species"]]["emoji"]
    animate([f"{e} 🚿", f"{e}💦", f"🛁{e}🧼🧼", f"🛁{e}🫧🫧🫧", f"✨{e}✨ squeaky clean!"], 0.4)
    change(p, hygiene=45, happy=-3)
    return ([f"🛁 Splish splash! {p['name']} is sparkling clean.  (+hygiene, -happiness)"], 1, False)


def act_medicine(p):
    e = SPECIES[p["species"]]["emoji"]
    animate([f"{e} 💊", f"{e}😖 gulp...", f"{e}😌"], 0.5)
    if p["sick"]:
        p["sick"] = False
        change(p, health=20, happy=-4)
        return ([f"💊 {p['name']} is cured and feeling better!  (+health)"], 1, False)
    change(p, health=-8, happy=-6)
    return ([f"🤮 {p['name']} wasn't sick! Medicine tasted awful.  (-health, -happiness)"], 1, False)


def act_cuddle(p):
    e = SPECIES[p["species"]]["emoji"]
    animate([f"{e}", f"{e}💕", f"{e}💕💕", f"🤗{e}💕💕💕"], 0.35)
    change(p, happy=12, hygiene=-1)
    line = random.choice([
        f"{p['name']} snuggles up to you.",
        f"{p['name']} purrs, wags, or wiggles — whatever it does, it's happy!",
        f"{p['name']} gives you the biggest hug.",
    ])
    return ([f"🤗 {line}  (+happiness)"], 1, False)


ACTIONS = {"1": act_feed, "2": act_play, "3": act_sleep, "4": act_clean, "5": act_medicine, "6": act_cuddle}


# --------------------------------------------------------------------------
#  Screens
# --------------------------------------------------------------------------
def title_screen():
    clear()
    banner()
    print(f"""
          🥚  →  🐣  →  🐶  →  🐲

    Adopt an emoji pet and keep it alive!
    Feed it, play with it, keep it clean, let it sleep.
    {C.RED}If any of its stats drops to zero... it's game over.{C.R}
""")
    ask("  Press Enter to start ▶ ")


def create_pet():
    clear()
    banner()
    print(f"\n  {C.B}Choose your pet:{C.R}\n")
    for k, s in SPECIES.items():
        print(f"   {k}) {s['emoji']}  {s['name']}")
    while True:
        c = ask("\n  Your choice (1-6) ▶ ")
        if c in SPECIES:
            break
        print("  Please type a number from 1 to 6.")
    sp = SPECIES[c]
    name = ask(f"\n  Name your {sp['name']} (Enter for \"{sp['name']}\") ▶ ")
    name = (name[:12] or sp["name"]).strip() or sp["name"]
    print(f"\n  {C.B}Difficulty:{C.R}  1) 😌 Easy   2) 🙂 Normal   3) 😈 Hard")
    while True:
        d = ask("  Your choice (1-3, Enter = Normal) ▶ ") or "2"
        if d in DIFFICULTY:
            break
        print("  Please type 1, 2 or 3.")
    print()
    animate(["🥚", "🥚 ·", "🥚 ··", " 🥚 ", "🥚💥", "🐣", f"🐣✨", f"{sp['emoji']}🎉 {name} was born!"], 0.45)
    pause(0.8)
    return new_pet(name, c, d)


def game_over_screen(p, reason_key, data, new_best):
    sp = SPECIES[p["species"]]
    days = p["ticks"] / TICKS_PER_DAY
    clear()
    print(C.RED + C.B)
    print("   ╔══════════════════════════════════════════╗")
    print("   ║               G A M E   O V E R          ║")
    print("   ╚══════════════════════════════════════════╝" + C.R)
    print(f"""
                    🪦
               R . I . P .
               {sp['emoji']}  {C.B}{p['name']}{C.R}

     {p['name']} {DEATH_REASON[reason_key]}.

     📅 Survived:      {days:.1f} days  ({p['ticks']} turns)
     🏆 Mini-game wins: {p['wins']}
     🥇 Best survival:  {data['best_ticks'] / TICKS_PER_DAY:.1f} days  ({data['best_name'] or '-'})""")
    if new_best:
        print(f"\n     {C.YEL}{C.B}⭐ NEW RECORD! ⭐{C.R}")
    print()


def game_loop(p, data, music):
    notes = [f"👋 Hello! Take good care of {p['name']}. Type H for help."]
    while True:
        draw(p, notes, music)
        t0 = time.time()
        choice = ask("  Your choice ▶ ").lower()
        elapsed = time.time() - t0
        notes = []

        # Time keeps ticking while you hesitate
        if not FAST:
            idle = min(MAX_IDLE_TICKS, int(elapsed // IDLE_SECONDS))
            if idle > 0:
                notes.append(f"⏰ You took a while... {idle * 3} hours passed.")
                notes += tick(p, idle)
                dead = check_dead(p)
                if dead:
                    return dead

        if choice in ACTIONS:
            result = ACTIONS[choice](p)
            if result is None:
                notes.append("↩️  Cancelled.")
                continue
            msgs, ticks, sleeping = result
            notes += msgs
            if ticks:
                notes += tick(p, ticks, sleeping)
                notes += random_event(p) if not check_dead(p) else []
        elif choice == "m":
            notes.append(music.toggle())
        elif choice == "n":
            notes.append(music.next_track())
        elif choice == "h":
            show_help()
        elif choice == "s":
            data["pet"] = p
            notes.append("💾 Game saved!" if save_data(data) else "⚠️ Could not save here (folder is read-only).")
        elif choice == "q":
            data["pet"] = p
            save_data(data)
            return "quit"
        else:
            notes.append("🤔 Please choose one of the options shown.")
            continue

        dead = check_dead(p)
        if dead:
            return dead


def main():
    setup_terminal()
    data = load_data()
    music = Music()
    try:
        title_screen()
        music.start()
        p = None
        if data["pet"]:
            sv = data["pet"]
            print(f"\n  💾 Saved pet found: {SPECIES[sv['species']]['emoji']} {sv['name']}")
            c = ask("  [1] Continue   [2] New game ▶ ")
            if c != "2":
                p = sv
        while True:
            if p is None:
                p = create_pet()
            result = game_loop(p, data, music)
            if result == "quit":
                clear()
                print(f"\n  👋 See you soon! {p['name']} will be waiting for you.\n")
                break
            # the pet died
            new_best = p["ticks"] > data["best_ticks"]
            if new_best:
                data["best_ticks"], data["best_name"] = p["ticks"], p["name"]
            data["pet"] = None
            save_data(data)
            game_over_screen(p, result, data, new_best)
            again = ask("  Adopt a new pet? [Y/N] ▶ ").lower()
            if again not in ("y", "yes"):
                print("\n  Thanks for playing! 🐾\n")
                break
            p = None
    except (QuitGame, KeyboardInterrupt):
        if "p" in locals() and p is not None and check_dead(p) is None:
            data["pet"] = p
            save_data(data)
        print("\n\n  👋 Goodbye! Your progress was saved.\n")
    finally:
        music.stop()


if __name__ == "__main__":
    main()
