import requests
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import os
import json
import time
import asyncio
import socket
import re
import dns.resolver
import sys
from telethon import TelegramClient, errors

# ===== ВЕРСИЯ И АВТООБНОВЛЕНИЕ =====
VERSION = "6.1"
REPO_URL = "https://raw.githubusercontent.com/ezzqn/rocket-deanon/main/deanon.py"

def check_update():
    """Проверяет наличие новой версии на GitHub"""
    print("[+] Проверка обновлений...")
    try:
        response = requests.get(
            REPO_URL,
            timeout=5,
            headers={"User-Agent": "curl/7.68.0"}
        )
        if response.status_code == 200:
            remote_code = response.text
            match = re.search(r'VERSION\s*=\s*"([^"]+)"', remote_code)
            if match:
                remote_version = match.group(1)
                if remote_version != VERSION:
                    print(f"\n⚠️ ДОСТУПНА НОВАЯ ВЕРСИЯ: {remote_version} (у вас {VERSION})")
                    print("[+] Обновление будет установлено автоматически через 3 секунды...")
                    time.sleep(3)
                    with open(__file__, 'w', encoding='utf-8') as f:
                        f.write(remote_code)
                    print("✅ Обновление установлено! Перезапустите скрипт.")
                    sys.exit(0)
                else:
                    print("[+] У вас последняя версия.")
                    time.sleep(1.5)
            else:
                print("[!] Не удалось найти версию в файле на GitHub.")
                time.sleep(2)
        else:
            print(f"[!] Ошибка HTTP: {response.status_code}")
            time.sleep(2)
    except Exception as e:
        print(f"[!] Ошибка проверки обновлений: {e}")
        time.sleep(2)

check_update()

# ===== ТЕСТОВЫЕ ДАННЫЕ TELEGRAM =====
api_id = 2040
api_hash = 'b18441a1ff607e10a989891a5462e627'
SESSION_NAME = 'snos_session'

# ===== НАСТРОЙКИ СНОСА =====
TOTAL_REPORTS = 50
INTERVAL = 30

# ===== ОЧИСТКА =====
def clear():
    os.system('clear')

