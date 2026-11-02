"""Presentation grouping without changing requirement IDs or meaning."""
from collections import OrderedDict
from pathlib import Path
import re


def category(text):
    text = text.lower()
    if re.search(r"\b(ai|ии|gpt)\b", text) or any(
        word in text for word in ("база знаний", "базы знаний", "базу знаний")
    ):
        return "ИИ и база знаний"
    rules = [
        ("Интеграции и платформа", ("интеграц", "api", "хостинг", "облачн", "python", "telegram", "e-mail", "email", "push")),
        ("Роли и доступ", ("партнер может", "менеджер отдела", "юрист", "руководитель видит", "руководителю", "права", "роль")),
        ("Финансы и аналитика", ("комисси", "вознагражден", "выплат", "сумму сделки", "отчеты по", "аналитик")),
        ("Клиенты и сделки", ("клиент", "участ", "воронк", "собственник", "инвестор", "карточк", "дублир", "уникальн")),
        ("Интерфейс и качество", ("интерфейс", "дизайн", "темн", "темы", "адаптац", "кноп", "общен", "русск", "язык", "ответ")),
    ]
    for title, words in rules:
        if any(word in text for word in words):
            return title
    return "Интерфейс и качество"


def context(data):
    groups = OrderedDict()
    for r in data["requirements"]:
        groups.setdefault(category(r["description"]), []).append(r)
    order = ("Роли и доступ", "Клиенты и сделки", "Финансы и аналитика",
             "Интеграции и платформа", "ИИ и база знаний", "Интерфейс и качество")
    groups = OrderedDict((name, groups[name]) for name in order if name in groups)
    return {**data, "groups": [{"title": t, "items": items} for t, items in groups.items()],
            "counts": {s: sum(r["status"] == s for r in data["requirements"])
                       for s in ("required", "preferred", "optional")}}


def render_report(data, output):
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from weasyprint import HTML
    root = Path(__file__).resolve().parent
    env = Environment(loader=FileSystemLoader(root / "templates"),
                      autoescape=select_autoescape(["html"]))
    HTML(string=env.get_template("order_report.html").render(**context(data))).write_pdf(output)


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Пересобрать PDF из JSON без API")
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    render_report(json.loads(args.json_file.read_text(encoding="utf-8")),
                  args.output or args.json_file.with_suffix(".pdf"))
