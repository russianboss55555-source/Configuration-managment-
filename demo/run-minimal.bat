@echo off
setlocal
cd /d "%~dp0.."
set "DEMO_PATH=/"
python -m examples.make_vfs minimal
if errorlevel 1 exit /b %errorlevel%
call run.bat --vfs "examples/generated/minimal.zip" --script "examples/startup/stage3.txt" %*
exit /b %errorlevel%
