@echo off
rem Builds kompass-<version>.zip in this folder. Does not install it.
setlocal
cd /d "%~dp0"

if defined BLENDER goto build
for /f "delims=" %%B in ('where blender 2^>nul') do if not defined BLENDER set "BLENDER=%%B"
if defined BLENDER goto build

rem The installer puts each version in its own folder. The last one in name order wins.
for /d %%D in ("%ProgramFiles%\Blender Foundation\Blender *") do if exist "%%D\blender.exe" set "BLENDER=%%D\blender.exe"
if defined BLENDER goto build
if exist "%ProgramFiles(x86)%\Steam\steamapps\common\Blender\blender.exe" set "BLENDER=%ProgramFiles(x86)%\Steam\steamapps\common\Blender\blender.exe"
if defined BLENDER goto build

echo Blender was not found. Set BLENDER to the path of blender.exe and run this again.
exit /b 1

:build
echo Building with "%BLENDER%"
"%BLENDER%" --command extension build --source-dir kompass
