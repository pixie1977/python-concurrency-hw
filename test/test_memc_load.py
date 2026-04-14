#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тесты для memc_load.py
"""

import os
import sys
import unittest

from app.memc_load import parse_line, PhoneLog

# Добавляем путь к модулю
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))



class TestMemcLoad(unittest.TestCase):

    def test_parse_line_valid_idfa(self):
        """Тест парсинга корректной строки idfa"""
        line = "idfa\te7e1a50c0ec2747ca56cd9e1558c0d7c\t67.7835424444\t-22.8044005471\t7942,8519,4232"
        result = parse_line(line)

        self.assertIsNotNone(result)
        device_type, device_id, lat, lon, apps = result

        self.assertEqual(device_type, 'idfa')
        self.assertEqual(device_id, 'e7e1a50c0ec2747ca56cd9e1558c0d7c')
        self.assertAlmostEqual(lat, 67.7835424444)
        self.assertAlmostEqual(lon, -22.8044005471)
        self.assertEqual(apps, [7942, 8519, 4232])

    def test_parse_line_valid_gaid(self):
        """Тест парсинга корректной строки gaid"""
        line = "gaid\t3261cf44cbe6a00839c574336fdf49f6\t137.790839567\t56.8403675248\t7462,1115,5205"
        result = parse_line(line)

        self.assertIsNotNone(result)
        device_type, device_id, lat, lon, apps = result

        self.assertEqual(device_type, 'gaid')
        self.assertEqual(device_id, '3261cf44cbe6a00839c574336fdf49f6')
        self.assertAlmostEqual(lat, 137.790839567)
        self.assertAlmostEqual(lon, 56.8403675248)
        self.assertEqual(apps, [7462, 1115, 5205])

    def test_parse_line_invalid_device_type(self):
        """Тест парсинга строки с неизвестным типом устройства"""
        line = "unknown\tdevice123\t1.0\t2.0\t1,2,3"
        result = parse_line(line)
        self.assertIsNone(result)

    def test_parse_line_invalid_format(self):
        """Тест парсинга строки с неправильным форматом"""
        line = "idfa\tinvalid"
        result = parse_line(line)
        self.assertIsNone(result)

    def test_parse_line_invalid_numbers(self):
        """Тест парсинга строки с некорректными числами"""
        line = "idfa\td123\tinvalid\t-22.8\t7942,8519"
        result = parse_line(line)
        self.assertIsNone(result)

    def test_phone_log_serialize(self):
        """Тест сериализации PhoneLog"""
        phone_log = PhoneLog(lat=67.78, lon=-22.80, apps=[7942, 8519])
        serialized = phone_log.serialize()

        decoded = serialized.decode('utf-8')
        parts = decoded.split('|')

        self.assertIn('lat:67.78', parts)
        self.assertIn('lon:-22.8', parts)
        self.assertIn('apps:7942', parts)
        self.assertIn('apps:8519', parts)

    def test_phone_log_serialize_without_coords(self):
        """Тест сериализации PhoneLog без координат"""
        phone_log = PhoneLog(apps=[7942, 8519])
        serialized = phone_log.serialize()

        decoded = serialized.decode('utf-8')
        parts = decoded.split('|')

        self.assertNotIn('lat', decoded)
        self.assertNotIn('lon', decoded)
        self.assertEqual(len(parts), 2)

if __name__ == '__main__':
    unittest.main()