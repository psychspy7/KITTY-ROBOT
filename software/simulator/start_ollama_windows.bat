@echo off
cd /d "%~dp0"
set "ROBOT_LLM_PROVIDER=ollama"
set "ROBOT_OLLAMA_MODEL=qwen2.5:1.5b"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 main.py
) else (
    python main.py
)
pause
