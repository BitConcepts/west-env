@echo off
setlocal

echo Running west-env round-trip test (native)...

west env doctor || exit /b 1

echo Verifying shell startup...
west env shell <nul || exit /b 1

echo Native round-trip test passed.
