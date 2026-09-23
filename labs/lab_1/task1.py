# Імпорт стандартних бібліотек: для роботи з файловою системою, псевдовипадковими числами, наборами символів та середовищем
import os
import random
import string
import sys

# Динамічне додавання кореня репозиторію до sys.path для імпорту спільних модулів
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Крок 1: Імпорт персональних даних студента з модуля shared/student.py
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

# Крок 2: Вихідний пул паролів відповідно до Варіанта 12
passwords = [
    "SIEM@An4lysis",
    "easy123",
    "S0C@Analyst",
    "observer",
    "Threat@Hunt1ng",
    "viewer",
    "Incid3nt@Handle",
    "monitor",
    "Log@An4lysis",
    "watcher",
]

# Крок 2: Словник обов'язкових критеріїв безпеки для варіанта
criteria = {
    "min_length": 9,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

# Крок 2: Множина заборонених паролів (використано set для пошуку за O(1))
forbidden_passwords = {
    "easy123",
    "observer",
    "viewer",
    "monitor",
    "watcher",
    "admin",
}

# Крок 3: Генерація 3 випадкових індексів та симуляція повторного використання паролів
random_indices = [random.randint(0, len(passwords) - 1) for _ in range(3)]
duplicated_passwords = [passwords[idx] for idx in random_indices]
passwords.extend(duplicated_passwords)


# Крок 4: Алгоритм оцінки стійкості пароля за каскадною схемою
def evaluate_password(pwd: str, crit: dict, forbidden: set) -> str:
    min_len = crit["min_length"]

    # 1. Заборонений: знайдено в forbidden_passwords або довжина менша за min_length
    if pwd in forbidden or len(pwd) < min_len:
        return "Заборонений"

    # Перевірка наявності різних категорій символів за допомогою генераторів
    has_digit = any(c.isdigit() for c in pwd)
    has_upper = any(c.isupper() for c in pwd)
    has_lower = any(c.islower() for c in pwd)
    has_special = any(c in string.punctuation for c in pwd)

    # Перевірка виконання всіх обов'язкових вимог безпеки варіанта
    all_criteria_met = has_digit and has_upper and has_special and has_lower

    # 5. Дуже сильний: виконано всі критерії та довжина >= min_length + 4 символів
    if all_criteria_met and len(pwd) >= (min_len + 4):
        return "Дуже сильний"

    # 4. Сильний: виконано всі критерії, але довжина менша за min_length + 4
    if all_criteria_met and len(pwd) < (min_len + 4):
        return "Сильний"

    # 3. Середній: довжина валідна та виконано 2 або більше критеріїв безпеки
    matched_groups = sum([has_digit, has_upper, has_special, has_lower])
    if matched_groups >= 2:
        return "Середній"

    # 2. Слабкий: пароль не заборонений, але задовольняє мінімальну кількість умов
    if (has_digit or has_upper or has_special or has_lower):
        return "Слабкий"


# Крок 5: Головна функція запуску з формуванням структурованої таблиці результатів
def main():
    print(f"Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER} | Група: {GROUP_NAME}\n")
    print("№ | Пароль | Довжина | Статус")

    # Ітерація списком паролів з нумерацією рядків за допомогою enumerate
    for idx, pwd in enumerate(passwords, start=1):
        status = evaluate_password(pwd, criteria, forbidden_passwords)
        print(f"{idx} | {pwd} | {len(pwd)} | {status}")


# Точка входу в програму для запобігання виконанню при імпорті в main.py
if __name__ == "__main__":
    main()
