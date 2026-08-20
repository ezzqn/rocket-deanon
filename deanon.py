import requests
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import os
import json
import time
import asyncio
import socket
import re
import sys
import subprocess
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import InputReportReasonViolence

# ===== ВЕРСИЯ =====
VERSION = "9.6"
REPO_URL = "https://raw.githubusercontent.com/ezzqn/rocket-deanon/main/deanon.py"

# ===== ФУНКЦИИ =====
def version_to_tuple(v):
    return tuple(map(int, v.split('.')))

def git_push():
    print("[+] Проверка изменений в репозитории...")
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True
        )
        if status.stdout.strip():
            print("[+] Обнаружены изменения. Отправка на GitHub...")
            subprocess.run(["git", "add", "."], cwd=os.path.dirname(os.path.abspath(__file__)))
            commit_msg = f"Авто-пуш: обновление от {time.strftime('%Y-%m-%d %H:%M')}"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=os.path.dirname(os.path.abspath(__file__)))
            result = subprocess.run(["git", "push"], cwd=os.path.dirname(os.path.abspath(__file__)))
            if result.returncode == 0:
                print("✅ Изменения отправлены на GitHub.")
            else:
                print("❌ Ошибка при пуше.")
        else:
            print("[+] Нет изменений для пуша.")
    except Exception as e:
        print(f"[!] Ошибка авто-пуша: {e}")

def check_update():
    print("[+] Проверка обновлений...")
    try:
        response = requests.get(REPO_URL, timeout=5, headers={"User-Agent": "curl/7.68.0"})
        if response.status_code == 200:
            remote_code = response.text
            match = re.search(r'VERSION\s*=\s*"([^"]+)"', remote_code)
            if match:
                remote_version = match.group(1)
                if version_to_tuple(remote_version) > version_to_tuple(VERSION):
                    print(f"\n⚠️ ДОСТУПНА НОВАЯ ВЕРСИЯ: {remote_version} (у вас {VERSION})")
                    print("[+] Обновление через 3 секунды...")
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
git_push()

# ===== НАСТРОЙКИ =====
api_id = 2040
api_hash = 'b18441a1ff607e10a989891a5462e627'
SESSION_NAME = 'snos_session'

TOTAL_REPORTS = 50
INTERVAL = 30
TARGET_USERNAME = ""

def clear():
    os.system('clear')

# ===== ФУНКЦИИ ПОИСКА (ГОСДАННЫЕ) =====
def search_inn_free(inn):
    print(f"\n[+] Проверка ИНН: {inn}")
    try:
        url = f"https://api-fns.ru/api/inn?inn={inn}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                print("[✅] ИНН существует.")
                print(f"  Организация: {data['items'][0].get('name', 'Неизвестно')}")
            else:
                print("[❌] ИНН не найден.")
        else:
            print("[!] Сервис временно недоступен.")
    except Exception as e:
        print(f"[-] Ошибка: {e}")

def search_passport_free(passport):
    print(f"\n[+] Проверка паспорта: {passport}")
    try:
        url = f"https://api.nalog.ru/passport?series={passport[:4]}&number={passport[5:]}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                print("[✅] Паспорт действителен.")
            else:
                print("[❌] Паспорт недействителен.")
        else:
            print("[!] Сервис недоступен.")
    except Exception as e:
        print(f"[-] Ошибка: {e}")

def search_ogrn_free(ogrn):
    print(f"\n[+] Проверка ОГРН: {ogrn}")
    try:
        url = f"https://api-fns.ru/api/ogrn?ogrn={ogrn}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                print("[✅] ОГРН существует.")
                print(f"  Организация: {data['items'][0].get('name', 'Неизвестно')}")
            else:
                print("[❌] ОГРН не найден.")
        else:
            print("[!] Сервис недоступен.")
    except Exception as e:
        print(f"[-] Ошибка: {e}")

def search_car_free(plate):
    print(f"\n[+] Проверка номера авто: {plate}")
    try:
        url = f"https://api.avtocod.ru/api/v1/check?plate={plate}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('found'):
                print("[✅] Номер найден.")
                print(f"  Марка: {data.get('brand', 'Неизвестно')}")
                print(f"  Модель: {data.get('model', 'Неизвестно')}")
                print(f"  Год: {data.get('year', 'Неизвестно')}")
            else:
                print("[❌] Номер не найден.")
        else:
            print("[!] Сервис недоступен.")
    except Exception as e:
        print(f"[-] Ошибка: {e}")

