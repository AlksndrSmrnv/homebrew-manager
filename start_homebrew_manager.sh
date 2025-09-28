#!/bin/bash

# Homebrew Manager Launcher
# Скрипт для запуска GUI приложения управления Homebrew

echo "🚀 Запуск Homebrew Manager..."

# Проверяем наличие Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден! Установите Python 3."
    exit 1
fi

# Проверяем наличие tkinter
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "⚠️  tkinter не найден. Устанавливаем..."
    brew install python-tk
fi

# Запускаем приложение
python3 "$(dirname "$0")/homebrew_manager.py"