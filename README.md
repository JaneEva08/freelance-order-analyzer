# Freelance Order Analyzer — VPf10

Текст объявления → ИИ → проверенный JSON → HTML-шаблон → PDF.
Требования заказчика отделены от неясностей и вопросов анализатора.

Репозиторий: https://github.com/JaneEva08/freelance-order-analyzer

## Установка

Требуется Python 3.10+. В Windows для WeasyPrint нужны системные библиотеки
Pango; инструкция: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

В локальном .env задайте OPENAI_API_KEY, OPENAI_MODEL и, при работе
через совместимого провайдера, OPENAI_BASE_URL. Не публикуйте .env.

## Разбор объявления

Сохраните исходный текст в UTF-8:

```powershell
python analyze_order.py order.txt --source-url https://example.com/order
python analyze_order.py order.txt --json-only
python -m unittest discover -s tests -v
```

Результаты появляются в reports/: JSON и PDF с одинаковым именем.
Автоматического парсинга биржи в приложении нет. Неизвестные бюджет и сроки
сохраняются как null; почасовая ставка поясняется отдельно.

Проверяются структура JSON, допустимые статусы, уникальность ID, ссылки
вопросов и точное присутствие цитат. При ошибке ответа модель получает до
двух запросов на исправление. Это не гарантирует полноту и правильность
смыслового разбора: результат нужно сверять с исходником.

В тексте объявления могут быть чужие инструкции; промпт рассматривает
их как данные. HTML экранируется при подстановке в шаблон.

## Исходный режим диалога

Расшифровка диалога → ИИ (OpenAI) → структурированный JSON → HTML-шаблон (Jinja2) → PDF (WeasyPrint) в `reports/`.

```bash
pip install -r requirements.txt
cp .env.example .env            # впишите OPENAI_API_KEY
python main.py example_dialog.txt
python main.py example_dialog.txt --design   # + изображение, сгенерированное ИИ
MOCK_AI=1 python main.py example_dialog.txt  # без API-ключа (заглушка)
```

Структура: `main.py`, `utils/ai_processor.py`, `utils/pdf_generator.py`, `utils/image_generator.py`,
`templates/report_template.html`, `reports/`. Ошибки (пустой файл, нет ключа, битый JSON, сбой API)
обрабатываются, основные этапы логируются.

