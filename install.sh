/bin/bash

echo "=================================="
echo "   ROCKET DEANON PRO — УСТАНОВКА"
echo "=================================="

echo "[1/4] Обновление пакетов..."
pkg update -y && pkg upgrade -y

echo "[2/4] Установка Python и Git..."
pkg install python git -y

echo "[3/4] Клонирование репозитория..."
git clone https://github.com/ezzqn/rocket-deanon
cd rocket-deanon || exit

echo "[4/4] Установка библиотек..."
pip install -r requirements.txt

echo "=================================="
echo "✅ УСТАНОВКА ЗАВЕРШЕНА!"
echo "Запустите: python deanon.py"
echo "=================================="
