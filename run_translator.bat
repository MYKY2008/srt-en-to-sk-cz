@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

echo ===============================================
echo   SRT EN do SK/CZ prekladac - Spustac
echo ===============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Vytvaram virtualne prostredie...
    where py >nul 2>nul
    if %ERRORLEVEL%==0 (
        py -3 -m venv .venv
    ) else (
        where python >nul 2>nul
        if not %ERRORLEVEL%==0 (
            echo Python sa nenasiel. Nainstaluj Python 3 a skus znova.
            pause
            exit /b 1
        )
        python -m venv .venv
    )
) else (
    echo [1/4] Virtualne prostredie uz existuje.
)

echo [2/4] Aktualizujem pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul

echo [3/4] Instalujem requirements...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if not %ERRORLEVEL%==0 (
    echo Nepodarilo sa nainstalovat requirements.
    pause
    exit /b 1
)

echo.
echo [4/4] Priprava prekladaca je hotova.
echo.

set "INPUT_FILE="
set /p INPUT_FILE=Zadaj celu cestu k EN .srt alebo .mkv suboru (alebo ho sem pretiahni): 
set "INPUT_FILE=%INPUT_FILE:"=%"

if "%INPUT_FILE%"=="" (
    echo Nezadal si vstupny subor.
    pause
    exit /b 1
)

if not exist "%INPUT_FILE%" (
    echo Vstupny subor neexistuje: %INPUT_FILE%
    pause
    exit /b 1
)

echo.
echo Vyber rezim:
echo   1) Preklad titulkov (SRT alebo MKV->SRT->preklad)
echo   2) Iba extrakcia titulkov z MKV do SRT
set "MODE="
set /p MODE_CHOICE=Zadaj 1 alebo 2: 

if "%MODE_CHOICE%"=="1" set "MODE=translate"
if "%MODE_CHOICE%"=="2" set "MODE=extract"

if "%MODE%"=="" (
    echo Neplatna volba rezimu.
    pause
    exit /b 1
)

if "%MODE%"=="extract" (
    echo.
    echo Spustam extrakciu titulkov z MKV...
    ".venv\Scripts\python.exe" srt_translate.py "%INPUT_FILE%" --extract-only
    set EXIT_CODE=%ERRORLEVEL%

    echo.
    if %EXIT_CODE%==0 (
        echo Extrakcia uspesne dokoncena.
    ) else (
        echo Extrakcia zlyhala s navratovym kodom %EXIT_CODE%.
    )

    echo.
    pause
    exit /b %EXIT_CODE%
)

echo.
echo Vyber cielovy jazyk:
echo   1) Slovencina (sk)
echo   2) Cestina (cz)
set "TARGET="
set /p TARGET_CHOICE=Zadaj 1 alebo 2: 

if "%TARGET_CHOICE%"=="1" set "TARGET=sk"
if "%TARGET_CHOICE%"=="2" set "TARGET=cz"

if "%TARGET%"=="" (
    echo Neplatna volba jazyka.
    pause
    exit /b 1
)

echo.
echo Spustam preklad...
".venv\Scripts\python.exe" srt_translate.py "%INPUT_FILE%" --target %TARGET%
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE%==0 (
    echo Preklad uspesne dokonceny.
) else (
    echo Preklad zlyhal s navratovym kodom %EXIT_CODE%.
)

echo.
pause
exit /b %EXIT_CODE%
