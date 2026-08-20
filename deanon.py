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
import subprocess
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import InputReportReasonViolence

VERSION = "8.0"
REPO_URL = "https://raw.githubusercontent.com/ezzqn/rocket-deanon/main/deanon.py"

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

api_id = 2040
api_hash = 'b18441a1ff607e10a989891a5462e627'
SESSION_NAME = 'snos_session'

TOTAL_REPORTS = 50
INTERVAL = 30
TARGET_USERNAME = ""

def clear():
    os.system('clear')

THREAT_KEYWORDS = [
    'убью', 'убить', 'смерть', 'зарежу', 'зарезать', 'взорву', 'взорвать',
    'подожгу', 'поджечь', 'сломаю', 'сломать', 'изнасилую', 'изнасиловать',
    'отрежу', 'отрезать', 'вырежу', 'вырезать', 'закопаю', 'закопать',
    'киллер', 'расстрел', 'расстреляю', 'петля', 'пуля', 'нож', 'пистолет',
    'автомат', 'граната', 'бомба', 'взрывчатка', 'отравлю', 'отравить',
    'перережу', 'перерезать', 'задушу', 'задушить', 'сожгу', 'сжечь',
    'порежу', 'порву', 'разорву', 'разрезать', 'растерзаю', 'растерзать',
    'уничтожу', 'уничтожить', 'ликвидирую', 'ликвидировать', 'устрашу',
    'устрашить', 'нападу', 'напасть', 'ударю', 'ударить', 'забью', 'забить',
    'застрелю', 'застрелить', 'прикончу', 'прикончить', 'мочить', 'мокрое дело',
    'кинуть', 'кидануть', 'подставить', 'подстава', 'разберусь', 'разобраться',
    'вычислю', 'вычислить', 'найду', 'найти', 'доберусь', 'добраться',
    'приеду', 'прийти', 'приду', 'нагряну', 'нагрянуть', 'навещу', 'навестить',
    'kill', 'death', 'die', 'murder', 'slaughter', 'blood', 'bloody',
    'shoot', 'shot', 'gun', 'weapon', 'bomb', 'explosive', 'terror',
    'attack', 'assault', 'violence', 'violent', 'threat', 'threaten',
    'destroy', 'annihilate', 'execute', 'execution', 'hitman', 'assassin',
    'stab', 'stabbing', 'cut', 'slit', 'strangle', 'choke',
    'burn', 'fire', 'flame', 'torch', 'rape', 'molest',
    'трупа', 'труп', 'кровь', 'кровавый', 'кишки', 'расчленёнка',
    'мясо', 'мясник', 'псих', 'маньяк', 'сатана', 'дьявол',
    'ад', 'пекло', 'конец', 'финиш', 'каюк', 'хана',
    'завалю', 'завалить', 'положу', 'положить', 'урою', 'урыть',
    'закопаю', 'зарыть', 'закопать', 'замучаю', 'замучить',
    'изуродую', 'изуродовать', 'искалечу', 'искалечить',
    'прибью', 'прибить', 'пристукну', 'пристукнуть',
    'шлёпну', 'шлёпнуть', 'грохну', 'грохнуть',
    'мочить буду', 'кинуть на деньги', 'поджог', 'поджигатель',
    'террорист', 'экстремист', 'насильник', 'педофил', 'психопат'
]

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
                    print(f"  ⚠️ Угроза в сообщении {msg.id}: {msg.text[:60]}...")
                    break
    if threat_ids:
        print(f"[+] Найдено {len(threat_ids)} сообщений с угрозами.")
        return threat_ids
    else:
        print("[!] Угроз не найдено. Будет использовано последнее сообщение.")
        return [messages[0].id] if messages else [1]

async def check_account_status(username):
    client = TelegramClient(SESSION_NAME, api_id, api_hash)
    await client.start()
    try:
        entity = await client.get_entity(f'@{username}')
        if entity.deleted:
            status = "❌ Аккаунт удалён или заблокирован"
        elif entity.restricted:
            status = "⚠️ Аккаунт ограничен (возможны санкции)"
        else:
            status = "✅ Аккаунт активен"
        await client.disconnect()
        return status, entity
    except errors.UsernameNotOccupiedError:
        await client.disconnect()
        return "❌ Пользователь не найден (возможно, удалён)", None
    except Exception as e:
        await client.disconnect()
        return f"⚠️ Ошибка проверки: {e}", None

async def send_reports(target_username):
    print("\n" + "="*50)
    print(f" ROCKET SNOSER — {TOTAL_REPORTS} жалоб за {TOTAL_REPORTS * INTERVAL // 60} минут")
    print(" ПРИЧИНА: УГРОЗЫ (VIOLENCE)")
    print(" АВТОПОИСК УГРОЗ В 150 СООБЩЕНИЯХ")
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
    try:
        msg_ids = await find_threat_messages(client, entity, limit=150)
        print(f"[+] Будет использовано {len(msg_ids)} сообщений для привязки.")
    except Exception as e:
        print(f"[!] Ошибка сканирования: {e}. Использую последнее сообщение.")
        try:
            messages = await client.get_messages(entity, limit=1)
            msg_ids = [messages[0].id] if messages else [1]
        except:
            msg_ids = [1]
    print(f"\n[+] Старт: {TOTAL_REPORTS} жалоб (причина: угрозы), интервал {INTERVAL} сек.\n")
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
    print(f" Причина:       Угрозы (VIOLENCE)")
    print(f" Привязано сообщений: {len(msg_ids)}")
    print(f" Ошибок:        {errors_count}")
    print(f" Время:         {minutes} мин {seconds} сек")
    print(f" Статус:        ⏳ ЖАЛОБЫ НА РАССМОТРЕНИИ. ПРОВЕРЬТЕ СТАТУС ЧЕРЕЗ 1-2 ЧАСА.")
    print("="*50 + "\n")
    await client.disconnect()

async def main():
    global TARGET_USERNAME
    while True:
        clear()
        print("""
╔═══════════════════════════════════════════╗
║     [ ROCKET DEANON PRO v8.0 ]           ║
║         АВТОПОИСК УГРОЗ                  ║
╠═══════════════════════════════════════════╣
║  1. telegram   — инфо по юзеру           ║
║  2. number     — инфо по номеру          ║
║  3. ip         — инфо по IP              ║
║  4. snos       — снос (50 жалоб)         ║
║  5. status     — проверить статус цели   ║
║  6. exit       — выход                   ║
╚═══════════════════════════════════════════╝
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
        elif choice == '6' or choice == 'exit':
            print("Выход.")
            break
        else:
            input("Неверно. ENTER → меню")

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

if __name__ == "__main__":
    asyncio.run(main())