def search_snils_free(snils):
    print(f"\n[+] Проверка СНИЛС: {snils}")
    pattern = r'^\d{3}-\d{3}-\d{3} \d{2}$'
    if re.match(pattern, snils):
        print("[✅] Формат СНИЛС правильный.")
        print("[!] Для проверки существования используйте gosuslugi.ru")
    else:
        print("[❌] Неверный формат СНИЛС.")

async def gos_menu():
    while True:
        clear()
        print("""
╔══════════════════════════════════════════════════════════╗
║                     📋 ГОСДАННЫЕ                         ║
╠══════════════════════════════════════════════════════════╣
║  1. 🚗 По номеру автомобиля                             ║
║  2. 🆔 По СНИЛС (проверка формата)                      ║
║  3. 🛂 По паспорту                                      ║
║  4. 📄 По ИНН                                           ║
║  5. 🏢 По ОГРН                                          ║
║  6. 🔙 Назад (в главное меню)                           ║
╚══════════════════════════════════════════════════════════╝
""")
        choice = input(">> ").strip()
        
        if choice == '1':
            plate = input("Введите номер автомобиля (A123BC): ").strip().upper()
            search_car_free(plate)
            input("\nENTER → продолжить")
        elif choice == '2':
            snils = input("Введите СНИЛС (123-456-789 01): ").strip()
            search_snils_free(snils)
            input("\nENTER → продолжить")
        elif choice == '3':
            passport = input("Введите паспорт (45 12 345678): ").strip()
            search_passport_free(passport)
            input("\nENTER → продолжить")
        elif choice == '4':
            inn = input("Введите ИНН (10 или 12 цифр): ").strip()
            search_inn_free(inn)
            input("\nENTER → продолжить")
        elif choice == '5':
            ogrn = input("Введите ОГРН (13 цифр): ").strip()
            search_ogrn_free(ogrn)
            input("\nENTER → продолжить")
        elif choice == '6':
            break
        else:
            print("[!] Неверный выбор.")
            time.sleep(1)

# ===== ОСНОВНОЕ МЕНЮ (ВЫРОВНЕННОЕ) =====
async def main():
    global TARGET_USERNAME
    while True:
        clear()
        print("""
╔══════════════════════════════════════════════════════════╗
║   ██████╗  ██████╗  ██████╗ ██╗  ██╗███████╗████████╗  ║
║   ██╔══██╗██╔═══██╗██╔═══██╗██║ ██╔╝██╔════╝╚══██╔══╝  ║
║   ██████╔╝██║   ██║██║   ██║█████╔╝ █████╗     ██║     ║
║   ██╔══██╗██║   ██║██║   ██║██╔═██╗ ██╔══╝     ██║     ║
║   ██║  ██║╚██████╔╝╚██████╔╝██║  ██╗███████╗   ██║     ║
║   ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝     ║
╠══════════════════════════════════════════════════════════╣
║                  ROCKET DEANON PRO v9.6                  ║
║                  АВТОПОИСК УГРОЗ                         ║
╠══════════════════════════════════════════════════════════╣
║  [1] 👤 TELEGRAM   — инфо по юзеру                      ║
║  [2] 📞 NUMBER     — инфо по номеру                     ║
║  [3] 🌐 IP         — инфо по IP                         ║
║  [4] 💣 SNOS       — снос (50 жалоб)                    ║
║  [5] 📊 STATUS     — проверить статус                   ║
║  [6] 📋 GOSDATA    — госданные (бесплатно)              ║
║  [7] 🚪 EXIT       — выход                              ║
╚══════════════════════════════════════════════════════════╝
║  @ezzqn  |  t.me/sovetovosint                           ║
╚══════════════════════════════════════════════════════════╝
""")
        choice = input(">> ").strip().lower()

        if choice == '1' or choice == 'telegram':
            username = input("Введите username (без @): ")
            phone = get_phone_by_nick(username)
            if phone and phone != 'Не найден':
                get_max_phone_info(phone)
            input("\nENTER → меню")

        elif choice == '2' or choice == 'number':
            phone = input("Введите номер (+79001234567): ")
            get_max_phone_info(phone)
            input("\nENTER → меню")

        elif choice == '3' or choice == 'ip':
            ip = input("Введите IP: ")
            get_max_ip_info(ip)
            input("\nENTER → меню")

        elif choice == '4' or choice == 'snos':
            target = input("Введите username канала или пользователя (без @): ")
            TARGET_USERNAME = target
            await send_reports(target)
            input("\nENTER → меню")

        elif choice == '5' or choice == 'status':
            if not TARGET_USERNAME:
                target = input("Введите username (без @): ")
                TARGET_USERNAME = target
            print(f"\n[+] Проверка статуса @{TARGET_USERNAME}...")
            status, _ = await check_account_status(TARGET_USERNAME)
            print(f"\n📌 СТАТУС АККАУНТА: {status}")
            input("\nENTER → меню")

        elif choice == '6' or choice == 'gosdata':
            await gos_menu()

        elif choice == '7' or choice == 'exit':
            print("Выход.")
            break

        else:
            input("Неверно. ENTER → меню")

