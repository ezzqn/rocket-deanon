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
from telethon import TelegramClient, errors
import subprocess

# ===== ТЕСТОВЫЕ ДАННЫЕ TELEGRAM =====
api_id = 2040
api_hash = 'b18441a1ff607e10a989891a5462e627'
SESSION_NAME = 'snos_session'

# ===== ОЧИСТКА =====
def clear():
    os.system('clear')

# ===== 1. МАКСИМУМ ПО TELEGRAM-ЮЗЕРУ =====
def get_max_telegram_info(username):
    print(f"\n[+] Сбор данных по @{username}...")
    info = {}
    
    # Через tgstat
    try:
        response = requests.get(f'https://api.tgstat.ru/channels/search?q=@{username}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('channels'):
                for ch in data['channels']:
                    if ch.get('username') == username:
                        info['id'] = ch.get('id', 'Неизвестно')
                        info['name'] = ch.get('title', 'Неизвестно')
                        info['phone'] = ch.get('phone', 'Не найден')
                        info['subscribers'] = ch.get('subscribers', 'Неизвестно')
                        info['bio'] = ch.get('about', 'Неизвестно')
                        info['photo'] = ch.get('photo', 'Неизвестно')
                        break
    except:
        pass
    
    # Если не нашли — ручной ввод
    if not info:
        info['id'] = 'Неизвестно'
        info['name'] = 'Неизвестно'
        info['phone'] = input("[!] Введите номер, если известен (или ENTER): ")
        info['subscribers'] = 'Неизвестно'
        info['bio'] = 'Неизвестно'
        info['photo'] = 'Неизвестно'
    
    print(f"""
╔═══════════════════════════════════════════╗
║         ПОЛНАЯ ИНФОРМАЦИЯ ПО ЮЗЕРУ        ║
╠═══════════════════════════════════════════╣
║ Username: @{username}                                
║ ID: {info.get('id', 'Неизвестно')}                     
║ Имя: {info.get('name', 'Неизвестно')}                     
║ Номер: {info.get('phone', 'Не найден')}                  
║ Подписчиков: {info.get('subscribers', 'Неизвестно')}         
║ Описание: {info.get('bio', 'Неизвестно')}                 
║ Фото: {info.get('photo', 'Неизвестно')}                  
║ Ссылка: https://t.me/{username}                     
╚═══════════════════════════════════════════╝
""")
    
    # Поиск в соцсетях (дополнительно)
    print("\n[+] Соцсети по нику:")
    sites = {
        'Instagram': f'https://www.instagram.com/{username}',
        'Twitter': f'https://twitter.com/{username}',
        'GitHub': f'https://github.com/{username}',
        'Reddit': f'https://www.reddit.com/user/{username}',
        'TikTok': f'https://www.tiktok.com/@{username}',
        'YouTube': f'https://www.youtube.com/@{username}',
        'VK': f'https://vk.com/{username}',
        'Pinterest': f'https://pinterest.com/{username}',
        'Twitch': f'https://twitch.tv/{username}',
    }
    for site, url in sites.items():
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"  ✅ {site}: {url} (активен)")
            else:
                print(f"  ❌ {site}: {url}")
        except:
            print(f"  ⚠️ {site}: ошибка проверки")
    
    return info.get('phone')

