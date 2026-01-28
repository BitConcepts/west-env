@echo off
setlocal

REM =====================================================
REM Resolve script directory and workspace root
REM =====================================================
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
for %%I in ("%SCRIPT_DIR%\..") do set "WORKSPACE_DIR=%%~fI"

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

echo.
echo === Bootstrapping west-env workspace ===
echo Workspace root:
echo   %WORKSPACE_DIR%
echo.

REM =====================================================
REM Python + venv
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
if errorlevel 1 exit /b 1

python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

python -m pip install west
if errorlevel 1 exit /b 1

REM =====================================================
REM WEST OPERATIONS (FORCED CWD)
REM =====================================================
pushd "%WORKSPACE_DIR%"
if errorlevel 1 exit /b 1

echo DEBUG: west CWD is %CD%

if not exist ".west" (
  echo Initializing west workspace...
  python -m west init -l .
  if errorlevel 1 (
    echo ERROR: west init failed
    popd
    exit /b 1
  )
)

echo Updating workspace...
python -m west update
if errorlevel 1 (
  echo ERROR: west update failed
  popd
  exit /b 1
)

python -m west list west-env >nul 2>&1
if errorlevel 1 (
  echo ERROR: west-env project not found.
  echo The active manifest is not west.yml.
  popd
  exit /b 1
)

popd

echo.
echo === Bootstrap complete ===
echo Workspace:
echo   %WORKSPACE_DIR%
echo.
echo Next steps:
echo   scripts\shell.cmd
echo   west env doctor
