@echo off
REM ============================================================
REM  Adversaires CVTT Vaires - lancement Windows
REM  Premier lancement : cree l'environnement et installe tout.
REM  Lancements suivants : met a jour les donnees et ouvre la page.
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
    echo Creation de l'environnement Python (une seule fois)...
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

python -m ttvaires %*
pause
