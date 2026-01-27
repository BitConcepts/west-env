@echo off
setlocal EnableDelayedExpansion

echo Bootstrapping west-env workspace (Windows)...
echo.

REM =====================================================
REM Guard: must NOT be run inside west-env repo
REM =====================================================
if exist pyproject.toml (
  echo ERROR: bootstrap.cmd must NOT be run inside the west-env repository.
  echo.
  echo Please do the following instead:
  echo   1. Create a new workspace directory
  echo   2. Run bootstrap.cmd from that directory
  echo.
  echo Example:
  echo   mkdir west-env-ws
  echo   cd west-env-ws
  echo   bootstrap.cmd
  exit /b 1
)

REM =====================================================
REM Paths
REM =====================================================
set "WORKSPACE_DIR=%CD%"
set "VENV_DIR=.venv"
set "MODULE_DIR=modules\west-env"
set "WEST_YML=west.yml"

REM =====================================================
REM Check Python
REM =====================================================
where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found in PATH
  exit /b 1
)

REM =====================================================
REM Create virtual environment
REM =====================================================
if not exist "%VENV_DIR%" (
  echo Creating virtual environment...
  python -m venv "%VENV_DIR%"
)

REM =====================================================
REM Activate venv
REM =====================================================
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
  echo ERROR: Failed to activate virtual environment
  exit /b 1
)

REM =====================================================
REM Install tooling
REM =====================================================
python -m pip install --upgrade pip
python -m pip install west

REM =====================================================
REM Create minimal west.yml if missing
REM =====================================================
if not exist "%WEST_YML%" (
  echo Creating west.yml...
  (
    echo manifest:
    echo   projects:
    echo     - name: west-env
    echo       path: modules/west-env
    echo       url: https://github.com/bitconcepts/west-env
    echo       revision: main
  ) > "%WEST_YML%"
)

REM =====================================================
REM Initialize west workspace
REM =====================================================
if not exist ".west" (
  echo Initializing west workspace...
  west init -l .
)

REM =====================================================
REM Update workspace (fetch west-env)
REM =====================================================
echo Updating workspace...
west update

echo.
echo Bootstrap complete.
echo.
echo Workspace location:
echo   %WORKSPACE_DIR%
echo.
echo Next steps:
echo   shell.cmd
echo   west env doctor
