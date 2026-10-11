@echo off
chcp 65001 >nul
title Build Emoji Tamagotchi EXE
echo ==========================================
echo   Building EmojiTamagotchi.exe
echo ==========================================
python --version >nul 2>&1
if errorlevel 1 (
  echo Python not found. Install it from python.org ^(tick "Add Python to PATH"^) and run again.
  pause
  exit /b 1
)
python -m pip install --upgrade pyinstaller
python -m pip install pygame
set PG=
python -c "import pygame" >nul 2>&1 && set PG=--collect-all pygame
python -m PyInstaller --onefile --console --clean --name EmojiTamagotchi %PG% tamagotchi.py
if errorlevel 1 (
  echo BUILD FAILED
  pause
  exit /b 1
)
if exist release rmdir /s /q release
mkdir release
copy /y dist\EmojiTamagotchi.exe release\ >nul
xcopy /e /i /y music release\music >nul
echo.
echo DONE!  Your game is in the "release" folder:
echo   release\EmojiTamagotchi.exe   ^(double-click to play^)
echo   release\music\                ^(put your music files here^)
pause
