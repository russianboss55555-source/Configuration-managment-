@echo off
setlocal
cd /d "%~dp0.."
set "DEMO_PATH=/my documents"
call run.bat --vfs "examples/generated/multiple.zip" --script "examples/startup/config.txt" %*
exit /b %errorlevel%
