# check_cache.py
import memcache

# Подключаемся к одному из серверов
mc = memcache.Client(['127.0.0.1:33013'])

# Получаем статистику
stats = mc.get_stats()
print("Статистика memcached:")
for server, stats_dict in stats:
    print(f"{server}:")
    for key, value in list(stats_dict.items())[:10]:  # первые 10 параметров
        print(f"  {key}: {value}")

# Можно получить несколько ключей, если есть ID из логов
# keys = ["idfa:some_id", "gaid:some_id"]
# values = mc.get_multi(keys)
# print(f"Получено значений: {len(values)}")