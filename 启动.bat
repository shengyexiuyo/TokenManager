@echo off
chcp 65001 >nul
title Token Manager
cd /d "%~dp0"
start http://localhost:5000
python server.py
