@echo off
setlocal
cd /d "%~dp0.."
set "DEMO_PATH=/my documents"
call run.bat --vfs "examples/generated/minimal.zip" --script "examples/startup/config.txt" %*
exit /b %errorlevel%
