import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

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

security_levels = ("Sandbox", "Development", "Secure", "Production Critical")
blocked_users = {"sandbox_env", "pipeline_breach", "automation_fail"}




def check_access(username: str, resource_level: int) -> str:
    if username not in users:
        return "DENY (User not found)"

    if username in blocked_users:
        return "DENY (User is blocked)"

    user_info = users[username]

    if not user_info.get("active", False):
        return "DENY (Account inactive)"

    if user_info.get("clearance", 0) >= resource_level:  # ty: ignore[unsupported-operator]
        return "ALLOW"
    else:
        return "DENY (Insufficient clearance)"




def main():
    print(f"Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER} | Група: {GROUP_NAME}")
    print("Список доступних ресурсів:")
    print(f"№ | Ресурс | Рівень безпеки")

    for idx, (res_name, sec_num) in enumerate(resources, start=1):
        level_title = security_levels[sec_num - 1]
        print(f"{idx:<3} | {res_name:<26} | {sec_num} ({level_title})")

    print("\n")
    print("Результати перевірки доступу:")

    for username in users:
        for res_name, res_level in resources:
            decision = check_access(username, res_level)
            print(f"user={username}   resource={res_name:}   ->   {decision}")

if __name__ == "__main__":
    main()
