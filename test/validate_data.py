#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Валидатор тестовых данных для memc_load.py

Проверяет сгенерированные TSV.gz файлы на соответствие формату.
"""

import argparse
import gzip
import os
import re
from collections import defaultdict

def validate_device_id(device_type, device_id):
    """Проверяет формат идентификатора устройства."""
    patterns = {
        'idfa': r'^[0-9a-f]{32}$',
        'gaid': r'^[0-9a-f]{32}$',
        'adid': r'^[0-9a-f]{16}$',
        'dvid': r'^[a-z0-9]{10}$'
    }

    if device_type not in patterns:
        return False

    pattern = re.compile(patterns[device_type])
    return bool(pattern.match(device_id))

def validate_coordinate(coord_str, min_val, max_val):
    """Проверяет корректность координаты."""
    try:
        coord = float(coord_str)
        return min_val <= coord <= max_val
    except (ValueError, TypeError):
        return False

def validate_apps_list(apps_str):
    """Проверяет список приложений."""
    if not apps_str or not apps_str.strip():
        return False

    apps = apps_str.strip().split(',')
    if len(apps) < 1:
        return False

    try:
        app_ids = [int(app) for app in apps]
        # Проверяем, что все ID в разумном диапазоне
        return all(1 <= app_id <= 99999 for app_id in app_ids)
    except ValueError:
        return False

def validate_line(line, line_number):
    """Валидирует одну строку данных."""
    parts = line.strip().split('\t')

    if len(parts) != 5:
        return False, f"Неверное количество полей: {len(parts)} вместо 5"

    device_type, device_id, lat_str, lon_str, apps_str = parts

    # Проверка типа устройства
    if device_type not in ['idfa', 'gaid', 'adid', 'dvid']:
        return False, f"Неизвестный тип устройства: {device_type}"

    # Проверка идентификатора
    if not validate_device_id(device_type, device_id):
        return False, f"Некорректный формат ID для {device_type}: {device_id}"

    # Проверка координат
    if not validate_coordinate(lat_str, -90.0, 90.0):
        return False, f"Некорректная широта: {lat_str}"

    if not validate_coordinate(lon_str, -180.0, 180.0):
        return False, f"Некорректная долгота: {lon_str}"

    # Проверка списка приложений
    if not validate_apps_list(apps_str):
        return False, f"Некорректный список приложений: {apps_str}"

    return True, "OK"

def analyze_file(filepath):
    """Анализирует файл и возвращает статистику."""
    stats = defaultdict(int)
    line_count = 0
    valid_count = 0
    errors = []

    try:
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line_count += 1

                if not line.strip():
                    continue

                is_valid, message = validate_line(line, line_num)

                if is_valid:
                    parts = line.strip().split('\t')
                    device_type = parts[0]
                    stats[f'total'] += 1
                    stats[f'device_{device_type}'] += 1
                    valid_count += 1
                else:
                    errors.append(f"Строка {line_num}: {message}")

        stats['valid_rate'] = valid_count / line_count if line_count > 0 else 0
        stats['file_size'] = os.path.getsize(filepath)

    except Exception as e:
        errors.append(f"Ошибка при чтении файла: {e}")

    return dict(stats), errors

def main():
    parser = argparse.ArgumentParser(description="Валидатор тестовых данных для memc_load.py")
    parser.add_argument("pattern", help="Паттерн для поиска файлов (например, ./test_data/*.tsv.gz)")

    args = parser.parse_args()

    import glob
    files = sorted(glob.glob(args.pattern))

    if not files:
        print(f"Файлы по паттерну '{args.pattern}' не найдены")
        return 1

    total_stats = defaultdict(int)
    all_errors = []

    print(f"Проверка {len(files)} файлов:")
    print("=" * 80)

    for filepath in files:
        print(f"\nФайл: {os.path.basename(filepath)}")
        print("-" * 40)

        stats, errors = analyze_file(filepath)

        if errors:
            print("Ошибки:")
            for error in errors[:10]:  # Показываем первые 10 ошибок
                print(f"  {error}")
            if len(errors) > 10:
                print(f"  ... и еще {len(errors) - 10} ошибок")
        else:
            print("Ошибок не обнаружено")

        # Выводим статистику
        print(f"Строк всего: {stats.get('total', 0)}")
        print(f"Успешно валидировано: {int(stats.get('valid_rate', 0) * stats.get('total', 0))}")
        print(f"Процент валидных: {stats.get('valid_rate', 0):.1%}")
        print(f"Размер файла: {stats.get('file_size', 0):,} байт")

        for key, value in sorted(stats.items()):
            if key.startswith('device_'):
                device_type = key.replace('device_', '')
                print(f"  {device_type.upper()}: {value}")

        # Обновляем общую статистику
        for key, value in stats.items():
            total_stats[key] += value if isinstance(value, int) else 0

    # Итоговая статистика
    if len(files) > 1:
        print("\n" + "=" * 80)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 80)
        print(f"Файлов проверено: {len(files)}")
        print(f"Всего строк: {total_stats.get('total', 0):,}")

        valid_total = 0
        for key, value in total_stats.items():
            if key.startswith('device_'):
                print(f"{key.replace('device_', '').upper()}: {value:,}")
                valid_total += value

        if total_stats.get('total', 0) > 0:
            overall_valid_rate = valid_total / total_stats['total']
            print(f"Общий процент валидных записей: {overall_valid_rate:.1%}")

    return 0 if not all_errors else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())