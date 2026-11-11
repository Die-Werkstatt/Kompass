@echo off
rem Builds kompass-<version>.zip in this folder.
rem With "install" it also installs and enables it in the user_default repository.
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
if errorlevel 1 exit /b 1
if /i not "%~1"=="install" exit /b 0

rem An open Blender drops the new extension from the preferences it saves.
tasklist /fi "imagename eq blender.exe" | find /i "blender.exe" >nul
if not errorlevel 1 (
    echo Close Blender and run this again.
    exit /b 1
)

for /f "tokens=3" %%V in ('findstr /b "version" kompass\blender_manifest.toml') do set "VERSION=%%~V"
"%BLENDER%" --command extension install-file -r user_default --enable "kompass-%VERSION%.zip"
