@echo off
chcp 65001 >nul
title Emoji Tamagotchi
python tamagotchi.py
if errorlevel 1 (
  echo.
  echo Python was not found. Install it from python.org ^(tick "Add Python to PATH"^),
  echo or just double-click EmojiTamagotchi.exe instead.
)
pause
