# Імпорт стандартних бібліотек: CSV-звіт, логування, регулярні вирази, лічильники, класи даних і шляхи
import csv
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Рядок-роздільник між листами у файлі з дампами заголовків
MESSAGE_SEPARATOR = "--- MESSAGE ---"

# Рядок заголовка має вигляд "Назва: значення"
HEADER_PATTERN = re.compile(r"^([A-Za-z][A-Za-z-]*):\s*(.*)$")

# Адреса електронної пошти всередині значення заголовка; група 1 — домен
ADDRESS_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+)")

# Оцінка підозрілості вимірюється за шкалою від 0 до MAX_SCORE
MAX_SCORE = 100

# Вагові коефіцієнти індикаторів фішингу; максимальні внески в сумі дають MAX_SCORE
SCORE_REPLY_TO_MISMATCH = 30
SCORE_RETURN_PATH_MISMATCH = 25
SCORE_PER_KEYWORD = 10
MAX_KEYWORD_SCORE = 30
SCORE_PER_EXTRA_HOP = 5
MAX_HOP_SCORE = 15

# Найбільша кількість вузлів ретрансляції, яка ще вважається звичайною
MAX_NORMAL_HOPS = 3

# Рівні ризику: (мінімальна оцінка, назва для звіту, підпис для консолі), від найвищого до найнижчого
RISK_LEVELS = [
    (75, "critical", "КРИТИЧНИЙ РИЗИК"),
    (50, "high", "ВИСОКИЙ РИЗИК"),
    (25, "medium", "СЕРЕДНІЙ РИЗИК"),
    (0, "low", "НИЗЬКИЙ РИЗИК"),
]
RISK_LOW = "low"

# Колонки CSV-звіту
CSV_COLUMNS = [
    "message_id",
    "subject",
    "score",
    "risk_level",
    "keyword_matches",
    "relay_hops",
    "reasons",
]


# Помилка вхідних даних, яку утиліта показує користувачеві без traceback
class MailAnalysisError(Exception):
    pass


# Заголовки одного листа
@dataclass
class EmailMessage:
    message_id: str
    from_header: str
    return_path: str = ""
    reply_to: str = ""
    subject: str = ""
    # default_factory створює окремий список для кожного об'єкта
    received: list[str] = field(default_factory=list)


# Результат аналізу одного листа
@dataclass
class AnalysisResult:
    message: EmailMessage
    score: int
    risk_level: str
    keyword_matches: list[str]
    relay_hops: int
    reasons: list[str]


