#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MemcLoad - многопоточный загрузчик логов в memcached
"""

import argparse
import gzip
import glob
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import memcache
except ImportError:
    print("Требуется установить memcache: pip install python-memcached")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname).1s %(message)s",
    datefmt="%Y.%m.%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Протобаф сообщение (упрощенная версия)
class PhoneLog:
    def __init__(self, lat=None, lon=None, apps=None):
        self.lat = lat
        self.lon = lon
        self.apps = apps or []

    def serialize(self):
        """Упрощенная сериализация в байты"""
        parts = []
        if self.lat is not None:
            parts.append(f"lat:{self.lat}")
        if self.lon is not None:
            parts.append(f"lon:{self.lon}")
        for app in self.apps:
            parts.append(f"apps:{app}")
        return "|".join(parts).encode('utf-8')

# Конфигурация серверов memcached
SUPPORTED_DEVICE_TYPES = {
    'idfa': '127.0.0.1:33013',
    'gaid': '127.0.0.1:33014',
    'adid': '127.0.0.1:33015',
    'dvid': '127.0.0.1:33016'
}

def parse_line(line):
    """
    Парсит строку TSV.

    Args:
        line: строка из файла

    Returns:
        tuple: (device_type, device_id, lat, lon, apps_list) или None при ошибке
    """
    try:
        parts = line.strip().split('\t')
        if len(parts) != 5:
            return None

        device_type, device_id, lat_str, lon_str, apps_str = parts

        if device_type not in SUPPORTED_DEVICE_TYPES:
            return None

        lat = float(lat_str)
        lon = float(lon_str)
        apps = [int(app) for app in apps_str.split(',') if app.strip()]

        return (device_type, device_id, lat, lon, apps)
    except (ValueError, IndexError):
        return None

def process_file(file_path, server_connections, dry_run):
    """
    Обрабатывает один файл.

    Args:
        file_path: путь к файлу
        server_connections: словарь подключений к серверам
        dry_run: сухой прогон

    Returns:
        bool: успех обработки
    """
    try:
        processed = 0
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                parsed = parse_line(line)
                if not parsed:
                    logger.debug(f"Пропущена строка {line_num} в {file_path}")
                    continue

                device_type, device_id, lat, lon, apps = parsed
                key = f"{device_type}:{device_id}"
                phone_log = PhoneLog(lat=lat, lon=lon, apps=apps)
                value = phone_log.serialize()

                server_addr = SUPPORTED_DEVICE_TYPES[device_type]
                conn = server_connections[server_addr]

                if not dry_run:
                    try:
                        result = conn.set(key, value)
                        if not result:
                            logger.warning(f"Не удалось записать {key} в {server_addr}")
                    except Exception as e:
                        logger.error(f"Ошибка записи {key} в {server_addr}: {e}")
                else:
                    logger.debug(f"{server_addr} - {key} -> lat: {lat} lon: {lon} apps: {len(apps)}")

                processed += 1

        logger.info(f"Файл {os.path.basename(file_path)}: обработано {processed} строк")
        return True

    except Exception as e:
        logger.error(f"Ошибка при обработке файла {file_path}: {e}")
        return False

def setup_memcached_connections(options):
    """
    Настраивает подключения к серверам memcached.

    Args:
        options: объект с параметрами

    Returns:
        dict: словарь подключений
    """
    connections = {}
    for device_type, default_addr in SUPPORTED_DEVICE_TYPES.items():
        addr = getattr(options, device_type, default_addr)
        try:
            connections[addr] = memcache.Client([addr])
            logger.info(f"Подключено к {addr} для {device_type}")
        except Exception as e:
            logger.error(f"Не удалось подключиться к {addr} для {device_type}: {e}")
            if not options.dry:
                raise
    return connections

def get_sorted_files(pattern):
    """
    Возвращает отсортированный список файлов по хронологическому порядку.

    Args:
        pattern: паттерн для glob

    Returns:
        list: отсортированные пути к файлам
    """
    # Логируем путь для отладки
    logger.info(f"Поиск файлов по паттерну: {pattern}")

    # Преобразуем все слэши к стандарту ОС
    pattern = os.path.normpath(pattern)
    logger.info(f"Нормализованный путь: {pattern}")

    # Проверяем существование директории
    directory = os.path.dirname(pattern)
    if os.path.exists(directory):
        logger.info(f"Директория существует: {directory}")
        files_in_dir = os.listdir(directory)
        logger.info(f"Содержимое директории: {files_in_dir}")

        # Покажем все файлы с их путями
        for f in files_in_dir:
            full_path = os.path.join(directory, f)
            size = os.path.getsize(full_path)
            logger.info(f"  {f} ({size} байт)")
    else:
        logger.error(f"Директория не существует: {directory}")
        return []

    # Ищем файлы разными способами
    patterns_to_try = [
        pattern,
        pattern.replace('/', os.sep).replace('\\', os.sep),
        pattern.replace('\\', '/'),
        pattern.replace('/', '\\'),
    ]

    files = []
    for pat in patterns_to_try:
        found = glob.glob(pat)
        if found:
            logger.info(f"Найдено {len(found)} файлов по паттерну '{pat}':")
            for f in found:
                logger.info(f"  - {f}")
            files = found
            break

    # Если ничего не найдено, попробуем найти все .tsv.gz файлы в директории
    if not files:
        dir_only = os.path.dirname(pattern)
        all_files = glob.glob(os.path.join(dir_only, "*.tsv.gz")) + \
                   glob.glob(os.path.join(dir_only, "*.TSV.GZ")) + \
                   glob.glob(os.path.join(dir_only, "*.Tsv.Gz"))

        if all_files:
            logger.warning(f"Найдены файлы с расширением .tsv.gz (возможно, регистр отличается): {len(all_files)}")
            for f in all_files:
                logger.info(f"  - {f}")
            files = all_files

    return sorted(files)

def rename_processed_file(file_path):
    """
    Переименовывает обработанный файл, добавляя точку в начало имени.
    (Во избежание повторной обработки)

    Args:
        file_path: путь к файлу

    Returns:
        bool: успех операции
    """
    try:
        dir_name = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        new_path = os.path.join(dir_name, f".{base_name}")
        os.rename(file_path, new_path)
        logger.info(f"Файл переименован: {file_path} -> {new_path}")
        return True
    except Exception as e:
        logger.error(f"Не удалось переименовать файл {file_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Многопоточный загрузчик логов в memcached")
    parser.add_argument("--pattern", required=True, help="Паттерн для поиска файлов (например, /path/*.tsv.gz)")
    parser.add_argument("--dry", action="store_true", help="Сухой прогон без записи в memcached")
    parser.add_argument("--workers", type=int, default=None, help="Количество рабочих потоков")
    parser.add_argument("--test", action="store_true", help="Режим тестирования")

    # Адреса серверов
    for device_type, default_addr in SUPPORTED_DEVICE_TYPES.items():
        parser.add_argument(f"--{device_type}", default=default_addr, help=f"Адрес memcached для {device_type}")

    options = parser.parse_args()

    if options.workers is None:
        import multiprocessing
        options.workers = multiprocessing.cpu_count() * 2

    logger.info(f"Memc loader started with options: {vars(options)}")

    try:
        # Настройка подключений
        server_connections = setup_memcached_connections(options)

        # Получаем список файлов в хронологическом порядке
        files = get_sorted_files(options.pattern)

        if not files:
            logger.warning(f"Файлы по паттерну {options.pattern} не найдены")
            return 0

        logger.info(f"Найдено {len(files)} файлов для обработки")

        # Обрабатываем файлы последовательно
        success_count = 0
        start_time = time.time()

        for file_path in files:
            logger.info(f"Обработка {file_path}")

            if process_file(file_path, server_connections, options.dry):
                if not options.dry:
                    if rename_processed_file(file_path):
                        success_count += 1
                else:
                    success_count += 1
            else:
                logger.error(f"Не удалось обработать файл {file_path}")

        total_time = time.time() - start_time
        logger.info(f"Обработка завершена: {success_count}/{len(files)} файлов за {total_time:.2f} сек")

        return 0 if success_count == len(files) else 1

    except KeyboardInterrupt:
        logger.info("Прервано пользователем")
        return 1
    except Exception as e:
        logger.exception(f"Неожиданная ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())