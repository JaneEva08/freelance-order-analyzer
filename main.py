"""AI Client Report Generator: dialog transcript -> AI -> JSON -> HTML -> PDF.

Usage: python main.py example_dialog.txt [--design]
       --design: add an AI-generated design image (needs OPENAI_API_KEY)
       (or without arguments: paste the transcript, finish with Ctrl+D / Ctrl+Z)
"""
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
for noisy in ("fontTools", "weasyprint", "httpx"):
    logging.getLogger(noisy).setLevel(logging.WARNING)
logger = logging.getLogger("main")


def read_transcript(argv: list) -> str:
    args = [a for a in argv[1:] if not a.startswith("--")]
    if args:
        path = Path(args[0])
        logger.info("Чтение транскрибации из файла: %s", path)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise SystemExit(f"Не удалось прочитать файл {path}: {exc}")
        logger.info("Файл прочитан (длина: %d символов)", len(text))
        return text
    logger.info("Ввод транскрибации из stdin")
    return sys.stdin.read()


def main(argv: list) -> int:
    from utils.ai_processor import AIProcessingError, process_dialog_with_ai
    from utils.pdf_generator import generate_pdf

    text = read_transcript(argv)
    try:
        logger.info("Обработка диалога с помощью ИИ")
        data = process_dialog_with_ai(text)
        logger.info("Структурированные данные получены: %d полей", len(data))
        if "--design" in argv:
            from utils.image_generator import generate_design_image
            image, _ = generate_design_image(text)
            if image:
                data["image_path"] = image.resolve().as_uri()
            else:
                logger.warning("Отчёт будет создан без изображения")
        logger.info("Генерация PDF")
        path = generate_pdf(data)
    except AIProcessingError as exc:
        logger.error("Ошибка обработки ИИ: %s", exc)
        return 1
    except Exception:
        logger.exception("Не удалось сгенерировать отчёт")
        return 1
    print(f"Отчёт успешно создан: {path.relative_to(Path(__file__).parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

