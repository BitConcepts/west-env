@echo off
setlocal EnableDelayedExpansion

REM =====================================================
REM Resolve script directory (…\scripts)
REM =====================================================
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Workspace root is parent of script directory
for %%I in ("%SCRIPT_DIR%\..") do set "WORKSPACE_DIR=%%~fI"

REM =====================================================
REM Enforce execution from workspace root
REM =====================================================
if /I not "%CD%"=="%WORKSPACE_DIR%" (
  echo ERROR: bootstrap.cmd must be run from the workspace root.
  echo.
  echo Workspace root:
  echo   %WORKSPACE_DIR%
  echo Current directory:
  echo   %CD%
  echo.
  echo Please run:
  echo   cd %WORKSPACE_DIR%
  echo   scripts\bootstrap.cmd
  exit /b 1
)

REM =====================================================
REM Guard: must NOT be inside a git repository (copy-only)
REM =====================================================
if exist "%WORKSPACE_DIR%\.git" (
  echo ERROR: This workspace appears to be inside a git repository.
  echo.
  echo The example workspace is COPY-ONLY and must be used from
  echo a separate directory outside the west-env repository.
  echo.
  echo Correct usage:
  echo   1. Create a new directory outside the repo
  echo   2. Copy example\workspace\* into it
  echo   3. Run scripts\bootstrap.cmd from there
  exit /b 1
)

REM =====================================================
REM Guard: must NOT be run inside west-env repo
REM =====================================================
if exist pyproject.toml (
  echo ERROR: bootstrap.cmd must NOT be run inside the west-env repository.
  echo.
  echo Create a separate workspace directory and run bootstrap there.
  exit /b 1
)

REM =====================================================
REM Validate west.yml presence
REM =====================================================
if not exist "%WORKSPACE_DIR%\west.yml" (
  echo ERROR: west.yml not found in workspace root.
  echo.
  echo This workspace must be created by copying
  echo example\workspace\* into a new directory.
  exit /b 1
)

echo Bootstrapping west-env workspace...
echo.

REM =====================================================
REM Paths
REM =====================================================
set "VENV_DIR=.venv"
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
REM Initialize west workspace
REM =====================================================
if not exist "%WORKSPACE_DIR%\.west" (
  echo Initializing west workspace...
  west init -l .
  if errorlevel 1 (
    echo ERROR: west init failed
    exit /b 1
  )
)

REM =====================================================
REM Update workspace
REM =====================================================
echo Updating workspace...
west update
if errorlevel 1 (
  echo ERROR: west update failed
  exit /b 1
)

echo.
echo Bootstrap complete.
echo.
echo Workspace location:
echo   %WORKSPACE_DIR%
echo.
echo Next steps:
echo   scripts\shell.cmd
echo   west env doctor
