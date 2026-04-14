#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Проверка доступности memcached серверов
"""

import memcache

SERVERS = {
    'idfa': '127.0.0.1:33013',
    'gaid': '127.0.0.1:33014',
    'adid': '127.0.0.1:33015',
    'dvid': '127.0.0.1:33016'
}

def check_server(addr, name):
    """Проверяет доступность сервера."""
    try:
        mc = memcache.Client([addr])
        # Попробуем записать и прочитать тестовое значение
        test_key = f"test_{name}"
        test_value = "OK"

        result_set = mc.set(test_key, test_value)
        result_get = mc.get(test_key)

        mc.delete(test_key)  # Очистим тестовый ключ

        if result_set and result_get == test_value:
            print(f"[✓] {name}: {addr} - ДОСТУПЕН")
            return True
        else:
            print(f"[✗] {name}: {addr} - ОШИБКА записи/чтения")
            return False

    except Exception as e:
        print(f"[✗] {name}: {addr} - НЕДОСТУПЕН ({e})")
        return False

if __name__ == "__main__":
    print("Проверка доступности memcached серверов:")
    print("-" * 50)

    all_ok = True
    for name, addr in SERVERS.items():
        if not check_server(addr, name):
            all_ok = False

    print("-" * 50)
    if all_ok:
        print("ВСЕ СЕРВЕРЫ ДОСТУПНЫ. Можно запускать memc_load.py")
    else:
        print("НЕКОТОРЫЕ СЕРВЕРЫ НЕДОСТУПНЫ. Проверьте их запуск.")