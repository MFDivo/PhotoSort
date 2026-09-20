@echo off
chcp 65001 > nul
title Organizador de Fotos - Build

echo ====================================================
echo   GERANDO OrganizadorDeFotos.exe
echo ====================================================
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Instale em: https://www.python.org/downloads/
    echo Marque a opcao Add Python to PATH durante a instalacao.
    pause
    exit /b 1
)

echo [1/3] Instalando dependencias...
pip install pyinstaller Pillow exifread --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)
echo        OK

echo.
echo [2/3] Gerando o executavel (pode demorar 1-2 minutos)...
pyinstaller --onefile --windowed --name OrganizadorDeFotos --clean organize_photos.py
if errorlevel 1 (
    echo [ERRO] Falha ao gerar o executavel.
    pause
    exit /b 1
)
echo        OK

echo.
echo [3/3] Copiando para a pasta atual...
copy /Y dist\OrganizadorDeFotos.exe OrganizadorDeFotos.exe > nul
echo        OK

echo.
echo ====================================================
echo   PRONTO! Arquivo gerado: OrganizadorDeFotos.exe
echo ====================================================
echo.
echo Pode fechar esta janela e abrir o OrganizadorDeFotos.exe
pause
