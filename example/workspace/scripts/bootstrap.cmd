@echo off
REM SPDX-License-Identifier: Apache-2.0
setlocal enabledelayedexpansion

REM =====================================================
REM Configuration
REM =====================================================
set PYTHON_MIN_MINOR=10
set PYTHON_MAX_MINOR=12

REM =====================================================
REM Resolve script directory and workspace root
REM =====================================================
set SCRIPT_DIR=%~dp0
set WORKSPACE_DIR=%SCRIPT_DIR%\..

for %%I in ("%WORKSPACE_DIR%") do set WORKSPACE_DIR=%%~fI

REM =====================================================
REM Hard guards
REM =====================================================
if not exist "%WORKSPACE_DIR%\west.yml" (
  echo ERROR: west.yml not found in workspace root.
  echo Expected: %WORKSPACE_DIR%\west.yml
  exit /b 1
)

if exist "%WORKSPACE_DIR%\.git" (
  echo ERROR: Workspace must not be inside a git repository.
  exit /b 1
)

if exist "%WORKSPACE_DIR%\pyproject.toml" (
  echo ERROR: bootstrap.cmd must NOT be run inside the west-env repository.
  exit /b 1
)

REM =====================================================
REM Python availability
REM =====================================================
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: python not found in PATH
  exit /b 1
)

REM =====================================================
REM Python version check (Zephyr requirement)
REM =====================================================
for /f "tokens=2 delims= " %%V in ('python --version') do set PYVER=%%V
for /f "tokens=1,2 delims=." %%A in ("%PYVER%") do (
  set PYMAJOR=%%A
  set PYMINOR=%%B
)

if not "%PYMAJOR%"=="3" (
  echo ERROR: Unsupported Python version %PYVER%
  echo Zephyr requires Python 3.%PYTHON_MIN_MINOR%-3.%PYTHON_MAX_MINOR%
  exit /b 1
)

if %PYMINOR% LSS %PYTHON_MIN_MINOR% (
  echo ERROR: Unsupported Python version %PYVER%
  echo Zephyr requires Python 3.%PYTHON_MIN_MINOR%-3.%PYTHON_MAX_MINOR%
  exit /b 1
)

if %PYMINOR% GTR %PYTHON_MAX_MINOR% (
  echo ERROR: Unsupported Python version %PYVER%
  echo Zephyr requires Python 3.%PYTHON_MIN_MINOR%-3.%PYTHON_MAX_MINOR%
  echo Python 3.%PYTHON_MAX_MINOR%+ is not yet supported
  exit /b 1
)

echo.
echo === Bootstrapping west-env workspace ===
echo Workspace root:
echo   %WORKSPACE_DIR%
echo Python version:
echo   %PYVER%
echo.

REM =====================================================
REM Virtual environment
REM =====================================================
set VENV_DIR=%WORKSPACE_DIR%\.venv

if not exist "%VENV_DIR%" (
  echo Creating virtual environment...
  python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"

python -m pip install --upgrade pip
if errorlevel 1 (
  echo ERROR: Failed to upgrade pip
  exit /b 1
)

python -m pip install west
if errorlevel 1 (
  echo ERROR: Failed to install west
  exit /b 1
)

REM =====================================================
REM WEST OPERATIONS (forced CWD)
REM =====================================================
cd /d "%WORKSPACE_DIR%"

if not exist ".west" (
  echo Initializing west workspace...
  python -m west init -l .
  if errorlevel 1 (
    echo ERROR: west init failed
    exit /b 1
  )
)

echo Updating workspace...
python -m west update
if errorlevel 1 (
  echo ERROR: west update failed
  exit /b 1
)

python -m west list west-env >nul 2>nul
if errorlevel 1 (
  echo ERROR: west-env project not found.
  echo The active manifest is not west.yml.
  exit /b 1
)

REM =====================================================
REM Install Zephyr Python dependencies
REM =====================================================
set ZEPHYR_REQS=%WORKSPACE_DIR%\..\zephyr\scripts\requirements.txt

if not exist "%ZEPHYR_REQS%" (
  echo ERROR: Zephyr requirements file not found:
  echo   %ZEPHYR_REQS%
  exit /b 1
)

echo.
echo Installing Zephyr Python dependencies...
pip install -r "%ZEPHYR_REQS%"
if errorlevel 1 (
  echo ERROR: Failed to install Zephyr Python dependencies
  exit /b 1
)

REM =====================================================
REM Done
REM =====================================================
echo.
echo === Bootstrap complete ===
echo Workspace:
echo   %WORKSPACE_DIR%
echo.
echo Next steps:
echo   scripts\shell.cmd
echo   west env doctor
