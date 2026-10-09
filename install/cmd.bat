@echo off
IF NOT EXIST ".venv\Scripts\activate.bat" (
    echo Virtual environment not found. Did you create it?
    EXIT /B 1
)

CALL .venv\Scripts\activate.bat
echo Virtual environment activated (CMD).
