@echo off
setlocal EnableDelayedExpansion

REM =====================================================
REM Resolve script directory and workspace root
REM =====================================================
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Workspace root is parent of script directory
for %%I in ("%SCRIPT_DIR%\..") do set "WORKSPACE_DIR=%%~fI"

REM =====================================================
REM Enforce execution from workspace root
REM =====================================================
if /I not "%CD%"=="%WORKSPACE_DIR%" (
  echo ERROR: shell.cmd must be run from the workspace root.
  echo.
  echo Workspace root:
  echo   %WORKSPACE_DIR%
  echo Current directory:
  echo   %CD%
  echo.
  echo Please run:
  echo   cd %WORKSPACE_DIR%
  echo   scripts\shell.cmd
  exit /b 1
)

REM =====================================================
REM Enter workspace explicitly
REM =====================================================
pushd "%WORKSPACE_DIR%"

REM =====================================================
REM Virtual environment
REM =====================================================
set "VENV_DIR=.venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
  echo Virtual environment not found.
  echo Run scripts\bootstrap.cmd first.
  popd
  exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
  echo ERROR: Failed to activate virtual environment
  popd
  exit /b 1
)

REM =====================================================
REM Extract versions
REM =====================================================

REM Python version (e.g. 3.10.12)
for /f "tokens=2 delims= " %%P in ('python --version') do set "PY_VER=%%P"

REM West version (e.g. v1.5.0)
for /f "tokens=3 delims= " %%W in ('west --version') do set "WEST_VER=%%W"

REM =====================================================
REM Banner
REM =====================================================
echo.
echo west-env workspace shell activated.
echo.
echo Python: v%PY_VER%
echo West:   %WEST_VER%
echo.
echo You are now in the workspace root.
echo Type "exit" to leave.
echo.

REM =====================================================
REM Enter interactive shell (stay in workspace)
REM =====================================================
cmd /k

REM =====================================================
REM Cleanup on exit
REM =====================================================
popd
