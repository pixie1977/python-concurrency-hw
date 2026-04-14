#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для проверки путей и прав доступа
"""

import os
import sys
from pathlib import Path

def check_paths():
    """Проверяет пути и права доступа"""
    print("=== Проверка путей и прав доступа ===")
    print(f"Текущая директория: {os.getcwd()}")
    print(f"Путь к скрипту: {__file__}")
    print(f"Python path: {sys.path}")

    # Проверяем различные возможные директории для тестовых данных
    possible_dirs = [
        "./test_data",
        "../test_data",
        "test_data",
        "./test/test_data",
        "../test/test_data"
    ]

    for dir_path in possible_dirs:
        abs_path = os.path.abspath(dir_path)
        print(f"\nПроверка директории: {dir_path}")
        print(f"  Абсолютный путь: {abs_path}")

        exists = os.path.exists(abs_path)
        print(f"  Существует: {exists}")

        if exists:
            is_dir = os.path.isdir(abs_path)
            print(f"  Это директория: {is_dir}")

            writable = os.access(abs_path, os.W_OK)
            print(f"  Доступна для записи: {writable}")

            # Попробуем создать временный файл для проверки
            test_file = os.path.join(abs_path, "test_write.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print(f"  Можно записать файл: Да")
            except Exception as e:
                print(f"  Можно записать файл: Нет ({e})")
        else:
            # Попробуем создать директорию
            try:
                os.makedirs(abs_path, exist_ok=True)
                print(f"  Можно создать: Да")

                # Проверим, можно ли в нее писать
                test_file = os.path.join(abs_path, "test_write.tmp")
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    print(f"  Можно записать файл: Да")
                except Exception as e:
                    print(f"  Можно записать файл: Нет ({e})")

            except Exception as e:
                print(f"  Можно создать: Нет ({e})")

if __name__ == "__main__":
    check_paths()