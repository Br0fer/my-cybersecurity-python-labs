# Імпорт стандартних бібліотек: хешування, порівняння за сталий час, випадкова сіль, регулярні вирази, дата й час
import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# Кількість ітерацій PBKDF2: що більше ітерацій, то дорожчий перебір паролів для зловмисника
PBKDF2_ITERATIONS = 600_000

# Довжина випадкової солі в байтах
SALT_SIZE = 16

# Час бездіяльності (у секундах), після якого сеанс вважається завершеним
SESSION_TIMEOUT_SEC = 900

# Спрощений формат email: локальна частина починається з латинської літери та має 3–64 символи
# (латинські літери, цифри, _), далі @ і доменне ім'я з принаймні однією крапкою
EMAIL_PATTERN = re.compile(
    r"[A-Za-z][A-Za-z0-9_]{2,63}@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+"
)

# Назви дій для журналу аудиту
ACTION_LOGIN_SUCCESS = "login_success"
ACTION_LOGIN_FAILURE = "login_failure"
ACTION_LOGOUT = "logout"


# Крок 2: Клас користувача з інкапсульованими хешем і сіллю пароля
class User:
    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user",
        active: bool = True,
    ):
        self.username = username
        # Присвоєння через property, тому email перевіряється вже під час створення об'єкта
        self.email = email
        self.role = role
        self.active = active
        # Приватні атрибути (name mangling): ззовні доступні лише як _User__password_hash / _User__password_salt
        self.__password_hash = b""
        self.__password_salt = b""
        self.set_password(password)

    # Читання email через property — ззовні виглядає як звичайний атрибут
    @property
    def email(self) -> str:
        return self.__email

    # Запис email із перевіркою формату; fullmatch вимагає збігу всього рядка
    @email.setter
    def email(self, value: str) -> None:
        if not isinstance(value, str) or not EMAIL_PATTERN.fullmatch(value):
            raise ValueError(f"Некоректний формат email: {value!r}")
        self.__email = value

    # Обчислення ключа PBKDF2-HMAC-SHA256 для пароля із заданою сіллю
    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
        )

    # Для кожного нового пароля генерується окрема випадкова сіль; сам пароль ніде не зберігається
    def set_password(self, password: str) -> None:
        if not isinstance(password, str) or not password:
            raise ValueError("Пароль має бути непорожнім рядком")
        self.__password_salt = os.urandom(SALT_SIZE)
        self.__password_hash = self._derive_key(password, self.__password_salt)

    # Перевірка пароля: compare_digest порівнює за сталий час і захищає від атак за часом виконання
    def check_password(self, password: str) -> bool:
        if not isinstance(password, str):
            return False
        candidate = self._derive_key(password, self.__password_salt)
        return hmac.compare_digest(candidate, self.__password_hash)

    # Деактивація облікового запису: такий користувач не може увійти в систему
    def deactivate(self) -> None:
        self.active = False

    # Текстове подання без пароля, хешу та солі
    def __str__(self) -> str:
        status = "активний" if self.active else "деактивований"
        return f"Користувач {self.username} <{self.email}> | роль: {self.role} | статус: {status}"


# Крок 3: Адміністратор — це користувач із додатковими правами (наслідування, зв'язок "Is-A")
class Admin(User):
    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        permissions: set[str] | None = None,
        active: bool = True,
    ):
        # Спільні атрибути ініціалізує батьківський клас
        super().__init__(username, email, password, role="admin", active=active)
        # Типове значення None замість set(): змінювана колекція в сигнатурі була б спільною для всіх об'єктів
        self.permissions: set[str] = (
            set(permissions) if permissions is not None else set()
        )

    def grant_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    # discard не кидає виняток, якщо такого дозволу немає
    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    # Перевизначення __str__: до опису користувача додається перелік прав
    def __str__(self) -> str:
        rights = ", ".join(sorted(self.permissions)) if self.permissions else "немає"
        return f"{super().__str__()} | права: {rights}"


