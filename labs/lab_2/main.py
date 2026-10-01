# Імпорт стандартних бібліотек: розбір аргументів командного рядка, робота з часом і шляхами
import argparse
import sys
from datetime import timedelta
from pathlib import Path

from labs.lab_2.task1 import SESSION_TIMEOUT_SEC, Admin, User, UserAccount
from labs.lab_2.task2 import run_analysis
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

# Каталог із вхідними файлами варіанта (поруч із цим модулем)
DATA_DIR = Path(__file__).resolve().parent / "data"


# Крок 7: Сценарій демонстрації класів Завдання 1
def run_demo() -> int:
    print(
        f"Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER} | Група: {GROUP_NAME}\n"
    )

    # Навчальні облікові дані, що існують лише в межах демонстрації
    user = User("analyst", "soc_analyst@example.com", "S0C@Analyst2026")
    account = UserAccount(user)

    print("--- 1. Створення користувача ---")
    print(user)

    print("\n--- 2. Невдалий та успішний вхід ---")
    print(
        "Вхід із хибним паролем:",
        account.login("analyst", "wrong-password", "192.168.1.10"),
    )
    print("Автентифіковано:", account.is_authenticated())
    print(
        "Вхід із правильним паролем:",
        account.login("analyst", "S0C@Analyst2026", "192.168.1.10"),
    )
    print("Автентифіковано:", account.is_authenticated())
    print(account["session"])

    print("\n--- 3. Зміна email із валідацією ---")
    user.email = "new_analyst@example.org"
    print("Новий email:", user.email)
    for bad_email in ("1analyst@example.com", "ab@example.com", "analyst@localhost"):
        try:
            user.email = bad_email
        except ValueError as error:
            print("Відхилено:", error)
    print("Email після невдалих спроб:", user.email)

    print("\n--- 4. Права адміністратора ---")
    admin = Admin(
        "root_admin",
        "root_admin@example.com",
        "Adm1n@Secure#Pass",
        permissions={"read_logs"},
    )
    admin.grant_permission("manage_users")
    print(admin)
    print("Має право manage_users:", admin.has_permission("manage_users"))
    admin.revoke_permission("manage_users")
    print(
        "Має право manage_users після відкликання:",
        admin.has_permission("manage_users"),
    )
    print(admin)

    print("\n--- 5. Доступ через account[...] ---")
    print('account["user"]:', account["user"])
    for action in (
        lambda: account["password_hash"],
        lambda: account.__setitem__("user", "not a user"),
    ):
        try:
            action()
        except KeyError as error:
            print("KeyError:", error)
        except TypeError as error:
            print("TypeError:", error)

    print("\n--- 6. Завершення сеансу за таймаутом ---")
    # Імітація бездіяльності: час останньої активності зсувається в минуле замість реального очікування
    account["session"].last_activity -= timedelta(seconds=SESSION_TIMEOUT_SEC + 1)
    print(
        f"Автентифіковано після {SESSION_TIMEOUT_SEC + 1} с бездіяльності:",
        account.is_authenticated(),
    )

    print("\n--- 7. Вихід із системи ---")
    account.login("analyst", "S0C@Analyst2026", "192.168.1.10")
    print("Автентифіковано після повторного входу:", account.is_authenticated())
    account.logout()
    print("Автентифіковано після виходу:", account.is_authenticated())

    print("\n--- 8. Деактивований користувач ---")
    user.deactivate()
    print(
        "Вхід деактивованого користувача:",
        account.login("analyst", "S0C@Analyst2026", "192.168.1.10"),
    )

    print("\n--- 9. Журнал аудиту ---")
    account["audit_log"].show_all()
    return 0


# Опис інтерфейсу командного рядка: підкоманди demo та analyze
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m labs.lab_2.main",
        description="Лабораторна робота №2: модель користувача (demo) та аналізатор поштових заголовків (analyze)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("demo", help="демонстрація класів Завдання 1")

    analyze = subparsers.add_parser(
        "analyze", help="аналіз заголовків листів на ознаки фішингу (Завдання 2)"
    )
    # type=Path одразу перетворює аргумент на об'єкт шляху
    analyze.add_argument(
        "--mail-log",
        type=Path,
        default=DATA_DIR / "mail_headers.log",
        help="шлях до файлу з дампами заголовків листів",
    )
    analyze.add_argument(
        "--suspicious-keywords",
        type=Path,
        default=DATA_DIR / "suspicious_keywords.txt",
        help="шлях до словника стоп-слів (одна фраза в рядку)",
    )
    analyze.add_argument(
        "--out-csv",
        type=Path,
        default=DATA_DIR / "phishing_report.csv",
        help="шлях до CSV-файлу звіту",
    )
    analyze.add_argument(
        "--debug", action="store_true", help="докладне логування (рівень DEBUG)"
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "demo":
        return run_demo()
    return run_analysis(
        args.mail_log, args.suspicious_keywords, args.out_csv, args.debug
    )


# Точка входу в програму для запобігання виконанню при імпорті
if __name__ == "__main__":
    sys.exit(main())
