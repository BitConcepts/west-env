@echo off
setlocal

echo Running west-env container round-trip test (Windows)...

REM Check for Docker
where docker >nul 2>&1
if %errorlevel%==0 goto :engine_found

REM Check for Podman
where podman >nul 2>&1
if %errorlevel%==0 goto :engine_found

echo No container engine available, skipping
exit /b 0

:engine_found

west env doctor --container || exit /b 1

echo Verifying container execution...
west env build --container --help >nul || exit /b 1

echo Container round-trip test passed.
