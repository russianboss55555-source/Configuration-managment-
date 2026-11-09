@echo off
setlocal
cd /d "%~dp0.."
set "DEMO_PATH=/"
python -m examples.make_vfs nested
if errorlevel 1 exit /b %errorlevel%
call run.bat --vfs "examples/generated/nested.zip" --script "examples/startup/stage3.txt" %*
exit /b %errorlevel%