# Читання словника стоп-слів: по одній фразі в рядку, порожні рядки пропускаються
def load_keywords(path: Path) -> list[str]:
    keywords = [
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not keywords:
        raise MailAnalysisError(f"Словник стоп-слів порожній: {path}")
    logger.debug("Завантажено стоп-слів: %d", len(keywords))
    return keywords


# Розбір одного блоку заголовків; повертає None, якщо бракує обов'язкових заголовків
def parse_message_block(block: str, number: int) -> EmailMessage | None:
    headers: dict[str, str] = {}
    received: list[str] = []

    for line in block.splitlines():
        if not line.strip():
            continue
        match = HEADER_PATTERN.match(line.strip())
        if not match:
            logger.debug("Блок %d: рядок не схожий на заголовок: %r", number, line)
            continue
        # Назви заголовків нечутливі до регістру
        name, value = match.group(1).lower(), match.group(2).strip()
        # Заголовок Received повторюється для кожного вузла, тому збирається у список
        if name == "received":
            received.append(value)
        else:
            headers[name] = value

    if "message-id" not in headers or "from" not in headers:
        logger.warning(
            "Блок %d пропущено: відсутній заголовок Message-ID або From", number
        )
        return None

    return EmailMessage(
        message_id=headers["message-id"],
        from_header=headers["from"],
        return_path=headers.get("return-path", ""),
        reply_to=headers.get("reply-to", ""),
        subject=headers.get("subject", ""),
        received=received,
    )


# Читання файлу з дампами заголовків і поділ його на окремі листи
def parse_mail_log(path: Path) -> list[EmailMessage]:
    text = path.read_text(encoding="utf-8")
    messages = []
    for number, block in enumerate(text.split(MESSAGE_SEPARATOR), start=1):
        if not block.strip():
            continue
        message = parse_message_block(block, number)
        if message is not None:
            messages.append(message)

    if not messages:
        raise MailAnalysisError(f"У файлі не знайдено жодного коректного листа: {path}")
    return messages


# Виділення адреси зі значення заголовка: "HR <hr@example.com>" -> "hr@example.com"
def extract_address(value: str) -> str:
    match = ADDRESS_PATTERN.search(value)
    return match.group(0).lower() if match else ""


# Виділення домену зі значення заголовка: "HR <hr@example.com>" -> "example.com"
def extract_domain(value: str) -> str:
    match = ADDRESS_PATTERN.search(value)
    return match.group(1).lower().rstrip(".") if match else ""


# Визначення рівня ризику за оцінкою: перший поріг, якого оцінка досягає
def classify_risk(score: int) -> str:
    for threshold, level, _ in RISK_LEVELS:
        if score >= threshold:
            return level
    return RISK_LOW


# Підпис рівня ризику для консольного звіту
def risk_label(level: str) -> str:
    return next(label for _, name, label in RISK_LEVELS if name == level)


# Оцінка підозрілості одного листа за шкалою 0–100 за індикаторами з завдання
def analyze_message(message: EmailMessage, keywords: list[str]) -> AnalysisResult:
    score = 0
    reasons: list[str] = []

    from_domain = extract_domain(message.from_header)
    reply_to_domain = extract_domain(message.reply_to)
    return_path_domain = extract_domain(message.return_path)

    # Індикатор 1: відповідь на лист піде на інший домен, ніж той, з якого він нібито надійшов
    if reply_to_domain and reply_to_domain != from_domain:
        score += SCORE_REPLY_TO_MISMATCH
        reasons.append("From and Reply-To domains differ")

    # Індикатор 2: фактичний відправник (Return-Path) не збігається з адресою From
    if return_path_domain and return_path_domain != from_domain:
        score += SCORE_RETURN_PATH_MISMATCH
        reasons.append("From and Return-Path domains differ")

    # Індикатор 3: стоп-слова в темі листа (без урахування регістру); внесок обмежений зверху
    subject = message.subject.lower()
    keyword_matches = [keyword for keyword in keywords if keyword in subject]
    if keyword_matches:
        score += min(SCORE_PER_KEYWORD * len(keyword_matches), MAX_KEYWORD_SCORE)
        reasons.append(f"suspicious keywords: {', '.join(keyword_matches)}")

    # Індикатор 4: кожен заголовок Received — один вузол ретрансляції; внесок обмежений зверху
    relay_hops = len(message.received)
    if relay_hops > MAX_NORMAL_HOPS:
        extra_hops = relay_hops - MAX_NORMAL_HOPS
        score += min(SCORE_PER_EXTRA_HOP * extra_hops, MAX_HOP_SCORE)
        reasons.append(f"unusually long relay chain ({relay_hops} hops)")

    risk_level = classify_risk(score)
    logger.debug(
        "%s: оцінка %d/%d, рівень %s", message.message_id, score, MAX_SCORE, risk_level
    )
    return AnalysisResult(
        message, score, risk_level, keyword_matches, relay_hops, reasons
    )


# Запис звіту у CSV; newline="" потрібен, щоб модуль csv сам керував кінцями рядків
def write_csv_report(results: list[AnalysisResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_COLUMNS)
        for result in results:
            writer.writerow(
                [
                    result.message.message_id,
                    result.message.subject,
                    result.score,
                    result.risk_level,
                    "; ".join(result.keyword_matches),
                    result.relay_hops,
                    "; ".join(result.reasons),
                ]
            )


# Виведення звіту в консоль
def print_report(results: list[AnalysisResult]) -> None:
    print("\n=== Результати аудиту фішингу та підміни відправника ===")
    # Докладно показуються листи з рівнем ризику, вищим за низький
    suspicious = [result for result in results if result.risk_level != RISK_LOW]
    if not suspicious:
        print("Підозрілих листів не виявлено")

    for result in suspicious:
        message = result.message
        from_address = extract_address(message.from_header)
        label = risk_label(result.risk_level)
        print(f'\n[{label}] Лист {message.message_id} | Тема: "{message.subject}"')
        if "From and Return-Path domains differ" in result.reasons:
            return_path = extract_address(message.return_path)
            print(
                f'  - Невідповідність відправника: From: "{from_address}" vs Return-Path: "{return_path}"'
            )
        if "From and Reply-To domains differ" in result.reasons:
            print(
                f'  - Невідповідність Reply-To   : "{extract_address(message.reply_to)}"'
            )
        if result.keyword_matches:
            print(f"  - Знайдені стоп-слова        : {result.keyword_matches}")
        hops_note = "аномально" if result.relay_hops > MAX_NORMAL_HOPS else "норма"
        print(f"  - Вузлів ретрансляції        : {result.relay_hops} ({hops_note})")
        print(f"  - Оцінка підозрілості        : {result.score}/{MAX_SCORE} ({label})")

    # Counter рахує кількість листів за рівнями ризику та частоту кожного індикатора
    levels = Counter(result.risk_level for result in results)
    indicators = Counter(
        reason.split(":")[0].split(" (")[0]
        for result in results
        for reason in result.reasons
    )

    print("\n=== Підсумок ===")
    print(f"Усього листів : {len(results)}")
    for _, level, label in RISK_LEVELS:
        print(f"{label.capitalize()} : {levels[level]}")
    if indicators:
        print("\n=== Частота індикаторів ===")
        for indicator, count in indicators.most_common():
            print(f"{indicator} : {count}")
    print()


# Головна функція утиліти; повертає код завершення (0 — успіх, 1 — помилка)
def run_analysis(
    mail_log: Path, keywords_file: Path, out_csv: Path, debug: bool = False
) -> int:
    # force=True переналаштовує логування, навіть якщо його вже було налаштовано раніше
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="[%(levelname)s] %(message)s",
        force=True,
    )

    try:
        logger.info("Аналіз заголовків листів із файлу %s...", mail_log)
        keywords = load_keywords(keywords_file)
        messages = parse_mail_log(mail_log)
        logger.info("Перевірено листів: %d.", len(messages))

        results = [analyze_message(message, keywords) for message in messages]
        for result in results:
            if result.risk_level != RISK_LOW:
                logger.warning(
                    "Підозрілий лист %s (оцінка %d/%d, рівень %s): %s",
                    result.message.message_id,
                    result.score,
                    MAX_SCORE,
                    result.risk_level,
                    "; ".join(result.reasons),
                )

        print_report(results)
        write_csv_report(results, out_csv)
        logger.info("Звіт збережено у %s", out_csv)
    except FileNotFoundError as error:
        logger.error("Файл не знайдено: %s", error.filename)
        return 1
    except (OSError, UnicodeDecodeError) as error:
        logger.error("Помилка читання або запису файлу: %s", error)
        return 1
    except MailAnalysisError as error:
        logger.error("%s", error)
        return 1

    return 0
