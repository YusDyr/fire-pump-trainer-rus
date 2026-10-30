@echo off
chcp 65001 >nul
rem Рендер роликов потоков воды насоса НЦПК М-В1У.
rem   render.bat            — черновик: все 4 ролика параллельно, каждый в своём окне (быстро)
rem   render.bat draft 2    — черновик только сценария 2
rem   render.bat final      — финал: Cycles на видеокарте NVIDIA, 1920x1080, по очереди
rem   render.bat final 1 3  — финал только сценариев 1 и 3
rem Сценарии: 1 водоём, 2 цистерна и гидрант, 3 слив и продувка, 4 ступень ВД и пена.
rem Ролики появляются в папке video рядом с этим файлом.
setlocal
set MODE=%1
if "%MODE%"=="" set MODE=draft

set BL=
if exist "%ProgramFiles%\Blender\blender.exe" set BL="%ProgramFiles%\Blender\blender.exe"
if not defined BL if exist "%ProgramFiles%\Blender Foundation\Blender 5.2\blender.exe" set BL="%ProgramFiles%\Blender Foundation\Blender 5.2\blender.exe"
if not defined BL for /f "delims=" %%P in ('where blender 2^>nul') do set BL="%%P"
if not defined BL (
  echo Не найден blender.exe в "%ProgramFiles%\Blender". Укажите путь вручную:
  echo   set BL="C:\путь\к\blender.exe" ^& render.bat
  pause & exit /b 1
)
echo Blender: %BL%
pushd "%~dp0"

if /i "%MODE%"=="draft" if "%2"=="" (
  echo Черновик: запускаю 4 сценария параллельно, каждый в отдельном окне...
  for %%N in (1 2 3 4) do start "Черновик, сценарий %%N" cmd /c ""%BL:"=%" -b --python "%~dp0render_win.py" -- draft %%N & echo. & echo Сценарий %%N готов & pause"
  echo Окна запущены. Ролики появятся в "%~dp0video".
  exit /b 0
)

echo Режим: %MODE% %2 %3 %4 %5
%BL% -b --python "%~dp0render_win.py" -- %MODE% %2 %3 %4 %5
echo.
echo Готово. Ролики — в папке "%~dp0video"
pause
