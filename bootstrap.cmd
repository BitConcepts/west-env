@echo off
setlocal

echo Bootstrapping west-env (Windows)...

where west >nul 2>&1
if errorlevel 1 (
  echo west not found in PATH
  exit /b 1
)

pip install -e .

if not exist west-env.yml (
  copy example\west-env.yml west-env.yml >nul
  echo Created west-env.yml
)

echo.
echo Done.
echo Try:
echo   west env doctor
echo   west env build