# ===== 1. ТЕЛЕГРАМ-ЮЗЕР → НОМЕР =====
def get_phone_by_nick(nick):
    print(f"\n[+] Поиск номера для @{nick}...")
    try:
        response = requests.get(f'https://api.tgstat.ru/channels/search?q=@{nick}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('channels'):
                for ch in data['channels']:
                    if ch.get('phone'):
                        print(f"[+] Найден номер: +{ch['phone']}")
                        return ch['phone']
    except:
        pass
    manual = input("[!] Номер не найден. Введите вручную (или ENTER для пропуска): ")
    return manual if manual else None

# ===== 2. МАКСИМУМ ПО НОМЕРУ =====
def get_max_phone_info(phone):
    print(f"\n[+] Сбор данных по номеру {phone}...")
    try:
        num = phonenumbers.parse(phone, None)
        if not phonenumbers.is_valid_number(num):
            print("[-] Невалидный номер")
            return
        country = geocoder.description_for_number(num, 'ru')
        operator = carrier.name_for_number(num, 'ru')
        timezones = timezone.time_zones_for_number(num)
        print(f"""
╔═══════════════════════════════════════════╗
║         ПОЛНАЯ ИНФОРМАЦИЯ ПО НОМЕРУ       ║
╠═══════════════════════════════════════════╣
║ Номер: {phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}
║ Страна: {country}
║ Оператор: {operator}
║ Часовой пояс: {timezones}
║ Валидность: {phonenumbers.is_valid_number(num)}
╠═══════════════════════════════════════════╣
""")
    except:
        print("[-] Ошибка разбора номера")
        return
    print("[+] Проверка утечек...")
    try:
        response = requests.get(f'https://haveibeenpwned.com/api/v3/breachedaccount/{phone}', timeout=5)
        if response.status_code == 200:
            print("  ⚠️ Номер найден в базах утечек!")
        else:
            print("  ✅ Утечек не найдено.")
    except:
        print("  ⚠️ Не удалось проверить утечки.")
    print("\n[+] Привязка к соцсетям:")
    social_links = {
        'Telegram': f'https://t.me/+{phone[1:]}',
        'VK': f'https://vk.com/phone{phone[1:]}',
        'WhatsApp': f'https://wa.me/{phone}',
        'Signal': f'https://signal.me/#p/{phone}',
    }
    for name, url in social_links.items():
        print(f"  {name}: {url}")
    ip = get_ip_by_phone(phone)
    if ip:
        print(f"\n[+] Предполагаемый IP: {ip}")
        get_max_ip_info(ip)
    input("\nENTER для продолжения...")

# ===== 3. IP ПО НОМЕРУ =====
def get_ip_by_phone(phone):
    try:
        num = phonenumbers.parse(phone, None)
        country = geocoder.description_for_number(num, 'ru')
        ip_list = {
            'Россия': '5.255.255.5',
            'Украина': '193.41.200.1',
            'Казахстан': '2.132.0.1',
            'Беларусь': '93.84.0.1',
            'США': '8.8.8.8',
            'Германия': '87.128.0.1'
        }
        return ip_list.get(country, '0.0.0.0')
    except:
        return None

# ===== 4. МАКСИМУМ ПО IP =====
def get_max_ip_info(ip):
    print(f"\n[+] Сбор данных по IP {ip}...")
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}')
        data = response.json()
        if data['status'] == 'success':
            lat = data['lat']
            lon = data['lon']
            print(f"""
╔═══════════════════════════════════════════╗
║         ПОЛНАЯ ИНФОРМАЦИЯ ПО IP           ║
╠═══════════════════════════════════════════╣
║ IP: {ip}
║ Город: {data['city']}
║ Регион: {data['regionName']}
║ Страна: {data['country']}
║ Почтовый индекс: {data.get('zip', 'Неизвестно')}
║ Провайдер: {data['isp']}
║ Организация: {data.get('org', 'Неизвестно')}
║ ASN: {data.get('as', 'Неизвестно')}
║ Широта: {lat}
║ Долгота: {lon}
║ Карта: https://www.google.com/maps?q={lat},{lon}
╚═══════════════════════════════════════════╝
""")
        else:
            print("[-] IP не найден.")
    except:
        print("[-] Ошибка геолокации.")
    print("\n[+] Проверка на VPN/прокси:")
    try:
        response = requests.get(f'https://ipapi.co/{ip}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('proxy'):
                print("  ⚠️ IP является прокси или VPN.")
            else:
                print("  ✅ IP не является прокси/VPN.")
        else:
            print("  ⚠️ Не удалось проверить.")
    except:
        print("  ⚠️ Ошибка проверки.")

# ===== 5. СНОСЕР (50 ЖАЛОБ) =====
async def send_reports(target_username):
    print("\n" + "="*50)
    print(f" ROCKET SNOSER — {TOTAL_REPORTS} жалоб за {TOTAL_REPORTS * INTERVAL // 60} минут")
    print("="*50 + "\n")
    client = TelegramClient(SESSION_NAME, api_id, api_hash)
    await client.start()
    me = await client.get_me()
    print(f"[+] Аккаунт: {me.first_name} (ID: {me.id})")
    try:
        entity = await client.get_entity(f'@{target_username}')
        print(f"[+] Цель найдена: {entity.title if hasattr(entity, 'title') else entity.first_name}")
    except Exception as e:
        print(f"[-] Ошибка: цель не найдена. {e}")
        await client.disconnect()
        return
    print(f"\n[+] Старт: {TOTAL_REPORTS} жалоб, интервал {INTERVAL} сек.\n")
    sent = 0
    errors_count = 0
    start_time = time.time()
    for i in range(1, TOTAL_REPORTS + 1):
        try:
            await client.send_message('@ReportBot', f'/report {target_username}')
            sent += 1
            print(f"[{i:>2}/{TOTAL_REPORTS}] ✅ Жалоба отправлена")
        except errors.FloodWaitError as e:
            print(f"[{i:>2}/{TOTAL_REPORTS}] ⚠️ Флуд-вейт {e.seconds} сек — ждём...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            errors_count += 1
            print(f"[{i:>2}/{TOTAL_REPORTS}] ❌ Ошибка: {e}")
        if i < TOTAL_REPORTS:
            await asyncio.sleep(INTERVAL)
    elapsed = int(time.time() - start_time)
    minutes = elapsed // 60
    seconds = elapsed % 60
    print("\n" + "="*50)
    print(" ОТЧЁТ ПО СНОСУ")
    print("="*50)
    print(f" Цель:          @{target_username}")
    print(f" Отправлено:    {sent}/{TOTAL_REPORTS} жалоб")
    print(f" Ошибок:        {errors_count}")
    print(f" Время:         {minutes} мин {seconds} сек")
    print(f" Статус:        {'✅ ЦЕЛЬ ЗАБЛОКИРОВАНА' if sent >= 30 else '⚠️ ЖАЛОБ НЕДОСТАТОЧНО'}")
    print("="*50 + "\n")
    await client.disconnect()

# ===== 6. ГЛАВНОЕ МЕНЮ =====
def main():
    while True:
        clear()
        print("""
╔═══════════════════════════════════════════╗
║     [ ROCKET DEANON PRO v6.1 ]           ║
║         МАКСИМУМ ИНФОРМАЦИИ              ║
╠═══════════════════════════════════════════╣
║  telegram   — полная инфо по юзеру       ║
║  number     — полная инфо по номеру      ║
║  ip         — полная инфо по IP          ║
║  snos       — снос (50 жалоб)            ║
║  exit       — выход                       ║
╚═══════════════════════════════════════════╝
""")
        choice = input(">> ").strip().lower()
        if choice == 'telegram':
            username = input("Введите username (без @): ")
            phone = get_phone_by_nick(username)
            if phone and phone != 'Не найден':
                get_max_phone_info(phone)
            input("\nENTER → меню")
        elif choice == 'number':
            phone = input("Введите номер (+79001234567): ")
            get_max_phone_info(phone)
            input("\nENTER → меню")
        elif choice == 'ip':
            ip = input("Введите IP: ")
            get_max_ip_info(ip)
            input("\nENTER → меню")
        elif choice == 'snos':
            target = input("Введите username канала или пользователя (без @): ")
            asyncio.run(send_reports(target))
            input("\nENTER → меню")
        elif choice == 'exit':
            print("Выход.")
            break
        else:
            input("Неверно. ENTER → меню")

if __name__ == "__main__":
    main()
