@echo off
setlocal enabledelayedexpansion

rem Переходим в папку, где лежит этот файл
cd /d "%~dp0"

rem Проверяем, что установлен Python launcher
where py >nul 2>nul
if errorlevel 1 (
    echo Не найден Python launcher ^(команда "py"^).
    echo Установи Python 3.11 и поставь галочку "Add Python to PATH".
    pause
    exit /b 1
)

rem Создаём виртуальное окружение, если его ещё нет
if not exist ".venv\" (
    echo Создаю виртуальное окружение на Python 3.11...
    py -3.11 -m venv .venv
)

rem Активируем виртуальное окружение
call ".venv\Scripts\activate.bat"

rem Обновляем pip и ставим зависимости
python -m pip install --upgrade pip
pip install -r requirements.txt

rem Запускаем бота
python -m bot.main

echo.
echo Бот остановился. Нажми любую клавишу, чтобы закрыть окно.
pause >nul
endlocal
