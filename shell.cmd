@echo off
setlocal EnableDelayedExpansion

set "VENV_DIR=.venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
  echo Virtual environment not found.
  echo Run bootstrap.cmd first.
  exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"

REM ---- Extract Python version ----
for /f "tokens=2 delims= " %%P in ('python --version') do set PY_VER=%%P

REM ---- Extract west version ----
for /f "tokens=3 delims= " %%W in ('west --version') do set WEST_VER=%%W

echo.
echo west-env workspace shell activated.
echo.
echo Python: v%PY_VER%
echo West: v%WEST_VER%
echo.
echo You are now in the workspace root.
echo Type "exit" to leave.
echo.

cmd /k
