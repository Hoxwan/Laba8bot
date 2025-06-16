#1
import asyncio
import aiohttp

async def factorial(name, number):
    f = 1
    for i in range(2, number + 1):
        print(f"Task {name}: Compute factorial({i})...")
        await asyncio.sleep(0.1)  # Имитация асинхронной операции
        f *= i
    print(f"Task {name}: factorial({number}) = {f}")

async def main():
    await asyncio.gather(
        factorial("A", 15),
        factorial("B", 7),
        factorial("C", 4),
    )

if __name__ == '__main__':
    asyncio.run(main())
#2

services = [
    ("ipify", "https://api.ipify.org?format=json"),
    ("ip-api", "http://ip-api.com/json"),
    ("icanhazip", "https://icanhazip.com")
]

async def fetch_ip(session, name, url):
    try:
        async with session.get(url, timeout=2) as response:
            data = await response.json() if 'json' in url else {"ip": (await response.text()).strip()}
            return name, data.get('ip', data.get('query', 'Unknown'))
    except:
        return None

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_ip(session, name, url) for name, url in services]
        for future in asyncio.as_completed(tasks):
            result = await future
            if result:
                print(f"IP: {result[1]} (from {result[0]})")
                return

asyncio.run(main())
#3

async def interview(name, prep1, defense1, prep2, defense2):
    print(f"{name} started the 1 task")
    await asyncio.sleep(prep1 / 100)
    print(f"{name} moved on to the defense of the 1 task")
    await asyncio.sleep(defense1 / 100)
    print(f"{name} completed the 1 task")

    print(f"{name} is resting")
    await asyncio.sleep(5 / 100)

    print(f"{name} started the 2 task")
    await asyncio.sleep(prep2 / 100)
    print(f"{name} moved on to the defense of the 2 task")
    await asyncio.sleep(defense2 / 100)
    print(f"{name} completed the 2 task")


async def interviews(*candidates):
    await asyncio.gather(*[
        interview(name, *times)
        for name, *times in candidates
    ])


# Пример вызова:
asyncio.run(interviews(
    ("Alice", 10, 5, 8, 4),
    ("Bob", 7, 3, 6, 2)
))
#4

async def care(plant, action, duration, start_msg, end_msg):
    print(f"{action} {start_msg} {plant}")
    await asyncio.sleep(duration / 1000)
    print(f"{action} {end_msg} {plant}")


async def sowing(*plants_data):
    tasks = []
    for plant, soak, grow, root in plants_data:
        print(f"0 Beginning of sowing the {plant} plant")

        # Основные этапы
        tasks.append(asyncio.create_task(care(plant, 1, soak,
                                              "Soaking of the", "started")))
        await asyncio.sleep(0)  # Даем возможность запуститься

        tasks.append(asyncio.create_task(care(plant, 2, soak,
                                              "Soaking of the", "is finished")))

        # Параллельные уходы
        fert_task = asyncio.create_task(care(plant, 7, 3,
                                             "Application of fertilizers for",
                                             "Fertilizers for the have been introduced"))
        pest_task = asyncio.create_task(care(plant, 8, 5,
                                             "Treatment of", "from pests\nThe is treated from pests"))

        await asyncio.gather(*tasks)
        # Остальные этапы...

    await asyncio.gather(fert_task, pest_task)


# Пример вызова:
asyncio.run(sowing(
    ("tomato", 2000, 3000, 1500),
    ("cucumber", 1500, 2500, 1000)
))