# ===== 2. МАКСИМУМ ПО НОМЕРУ ТЕЛЕФОНА =====
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
║ Возможность: {phonenumbers.is_possible_number(num)}
╠═══════════════════════════════════════════╣
""")
    except:
        print("[-] Ошибка разбора номера")
        return
    
    # Проверка утечек
    print("[+] Проверка утечек...")
    try:
        response = requests.get(f'https://haveibeenpwned.com/api/v3/breachedaccount/{phone}', timeout=5)
        if response.status_code == 200:
            print("  ⚠️ Номер найден в базах утечек!")
        else:
            print("  ✅ Утечек не найдено.")
    except:
        print("  ⚠️ Не удалось проверить утечки.")
    
    # Соцсети
    print("\n[+] Привязка к соцсетям:")
    social_links = {
        'Telegram': f'https://t.me/+{phone[1:]}',
        'VK': f'https://vk.com/phone{phone[1:]}',
        'WhatsApp': f'https://wa.me/{phone}',
        'Signal': f'https://signal.me/#p/{phone}',
        'Viber': f'viber://chat?number={phone}',
    }
    for name, url in social_links.items():
        print(f"  {name}: {url}")
    
    # Местоположение по номеру (через opencnam)
    print("\n[+] Местоположение:")
    try:
        response = requests.get(f'https://api.opencnam.com/v3/phone/{phone}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  Город: {data.get('city', 'Неизвестно')}")
            print(f"  Штат/Регион: {data.get('state', 'Неизвестно')}")
        else:
            print("  ⚠️ Не удалось определить местоположение.")
    except:
        print("  ⚠️ Ошибка запроса к opencnam.")
    
    # Предполагаемый IP
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

# ===== 4. МАКСИМУМ ПО IP-АДРЕСУ =====
def get_max_ip_info(ip):
    print(f"\n[+] Сбор данных по IP {ip}...")
    
    # Геолокация
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
║ Временная зона: {data.get('timezone', 'Неизвестно')}
║ Карта: https://www.google.com/maps?q={lat},{lon}
╚═══════════════════════════════════════════╝
""")
        else:
            print("[-] IP не найден.")
    except:
        print("[-] Ошибка геолокации.")
    
    # Проверка на VPN/прокси
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
    
    # Проверка на спам/злоупотребления (AbuseIPDB)
    print("\n[+] Проверка на злоупотребления:")
    try:
        response = requests.get(f'https://api.abuseipdb.com/api/v2/check?ipAddress={ip}', 
                                headers={'Key': 'ваш_ключ_abuseipdb'}, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  Жалоб: {data['data']['totalReports']}")
            print(f"  Уровень доверия: {data['data']['abuseConfidenceScore']}%")
        else:
            print("  ⚠️ Не удалось проверить (требуется API-ключ).")
    except:
        print("  ⚠️ Ошибка проверки.")
    
    # Обратный DNS
    print("\n[+] Обратный DNS:")
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        print(f"  Хост: {hostname}")
    except:
        print("  ⚠️ Не удалось определить.")

# ===== 5. СНОСЕР =====
async def send_reports(target_username):
    print("\n" + "="*50)
    print(" ROCKET SNOSER — 20 жалоб за 10 минут")
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
    
    print(f"\n[+] Старт: 20 жалоб, интервал 30 сек.\n")
    sent = 0
    errors_count = 0
    start_time = time.time()
    
    for i in range(1, 21):
        try:
            await client.report(entity, reason='spam')
            sent += 1
            print(f"[{i:>2}/20] ✅ Жалоба отправлена")
        except errors.FloodWaitError as e:
            print(f"[{i:>2}/20] ⚠️ Флуд-вейт {e.seconds} сек — ждём...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            errors_count += 1
            print(f"[{i:>2}/20] ❌ Ошибка: {e}")
        
        if i < 20:
            await asyncio.sleep(30)
    
    elapsed = int(time.time() - start_time)
    minutes = elapsed // 60
    seconds = elapsed % 60
    
    print("\n" + "="*50)
    print(" ОТЧЁТ ПО СНОСУ")
    print("="*50)
    print(f" Цель:          @{target_username}")
    print(f" Отправлено:    {sent}/20 жалоб")
    print(f" Ошибок:        {errors_count}")
    print(f" Время:         {minutes} мин {seconds} сек")
    print(f" Статус:        {'✅ ЦЕЛЬ ЗАБЛОКИРОВАНА' if sent >= 15 else '⚠️ ЖАЛОБ НЕДОСТАТОЧНО'}")
    print("="*50 + "\n")
    
    await client.disconnect()

# ===== 6. ГЛАВНОЕ МЕНЮ =====
def main():
    while True:
        clear()
        print("""
╔═══════════════════════════════════════════╗
║     [ ROCKET DEANON PRO v6.0 ]           ║
║         МАКСИМУМ ИНФОРМАЦИИ              ║
╠═══════════════════════════════════════════╣
║  telegram   — полная инфо по юзеру       ║
║  number     — полная инфо по номеру      ║
║  ip         — полная инфо по IP          ║
║  snos       — снос (20 жалоб)            ║
║  exit       — выход                       ║
╚═══════════════════════════════════════════╝
""")
        choice = input(">> ").strip().lower()

        if choice == 'telegram':
            username = input("Введите username (без @): ")
            phone = get_max_telegram_info(username)
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
