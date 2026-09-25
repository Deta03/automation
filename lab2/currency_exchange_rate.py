import sys
import requests
import json
import os

# Адрес нашего API
url = "http://localhost:8080/"

# Проверяем количество параметров
if len(sys.argv) != 5:
    print("Usage: python3 currency_exchange_rate.py FROM TO DATE API_KEY")
    sys.exit(1)

# Получаем параметры из командной строки
from_currency = sys.argv[1].upper()
to_currency = sys.argv[2].upper()
date = sys.argv[3]
api_key = sys.argv[4]

try:
    # Отправляем запрос к API
    response = requests.post(
        url,
        params={
            "from": from_currency,
            "to": to_currency,
            "date": date
        },
        data={
            "key": api_key
        }
    )

    # Получаем JSON
    result = response.json()

    # Проверяем ошибку API
    if result["error"] != "":
        print("Error:", result["error"])

        with open("error.log", "a") as file:
            file.write(result["error"] + "\n")

        sys.exit(1)

    # Создаём папку data
    os.makedirs("../data", exist_ok=True)

    # Создаём имя файла
    filename = f"../data/{from_currency}_{to_currency}_{date}.json"

    # Сохраняем результат
    with open(filename, "w") as file:
        json.dump(result, file, indent=4)

    print("Data saved to:", filename)

except requests.exceptions.RequestException as error:
    print("Request error:", error)

    with open("error.log", "a") as file:
        file.write(str(error) + "\n")

except Exception as error:
    print("Error:", error)

    with open("error.log", "a") as file:
        file.write(str(error) + "\n")
