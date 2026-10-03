@echo off
REM ============================================================
REM  Outils CVTT Vaires - lancement Windows
REM  Premier lancement : cree l'environnement et installe tout.
REM  Sans argument : affiche un menu. Avec arguments : les transmet
REM  directement, par exemple : lancer.bat --resultats --hors-ligne
REM  ATTENTION : pas de parentheses dans les echo, elles cassent les blocs if.
REM ============================================================
cd /d "%~dp0"

REM Detection de Python : lanceur "py" OU commande "python".
set "PYTHON="
where py >nul 2>nul && set "PYTHON=py"
if not defined PYTHON (
    where python >nul 2>nul && set "PYTHON=python"
)
if not defined PYTHON (
    echo Python n'est pas installe ou pas dans le PATH.
    echo Telechargez-le sur https://www.python.org/downloads/
    echo IMPORTANT : cochez "Add python.exe to PATH" pendant l'installation.
    pause
    exit /b 1
)

if not exist .venv (
    echo Creation de l'environnement Python, une seule fois...
    %PYTHON% -m venv .venv
    if errorlevel 1 (
        echo Echec de la creation de l'environnement virtuel.
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)
REM Mise a jour des dependances si une nouvelle version de l'outil en demande.
python -c "import requests, bs4, openpyxl" >nul 2>nul || python -m pip install -r requirements.txt

if not "%~1"=="" (
    python -m ttvaires %*
    pause
    exit /b
)

echo.
echo  ==================================================
echo    CVTT Vaires - championnat par equipes
echo  ==================================================
echo    1. Adversaires : effectifs, brulages, calendrier
echo    2. Resultats des joueurs de Vaires : page + Excel
echo    3. Les deux
echo    4. Page de demonstration, donnees fictives
echo    5. Quitter
echo.
choice /c 12345 /n /m "  Votre choix, de 1 a 5 : "
if errorlevel 5 exit /b 0
if errorlevel 4 goto demo
if errorlevel 3 goto les_deux
if errorlevel 2 goto resultats
python -m ttvaires --adversaires
goto fin
:demo
python -m ttvaires --demo
goto fin
:les_deux
python -m ttvaires --resultats --adversaires
goto fin
:resultats
python -m ttvaires --resultats
:fin
pause
