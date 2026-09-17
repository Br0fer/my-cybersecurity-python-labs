import os
import random
import string
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

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

criteria = {
    "min_length": 9,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

forbidden_passwords = {
    "easy123",
    "observer",
    "viewer",
    "monitor",
    "watcher",
    "admin",
}

random_indices = [random.randint(0, len(passwords) - 1) for _ in range(3)]
duplicated_passwords = [passwords[idx] for idx in random_indices]
passwords.extend(duplicated_passwords)



def evaluate_password(pwd: str, crit: dict, forbidden: set) -> str:
    min_len = crit["min_length"]

    if pwd in forbidden or len(pwd) < min_len:
        return "Заборонений"

    has_digit = any(c.isdigit() for c in pwd)
    has_upper = any(c.isupper() for c in pwd)
    has_lower = any(c.islower() for c in pwd)
    has_special = any(c in string.punctuation for c in pwd)

    all_criteria_met = has_digit and has_upper and has_special

    if all_criteria_met and len(pwd) >= (min_len + 4):
        return "Дуже сильний"

    if all_criteria_met and len(pwd) < (min_len + 4):
        return "Сильний"

    if all_criteria_met and len(pwd) >= (min_len + 4):
        return "Сильний"

    matched_groups = sum([has_digit, has_upper, has_special, has_lower])
    if matched_groups >= 2:
        return "Середній"

    return "Слабкий"


def main():
    print(f"Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER} | Група: {GROUP_NAME}\n")
    print(f"№ | Пароль | Довжина | Статус")


    for idx, pwd in enumerate(passwords, start=1):
        status = evaluate_password(pwd, criteria, forbidden_passwords)
        print(f"{idx} | {pwd} | {len(pwd)} | {status}")

if __name__ == "__main__":
    main()
