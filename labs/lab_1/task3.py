# Імпорт стандартних бібліотек для роботи з CSV, системними шляхами, хешуванням, JSON та часом
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

# Динамічне додавання кореневої директорії проєкту до sys.path для коректного імпорту спільних модулів
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
# Крок 1: Імпорт персональних даних студента з модуля shared/student.py
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

# Параметри варіанта: мінімальна довжина пароля та персональна сіль (варіант, доповнений нулями зліва до 5 знаків)
MIN_PASSWORD_LENGTH = 8
SALT = str(VARIANT_NUMBER).zfill(5)

# Визначення шляхів до директорії даних та файлів бази користувачів і журналу логів
DATA_DIR = os.path.join("labs", "lab_1", "data")
CSV_PATH = os.path.join(DATA_DIR, "users.csv")
LOG_PATH = os.path.join(DATA_DIR, "log.json")


# Крок 1: Власний клас винятку для перевірки валідності довжини пароля
class ValidationError(Exception):
    pass


# Крок 1: Функція хешування за алгоритмом MD5 з валідацією вхідних даних та конкатенацією солі
def generate_hash(password: str, salt: str = "00000") -> str:
    # Перевірка на непорожність переданих значень
    if not password or not salt:
        raise ValueError("Пароль і сіль не можуть бути порожніми")

    # Перевірка на відповідність мінімальній дозволеній довжині
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль повинен бути не менше {MIN_PASSWORD_LENGTH} символів"
        )

    # Конкатенація пароля та солі
    combined = password + salt

    # Генерація шістнадцяткового значення MD5-хешу
    return hashlib.md5(combined.encode("utf-8")).hexdigest()


# Крок 6: Декоратор для автоматичного логування спроб входу у файл log.json
def log_event(func):
    def wrapper(*args, **kwargs):
        # Визначення імені користувача з іменованих або позиційних аргументів
        username = kwargs.get("username") or (args[0] if len(args) > 0 else None)
        status = "failure"

        # Виконання цільової функції та фіксація успішного чи неуспішного статусу
        try:
            result = func(*args, **kwargs)
            if result:
                status = "success"
            return result
        except Exception:
            status = "failure"
            raise
        finally:
            # Формування запису події відповідно до вимог формату
            log_entry = {
                "event": "login",
                "username": username,
                "result": status,
                "timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "args": list(args),
                "kwargs": kwargs,
            }

            # Запис події у JSON-файл із захистом структури масиву та створенням папки
            try:
                os.makedirs(DATA_DIR, exist_ok=True)
                logs = []
                if os.path.exists(LOG_PATH):
                    with open(LOG_PATH, "r", encoding="utf-8") as logf:
                        try:
                            logs = json.load(logf)
                            if not isinstance(logs, list):
                                logs = []
                        except json.JSONDecodeError:
                            logs = []
                logs.append(log_entry)

                with open(LOG_PATH, "w", encoding="utf-8") as logf:
                    json.dump(logs, logf, ensure_ascii=False, indent=4)
            except (OSError, PermissionError) as e:
                print(f"Помилка запису логу: {e}")

    return wrapper


# Крок 3.1: Функція створення кортежу облікового запису (логін, хеш_пароля) з персональною сіллю
def create_user(username: str, password: str) -> tuple:
    hash_value = generate_hash(password, salt=SALT)
    return (username, hash_value)


# Крок 3.2: Функція збереження списку користувачів у файл формату CSV із гарантованим створенням каталогу
def create_users(users_list: tuple):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CSV_PATH, "w", encoding="utf-8") as csvf:
        writer = csv.writer(csvf)
        for username, password in users_list:
            user_entry = create_user(username, password)
            writer.writerow(user_entry)


# Крок 4: Функція читання створеної бази даних користувачів із CSV-файлу
def read_users_db() -> list:
    users_db = []
    with open(CSV_PATH, "r", encoding="utf-8") as csvf:
        reader = csv.reader(csvf)
        for row in reader:
            if row:
                users_db.append(tuple(row))
    return users_db


# Крок 5: Функція автентифікації користувача з перевіркою хешу та підключеним логуванням через декоратор
@log_event
def login(username: str, password: str, users_db: list) -> bool:
    if not username or not password:
        raise ValueError("Логін і пароль не можуть бути порожніми")

    input_hash = generate_hash(password, salt=SALT)
    for db_user, db_hash in users_db:
        if db_user == username and db_hash == input_hash:
            return True
    return False


# Крок 8: Головна керуюча функція для виконання сценарію тестування
def main():
    print(f"Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER} | Група: {GROUP_NAME}")
    print("\n")

    # Крок 3: Створення вихідного кортежу з 10 користувачами
    users_to_register = (
        ("devsecops_lead", "SecurePass2026!"),
        ("security_engineer", "ThreatHunting#1"),
        ("automation_tech", "ScriptMaster99"),
        ("api_developer", "EndpointSecure1"),
        ("soc_analyst", "AlertTriaging2"),
        ("incident_handler", "ForensicReady8"),
        ("log_auditor", "AuditCompliance4"),
        ("cloud_architect", "CloudFortress#9"),
        ("pentester_red", "ExploitPayload7"),
        ("network_guard", "FirewallRuleSet5"),
    )

    # Крок 7: Комплексна обробка винятків під час роботи з файлами та автентифікації
    try:
        # Створення бази та запис у CSV-файл
        create_users(users_to_register)

        # Зчитування та виведення бази у консоль
        users_db = read_users_db()
        print("База даних користувачів(users.csv):\n")

        for index, (u, h) in enumerate(users_db, start=1):
            print(f"{index} | {u} | {h}")

        # Сценарії перевірки процедури автентифікації
        print("\nТестування автентифікації:")

        # 1. Успішна автентифікація з правильними обліковими даними
        res_true = login(
            username="devsecops_lead",
            password="SecurePass2026!",
            users_db=users_db,
        )
        print(f"Вхід devsecops_lead: {'УСПІШНО' if res_true else 'ВІДХИЛЕНО'}")

        # 2. Невдала спроба входу з некоректним паролем
        res_false = login(
            username="api_developer",
            password="WrongPassword123",
            users_db=users_db,
        )
        print(f"Вхід api_developer: {'УСПІШНО' if res_false else 'ВІДХИЛЕНО'}\n")

        # 3. Перехоплення власного винятку валідації пароля через малу довжину
        try:
            print("Перевірка username: soc_analyst, password: 123")
            login(username="soc_analyst", password="123", users_db=users_db)
        except ValidationError as ve:
            print(f"Перехоплено ValidationError: {ve}")

        # 4. Перехоплення винятку при передачі порожніх значень
        try:
            print("Перевірка username: , password: ")
            login(username="", password="", users_db=users_db)
        except ValueError as ve:
            print(f"Перехоплено ValueError: {ve}")

    # Обробка стандартних винятків роботи з файловою системою та потоками введення/виведення
    except FileNotFoundError as e:
        print(f"[Помилка] Файл не знайдено: {e}")
    except PermissionError as e:
        print(f"[Помилка] Недостатньо прав доступу: {e}")
    except OSError as e:
        print(f"[Помилка] Збій операції введення/виведення: {e}")


# Точка входу в програму
if __name__ == "__main__":
    main()