# Крок 4: Сеанс користувача з часом UTC
class Session:
    def __init__(self, ip: str):
        self.ip = ip
        # Час із часовим поясом UTC, щоб уникнути неоднозначності локального часу
        self.login_time: datetime = datetime.now(timezone.utc)
        self.last_activity: datetime = self.login_time

    # Оновлення часу останньої активності
    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    # Сеанс активний, якщо від останньої активності минуло менше timeout_sec секунд
    def is_active(self, timeout_sec: int) -> bool:
        if timeout_sec <= 0:
            raise ValueError("timeout_sec має бути додатним числом")
        idle = datetime.now(timezone.utc) - self.last_activity
        return idle < timedelta(seconds=timeout_sec)

    def __str__(self) -> str:
        return (
            f"Сеанс з {self.ip} | вхід: {self.login_time:%Y-%m-%d %H:%M:%S} UTC | "
            f"остання активність: {self.last_activity:%Y-%m-%d %H:%M:%S} UTC"
        )


# Крок 5: Окремий запис журналу аудиту; frozen=True забороняє змінювати запис після створення
@dataclass(frozen=True)
class AuditRecord:
    timestamp: datetime
    username: str
    action: str


# Крок 5: Журнал аудиту зберігає записи у списку
class AuditLog:
    def __init__(self):
        self.records: list[AuditRecord] = []

    # Додавання події; пароль у журнал не передається й не записується
    def add_log(self, username: str, action: str) -> None:
        self.records.append(AuditRecord(datetime.now(timezone.utc), username, action))

    # Виведення всіх записів журналу
    def show_all(self) -> None:
        if not self.records:
            print("Журнал аудиту порожній")
            return
        for idx, record in enumerate(self.records, start=1):
            print(
                f"{idx} | {record.timestamp:%Y-%m-%d %H:%M:%S} UTC | {record.username} | {record.action}"
            )


# Крок 6: Обліковий запис об'єднує User, Session та AuditLog (композиція, зв'язок "Has-A")
class UserAccount:
    def __init__(self, user: User, audit_log: AuditLog | None = None):
        self.user = user
        # Сеансу немає, доки користувач успішно не увійде
        self.session: Session | None = None
        self.audit_log = audit_log if audit_log is not None else AuditLog()
        # Дозволені ключі для доступу через account["..."] та очікувані типи значень
        self._allowed_items = {
            "user": User,
            "session": (Session, type(None)),
            "audit_log": AuditLog,
        }

    # Вхід: перевіряються ім'я, активність користувача та пароль; сеанс створюється лише після успіху
    def login(self, username: str, password: str, ip: str) -> bool:
        if (
            username != self.user.username
            or not self.user.active
            or not self.user.check_password(password)
        ):
            self.audit_log.add_log(username, ACTION_LOGIN_FAILURE)
            return False

        self.session = Session(ip)
        self.session.touch()
        self.audit_log.add_log(username, ACTION_LOGIN_SUCCESS)
        return True

    # Перевірка автентифікації не викликає touch(), тому не подовжує сеанс
    def is_authenticated(self) -> bool:
        return self.session is not None and self.session.is_active(SESSION_TIMEOUT_SEC)

    # Вихід: сеанс завершується, подія фіксується в аудиті
    def logout(self) -> None:
        if self.session is None:
            return
        self.session = None
        self.audit_log.add_log(self.user.username, ACTION_LOGOUT)

    # Доступ за ключем лише до дозволених атрибутів; хеш і сіль пароля серед них відсутні
    def __getitem__(self, key: str):
        if key not in self._allowed_items:
            raise KeyError(key)
        return getattr(self, key)

    # Запис за ключем із перевіркою типу значення
    def __setitem__(self, key: str, value) -> None:
        if key not in self._allowed_items:
            raise KeyError(key)
        if not isinstance(value, self._allowed_items[key]):
            raise TypeError(
                f"Неправильний тип значення для ключа {key!r}: {type(value).__name__}"
            )
        setattr(self, key, value)
