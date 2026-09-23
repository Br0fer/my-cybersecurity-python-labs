# Імпорт системних модулів для налаштування середовища пошуку бібліотек
import os
import sys

# Динамічне додавання кореневої директорії репозиторію до sys.path для імпорту модуля shared
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Крок 1: Імпорт персональних даних студента з модуля shared/student.py
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

# Крок 1: Вхідні дані — словник користувачів із атрибутами доступу (роль, числовий допуск, відділ, статус)
users = {
    "devsecops_lead": {
        "role": "devsecops",
        "clearance": 4,
        "department": "DevSecOps",
        "active": True,
    },
    "security_engineer": {
        "role": "security_engineer",
        "clearance": 3,
        "department": "Security Engineering",
        "active": True,
    },
    "automation_tech": {
        "role": "automation",
        "clearance": 2,
        "department": "Automation",
        "active": True,
    },
    "api_developer": {
        "role": "api_developer",
        "clearance": 2,
        "department": "API",
        "active": True,
    },
    "sandbox_env": {
        "role": "sandbox",
        "clearance": 1,
        "department": "Testing",
        "active": False,
    },
}

# Крок 1: Список кортежів захищених ресурсів системи та їхніх мінімальних рівнів безпеки (1-4)
resources = [
    ("security_pipelines", 4),
    ("secure_coding_standards", 3),
    ("automation_scripts", 2),
    ("api_specifications", 2),
    ("threat_models", 4),
    ("testing_frameworks", 1),
    ("security_gates", 3),
    ("vulnerability_scans", 4),
    ("integration_tests", 2),
    ("mock_services", 1),
]

# Крок 1: Текстові позначення рівнів безпеки (від 1 до 4) у вигляді незмінного кортежу
security_levels = ("Sandbox", "Development", "Secure", "Production Critical")
# Крок 1: Множина заблокованих облікових записів для перевірки входження за O(1)
blocked_users = {"sandbox_env", "pipeline_breach", "automation_fail"}


# Крок 3: Алгоритм багаторівневої перевірки прав доступу користувача до ресурсу
def check_access(username: str, resource_level: int) -> str:
    # 1. Перевірка наявності користувача в системній базі
    if username not in users:
        return "DENY (User not found)"

    # 2. Перевірка на присутність у списку блокування (скомпрометовані акаунти)
    if username in blocked_users:
        return "DENY (User is blocked)"

    user_info = users[username]

    # 3. Перевірка прапорця активності облікового запису
    if not user_info.get("active", False):
        return "DENY (Account inactive)"

    # 4. Порівняння рівня допуску (clearance) із рівнем безпеки цільового ресурсу
    if user_info.get("clearance", 0) >= resource_level:  # ty: ignore[unsupported-operator]
        return "ALLOW"
    else:
        return "DENY (Insufficient clearance)"


# Крок 8: Головна функція запуску та форматованого виведення результатів
def main():
    print(f"Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER} | Група: {GROUP_NAME}")
    print("Список доступних ресурсів:")
    print("№ | Ресурс | Рівень безпеки")

    # Крок 2: Виведення списку ресурсів із перетворенням числового рівня на текстовий
    for idx, (res_name, sec_num) in enumerate(resources, start=1):
        level_title = security_levels[sec_num - 1]
        print(f"{idx:<3} | {res_name:<26} | {sec_num} ({level_title})")

    print("\n")
    print("Результати перевірки доступу:")

    # Крок 4: Перевірка кожної пари «користувач-ресурс» та виведення логу доступу
    for username in users:
        for res_name, res_level in resources:
            decision = check_access(username, res_level)
            print(f"user={username}   resource={res_name:}   ->   {decision}")


# Точка входу в програму
if __name__ == "__main__":
    main()
