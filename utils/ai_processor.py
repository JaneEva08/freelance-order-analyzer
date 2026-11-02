"""Interaction with the LLM: raw dialog text -> structured JSON data."""
import json
import logging
import os
import re

logger = logging.getLogger(__name__)

FIELDS = ("client_name", "topic", "main_request", "mood", "deadline_budget", "next_steps")

SYSTEM_PROMPT = (
    "Ты помощник менеджера. Из расшифровки разговора с клиентом извлеки данные и верни "
    "СТРОГО JSON-объект с ключами: client_name, topic, main_request, mood, "
    "deadline_budget (желаемые сроки и стоимость), next_steps (строка, шаги через перенос строки). "
    "Все значения - строки на русском. Если данных нет - пиши 'Не указано'."
)


class AIProcessingError(Exception):
    """Raised when the model response cannot be turned into valid data."""


def _to_text(value) -> str:
    """The model may return a list instead of a string - normalise to str."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "\n".join(str(v).strip() for v in value if str(v).strip())
    if isinstance(value, dict):
        return "\n".join(f"{k}: {v}" for k, v in value.items())
    return str(value).strip()


def normalize(data: dict) -> dict:
    """Guarantee required fields and predictable (string) types."""
    if not isinstance(data, dict):
        raise AIProcessingError(f"Ожидался JSON-объект, получено: {type(data).__name__}")
    result = {f: _to_text(data.get(f)) or "Не указано" for f in FIELDS}
    missing = [f for f in FIELDS if f not in data]
    if missing:
        logger.warning("В ответе ИИ отсутствуют поля: %s", ", ".join(missing))
    return result


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", raw, re.S)
    if fenced:
        raw = fenced.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AIProcessingError(f"Ответ ИИ не является корректным JSON: {exc}") from exc


def _mock(text: str) -> dict:
    """Rule-based stub so the pipeline can be run without an API key."""
    name = re.search(r"меня зовут ([А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+)", text)
    budget = re.search(r"бюджет около [\d ]+ \w+ \w+", text, re.I)
    term = re.search(r"за \d+ недел[ьиюя]", text)
    return {
        "client_name": name.group(1) if name else "Не указано",
        "topic": "Обсуждение разработки корпоративного сайта",
        "main_request": "Корпоративный сайт на 10-12 страниц",
        "mood": "Довольный" if "доволен" in text.lower() else "Нейтральный",
        "deadline_budget": ", ".join(x.group(0) for x in (term, budget) if x) or "Не указано",
        "next_steps": ["Отправить портфолио", "Подготовить коммерческое предложение",
                       "Назначить встречу на следующей неделе"],
    }


def process_dialog_with_ai(text: str) -> dict:
    """Send the transcript to the LLM and return a validated dict with FIELDS."""
    if not text or not text.strip():
        raise AIProcessingError("Пустая транскрибация")

    if os.getenv("MOCK_AI") == "1":
        logger.info("MOCK_AI=1: используется заглушка вместо вызова ИИ")
        return normalize(_mock(text))

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AIProcessingError("Не задан OPENAI_API_KEY (см. .env.example)")

    from openai import OpenAI, OpenAIError

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    logger.info("Запрос к модели %s (длина диалога: %d символов)", model, len(text))
    try:
        response = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL") or None).chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": text}],
        )
    except OpenAIError as exc:
        raise AIProcessingError(f"Ошибка API: {exc}") from exc

    data = normalize(_parse_json(response.choices[0].message.content or ""))
    logger.info("Ответ ИИ получен и проверен: клиент=%s", data["client_name"])
    return data
