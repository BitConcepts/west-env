@echo off
setlocal EnableDelayedExpansion

REM =====================================================
REM Resolve script directory and workspace root
REM =====================================================
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

for %%I in ("%SCRIPT_DIR%\..") do set "WORKSPACE_DIR=%%~fI"

REM =====================================================
REM Guards
REM =====================================================
if exist "%WORKSPACE_DIR%\.git" (
  echo ERROR: Workspace must not be inside a git repository.
  exit /b 1
)

REM If someone copied scripts into the repo by mistake, refuse.
if exist "%WORKSPACE_DIR%\pyproject.toml" (
  echo ERROR: bootstrap.cmd must NOT be run inside the west-env repository.
  echo Create a separate workspace directory and run bootstrap there.
  exit /b 1
)

if not exist "%WORKSPACE_DIR%\west.yml" (
  echo ERROR: west.yml not found in workspace root:
  echo   %WORKSPACE_DIR%
  exit /b 1
)

echo Bootstrapping west-env workspace:
echo   %WORKSPACE_DIR%
echo.

REM =====================================================
REM Python + venv (ABSOLUTE)
REM =====================================================
set "VENV_DIR=%WORKSPACE_DIR%\.venv"

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found in PATH
  exit /b 1
)

if not exist "%VENV_DIR%" (
  echo Creating virtual environment...
  python -m venv "%VENV_DIR%"
  if errorlevel 1 exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
  echo ERROR: Failed to activate virtual environment
  exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

python -m pip install west
if errorlevel 1 exit /b 1

REM =====================================================
REM Initialize west workspace (DOC-CORRECT)
REM =====================================================
if not exist "%WORKSPACE_DIR%\.west" (
  echo Initializing west workspace...
  pushd "%WORKSPACE_DIR%"
  python -m west init
  if errorlevel 1 (
    echo ERROR: west init failed
    popd
    exit /b 1
  )
  popd
)
exit /b 1

REM =====================================================
REM Update workspace (run from workspace root)
REM =====================================================
echo Updating workspace...
pushd "%WORKSPACE_DIR%"
python -m west update
if errorlevel 1 (
  echo ERROR: west update failed
  popd
  exit /b 1
)
popd

echo.
echo Bootstrap complete.
echo.
echo Workspace location:
echo   %WORKSPACE_DIR%
echo.
echo Next steps:
echo   scripts\shell.cmd
echo   west env doctor
