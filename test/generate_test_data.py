#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Генератор тестовых данных для memc_load.py

Создает TSV.gz файлы с логами установок приложений в формате:
тип_устройства\tидентификатор\tширота\tдолгота\tсписок_приложений

Пример запуска:
    python generate_test_data.py --output-dir=./test_data --count=3 --records-per-file=1000
"""

import argparse
import gzip
import os
import random
from datetime import datetime, timedelta
import string

# Конфигурация
DEVICE_TYPES = ['idfa', 'gaid', 'adid', 'dvid']

# Диапазоны координат для разных регионов мира
COORDINATES_RANGES = [
    # Северная Америка
    {'lat': (24.396308, 49.384358), 'lon': (-125.0, -66.93457)},
    # Европа
    {'lat': (36.0, 71.0), 'lon': (-10.0, 30.0)},
    # Азия
    {'lat': (1.4, 53.0), 'lon': (60.0, 150.0)},
    # Южная Америка
    {'lat': (-55.0, 12.0), 'lon': (-81.0, -34.0)},
    # Австралия
    {'lat': (-43.0, -10.0), 'lon': (113.0, 154.0)},
]

# Минимальный и максимальный ID приложений
APP_ID_RANGE = (100, 9999)

# Минимальное и максимальное количество приложений на устройстве
APPS_PER_DEVICE = (5, 50)

def generate_device_id(device_type):
    """Генерирует идентификатор устройства в зависимости от типа."""
    if device_type == 'idfa':
        # IDFA: 32-символьный шестнадцатеричный
        return ''.join(random.choices('0123456789abcdef', k=32))
    elif device_type == 'gaid':
        # GAID: 32-символьный шестнадцатеричный
        return ''.join(random.choices('0123456789abcdef', k=32))
    elif device_type == 'adid':
        # ADID: 16-символьный шестнадцатеричный
        return ''.join(random.choices('0123456789abcdef', k=16))
    elif device_type == 'dvid':
        # DVID: 10-символьный буквенно-цифровой
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return None

def generate_coordinates():
    """Генерирует случайные координаты из одного из регионов."""
    region = random.choice(COORDINATES_RANGES)
    lat = round(random.uniform(region['lat'][0], region['lat'][1]), 10)
    lon = round(random.uniform(region['lon'][0], region['lon'][1]), 10)
    return lat, lon

def generate_apps_list():
    """Генерирует список установленных приложений."""
    count = random.randint(APPS_PER_DEVICE[0], APPS_PER_DEVICE[1])
    apps = random.sample(range(APP_ID_RANGE[0], APP_ID_RANGE[1] + 1), count)
    return ','.join(map(str, apps))

def generate_filename(base_time, index):
    """
    Генерирует имя файла в хронологическом порядке.

    Args:
        base_time: базовое время
        index: индекс файла

    Returns:
        str: имя файла в формате YYYYMMDDHHMMSS.tsv.gz
    """
    file_time = base_time + timedelta(minutes=index)
    return file_time.strftime("%Y%m%d%H%M%S.tsv.gz")

def generate_record():
    """Генерирует одну запись лога."""
    device_type = random.choice(DEVICE_TYPES)
    device_id = generate_device_id(device_type)
    lat, lon = generate_coordinates()
    apps_list = generate_apps_list()

    return f"{device_type}\t{device_id}\t{lat}\t{lon}\t{apps_list}"

def create_test_file(filepath, record_count):
    """
    Создает тестовый файл с заданным количеством записей.

    Args:
        filepath: путь к файлу
        record_count: количество записей
    """
    with gzip.open(filepath, 'wt', encoding='utf-8') as f:
        for _ in range(record_count):
            record = generate_record()
            f.write(record + '\n')

    print(f"Создан файл: {filepath} ({record_count} записей)")

def main():
    parser = argparse.ArgumentParser(description="Генератор тестовых данных для memc_load.py")
    parser.add_argument("--output-dir", default="./test_data", help="Каталог для сохранения файлов")
    parser.add_argument("--count", type=int, default=3, help="Количество файлов для генерации")
    parser.add_argument("--records-per-file", type=int, default=1000, help="Количество записей в каждом файле")
    parser.add_argument("--start-time", default=None, help="Начальное время в формате YYYY-MM-DD HH:MM:SS")

    args = parser.parse_args()

    # Создаем каталог для вывода
    os.makedirs(args.output_dir, exist_ok=True)

    # Определяем начальное время
    if args.start_time:
        base_time = datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
    else:
        base_time = datetime.now().replace(microsecond=0, second=0, minute=0)

    print(f"Генерация тестовых данных:")
    print(f"  Каталог: {args.output_dir}")
    print(f"  Количество файлов: {args.count}")
    print(f"  Записей в файле: {args.records_per_file}")
    print(f"  Начальное время: {base_time}")
    print("-" * 50)

    # Генерируем файлы в хронологическом порядке
    for i in range(args.count):
        filename = generate_filename(base_time, i)
        filepath = os.path.join(args.output_dir, filename)
        create_test_file(filepath, args.records_per_file)

    print("-" * 50)
    print("Генерация завершена!")

if __name__ == "__main__":
    main()