# ===== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ =====
async def check_account_status(username):
    client = TelegramClient(SESSION_NAME, api_id, api_hash)
    await client.start()
    try:
        entity = await client.get_entity(f'@{username}')
        if entity.deleted:
            status = "❌ Аккаунт удалён или заблокирован"
        elif entity.restricted:
            status = "⚠️ Аккаунт ограничен"
        else:
            status = "✅ Аккаунт активен"
        await client.disconnect()
        return status, entity
    except errors.UsernameNotOccupiedError:
        await client.disconnect()
        return "❌ Пользователь не найден", None
    except Exception as e:
        await client.disconnect()
        return f"⚠️ Ошибка: {e}", None

async def send_reports(target_username):
    print("\n" + "="*50)
    print(f" ROCKET SNOSER — {TOTAL_REPORTS} жалоб за {TOTAL_REPORTS * INTERVAL // 60} минут")
    print(" ПРИЧИНА: УГРОЗЫ (VIOLENCE)")
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
    
    msg_ids = []
    while True:
        threat_ids, _ = await find_threat_messages(client, entity, limit=150)
        if threat_ids:
            msg_ids = threat_ids
            break
        else:
            print("\n" + "="*50)
            print(" УГРОЗЫ НЕ ОБНАРУЖЕНЫ. ВЫБЕРИТЕ ДЕЙСТВИЕ:")
            print("="*50)
            print("  1. 🔄 Повторить поиск")
            print("  2. ⚠️ Отправить без привязки (РИСК БАНА)")
            print("  3. ❌ Отменить отправку")
            print("="*50)
            choice = input(">> ").strip()
            
            if choice == '1':
                continue
            elif choice == '2':
                print("[!] Отправка без привязки...")
                try:
                    last_msg = await client.get_messages(entity, limit=1)
                    msg_ids = [last_msg[0].id] if last_msg else [1]
                except:
                    msg_ids = [1]
                break
            elif choice == '3':
                print("[❌] Отменено.")
                await client.disconnect()
                return
    
    print(f"\n[+] Старт: {TOTAL_REPORTS} жалоб\n")
    sent = 0
    errors_count = 0
    start_time = time.time()
    
    for i in range(1, TOTAL_REPORTS + 1):
        try:
            await client.call(
                ReportRequest(
                    peer=entity,
                    id=msg_ids,
                    reason=InputReportReasonViolence()
                )
            )
            sent += 1
            print(f"[{i:>2}/{TOTAL_REPORTS}] ✅ Жалоба отправлена")
        except errors.FloodWaitError as e:
            print(f"[{i:>2}/{TOTAL_REPORTS}] ⚠️ Флуд-вейт {e.seconds} сек")
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
    print("="*50 + "\n")
    
    await client.disconnect()

async def find_threat_messages(client, entity, limit=150):
    print(f"[+] Сканирование последних {limit} сообщений...")
    messages = await client.get_messages(entity, limit=limit)
    threat_ids = []
    for msg in messages:
        if msg.text:
            msg_lower = msg.text.lower()
            for word in THREAT_KEYWORDS:
                if word in msg_lower:
                    threat_ids.append(msg.id)
                    print(f"  ⚠️ Угроза в сообщении {msg.id}")
                    break
    if threat_ids:
        print(f"[+] Найдено {len(threat_ids)} сообщений с угрозами.")
        return threat_ids, messages
    else:
        print("[!] УГРОЗЫ НЕ ОБНАРУЖЕНЫ.")
        return [], messages

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

THREAT_KEYWORDS = [
    'убью', 'убить', 'смерть', 'зарежу', 'зарезать', 'взорву', 'взорвать',
    'подожгу', 'поджечь', 'сломаю', 'сломать', 'изнасилую', 'изнасиловать',
    'отрежу', 'отрезать', 'вырежу', 'вырезать', 'закопаю', 'закопать',
    'киллер', 'расстрел', 'расстреляю', 'петля', 'пуля', 'нож', 'пистолет',
    'kill', 'death', 'die', 'murder', 'slaughter', 'blood', 'bloody',
    'shoot', 'shot', 'gun', 'weapon', 'bomb', 'explosive', 'terror',
    'attack', 'assault', 'violence', 'violent', 'threat', 'threaten',
]

if __name__ == "__main__":
    asyncio.run(main())
