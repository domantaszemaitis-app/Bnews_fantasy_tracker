@echo off
cd /d %~dp0
py update.py || python update.py
py server.py || python server.py
pause
