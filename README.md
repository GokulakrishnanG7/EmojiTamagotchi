# 🐣 Emoji Tamagotchi

A console survival game: adopt an emoji pet and keep **all 5 stats** above zero.
If any stat reaches 0, the game is over.

## ▶ Which file to run
| How | File |
|---|---|
| Python | `tamagotchi.py` (double-click `run_game.bat` on Windows, or `python tamagotchi.py`) |
| Windows exe | `EmojiTamagotchi.exe` (made by `build_exe.bat`, see below) |

Tip: use **Windows Terminal** (or any modern terminal) for the best emoji display.

## 🎵 Where to add music
Put your `.wav`, `.mp3` or `.ogg` file in the **`music/`** folder.
`.wav` works on Windows with no install. For `.mp3`/`.ogg`: `pip install pygame`.
In-game: `M` toggles music, `N` switches track. With the exe, keep `music/` next to it.

## 📦 Building the .exe (Windows)
Double-click **`build_exe.bat`**. It installs PyInstaller and creates
`release\EmojiTamagotchi.exe` plus `release\music\`.

## 🎮 Gameplay
Stats: 🍖 Fullness · 💖 Happiness · ⚡ Energy · 🧼 Hygiene · 💚 Health
Actions: Feed · Play (fetch + 2 mini-games) · Sleep · Clean · Medicine · Cuddle
Extras: 6 species, 3 difficulties (pets need more care as they age), day/night, growth stages, random events,
sickness, save/continue, best-survival record.

## 📁 Files
- `tamagotchi.py` the whole game (standard library only)
- `music/` your music + built-in chiptune theme
- `tools/generate_default_music.py` regenerates the default theme
- `build_exe.bat`, `run_game.bat`, `run_game.sh`
