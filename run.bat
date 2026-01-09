@echo off
title Domain Monitor - Telegram Bot
cd /d "%~dp0"

echo =====================================
echo Starting Domain Monitor...
echo =====================================

python all_in_one_monitor.py

pause
