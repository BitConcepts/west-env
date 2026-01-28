@echo off
REM SPDX-License-Identifier: Apache-2.0
setlocal EnableExtensions EnableDelayedExpansion

REM --------------------------------------------------
REM Load env file
REM --------------------------------------------------
set ENV_FILE=.env

if not exist "%ENV_FILE%" (
  echo [ERROR] Env file not found: %ENV_FILE%
  echo [HINT ] Copy .env.example.win to .env
  exit /b 1
)

REM IMPORTANT:
REM We must CALL each line so `set VAR=value` actually executes
for /f "usebackq delims=" %%A in ("%ENV_FILE%") do (
  set "line=%%A"
  if not "!line!"=="" if "!line:~0,3!" NEQ "REM" (
    call !line!
  )
)

REM --------------------------------------------------
REM Validate required variables
REM --------------------------------------------------
if not defined GHCR_USERNAME (
  echo [ERROR] GHCR_USERNAME not set
  exit /b 1
)

if not defined GHCR_TOKEN (
  echo [ERROR] GHCR_TOKEN not set
  exit /b 1
)

if not defined GHCR_REGISTRY (
  echo [ERROR] GHCR_REGISTRY not set
  exit /b 1
)

if not defined IMAGE_NAME (
  echo [ERROR] IMAGE_NAME not set
  exit /b 1
)

if not defined TAGS (
  echo [ERROR] TAGS not set
  exit /b 1
)

REM --------------------------------------------------
REM Login to GHCR (idempotent)
REM --------------------------------------------------
echo [INFO ] Logging into %GHCR_REGISTRY% as %GHCR_USERNAME%

echo %GHCR_TOKEN% | docker login %GHCR_REGISTRY% ^
  --username %GHCR_USERNAME% ^
  --password-stdin

if errorlevel 1 (
  echo [ERROR] Docker login failed
  exit /b 1
)

REM --------------------------------------------------
REM Push images
REM --------------------------------------------------
for %%T in (%TAGS%) do (
  set IMAGE=%GHCR_REGISTRY%/%IMAGE_NAME%:%%T
  echo [PUSH ] !IMAGE!
  docker push !IMAGE!
  if errorlevel 1 (
    echo [ERROR] Failed to push !IMAGE!
    exit /b 1
  )
)

echo [DONE ] All images pushed successfully
endlocal
