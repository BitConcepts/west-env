@echo off
REM SPDX-License-Identifier: Apache-2.0
setlocal EnableDelayedExpansion

REM =====================================================
REM Build configuration
REM =====================================================
set IMAGE_REGISTRY=ghcr.io
set IMAGE_NAMESPACE=bitconcepts
set IMAGE_NAME=zephyr-build-env

set ZEPHYR_VERSION=4.3.0
set ZEPHYR_SDK_VERSION=0.17.4
set UBUNTU_VERSION=22.04

set IMAGE_TAG=%ZEPHYR_VERSION%-sdk%ZEPHYR_SDK_VERSION%-ubuntu%UBUNTU_VERSION%
set IMAGE_FULL=%IMAGE_REGISTRY%/%IMAGE_NAMESPACE%/%IMAGE_NAME%:%IMAGE_TAG%
set IMAGE_LATEST=%IMAGE_REGISTRY%/%IMAGE_NAMESPACE%/%IMAGE_NAME%:latest

REM =====================================================
REM Preconditions
REM =====================================================
where docker >nul 2>&1
if errorlevel 1 (
  echo ERROR: docker not found in PATH
  exit /b 1
)

if not exist Dockerfile (
  echo ERROR: Dockerfile not found in current directory
  echo Please run this script from the directory containing the Dockerfile
  exit /b 1
)

echo Building Zephyr build container
echo.
echo   Image:   %IMAGE_FULL%
echo   Latest:  %IMAGE_LATEST%
echo   Zephyr:  %ZEPHYR_VERSION%
echo   SDK:     %ZEPHYR_SDK_VERSION%
echo   Ubuntu:  %UBUNTU_VERSION%
echo.

REM =====================================================
REM Build image
REM =====================================================
docker build ^
  --build-arg ZEPHYR_SDK_VERSION=%ZEPHYR_SDK_VERSION% ^
  -t %IMAGE_FULL% ^
  .

if errorlevel 1 (
  echo ERROR: docker build failed
  exit /b 1
)

REM =====================================================
REM Tag latest
REM =====================================================
docker tag %IMAGE_FULL% %IMAGE_LATEST%

if errorlevel 1 (
  echo ERROR: docker tag failed
  exit /b 1
)

echo.
echo Build complete.
echo.
echo To push the image:
echo   docker login %IMAGE_REGISTRY%
echo   docker push %IMAGE_FULL%
echo   docker push %IMAGE_LATEST%
echo.

endlocal
