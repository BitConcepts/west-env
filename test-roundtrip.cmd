@echo off
setlocal

echo Running west-env round-trip test...

west env doctor || exit /b 1

echo Testing shell startup...
west env shell -c "exit" || exit /b 1

echo Round-trip test passed.
