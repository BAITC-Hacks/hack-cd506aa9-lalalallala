#!/usr/bin/env python3
"""FAQ-бот на 5 вопросов: отвечает в терминале по совпадению ключевых слов.

Запуск:
    python3 faq_bot.py                  # интерактивный чат
    python3 faq_bot.py "во сколько старт?"   # один вопрос и выход
"""

import os
import re
import sys

DEFAULT_FAQ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faq.txt")

# Порог уверенности: ниже него считаем, что вопрос не про нашу тему.
MIN_SCORE = 0.34
# Совпадение по строке K: (синонимы) ценим чуть выше, чем по тексту вопроса.
KEYWORD_BONUS = 0.15
# Длина «стема»: обрезаем окончания, чтобы «команды» и «командой» сошлись.
STEM_LEN = 5

STOP_WORDS = {
    "а", "и", "в", "на", "с", "со", "по", "за", "у", "о", "об", "к", "из", "от",
    "для", "до", "не", "ну", "это", "это", "мне", "мы", "я", "ли", "же", "бы",
    "есть", "быть", "как", "так", "там", "тут", "вот", "еще", "уже", "их", "его",
}

WORD_RE = re.compile(r"[a-zа-я0-9]+")
EXIT_COMMANDS = {"/выход", "выход", "exit", "quit", "/quit", "/exit", "q"}


class Entry:
    """Одна пара вопрос–ответ из faq.txt."""

    def __init__(self, question, answer, keywords):
        self.question = question
        self.answer = answer
        self.keywords = keywords
        self.question_tokens = set(normalize(question))
        self.keyword_tokens = set(normalize(keywords))

    def __repr__(self):
        return "Entry(%r)" % self.question


def normalize(text):
    """Текст -> список стемов: нижний регистр, ё->е, без пунктуации и стоп-слов."""
    text = text.lower().replace("ё", "е")
    tokens = []
    for word in WORD_RE.findall(text):
        if word in STOP_WORDS:
            continue
        tokens.append(word[:STEM_LEN])
    return tokens


def load_faq(path=DEFAULT_FAQ):
    """Читает faq.txt и возвращает список Entry."""
    with open(path, encoding="utf-8") as handle:
        lines = handle.readlines()

    entries = []
    current = {}
    start_line = 0

    def flush(at_line):
        if not current:
            return
        if "Q" not in current or "A" not in current:
            raise ValueError(
                "%s: запись, начатая на строке %d, должна содержать и Q:, и A:"
                % (path, start_line)
            )
        entries.append(Entry(current["Q"], current["A"], current.get("K", "")))
        current.clear()

    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            flush(number)
            continue
        match = re.match(r"^([QAK])\s*:\s*(.*)$", line)
        if not match:
            raise ValueError(
                "%s, строка %d: ожидался префикс Q:, A: или K:, получено %r"
                % (path, number, line)
            )
        key, value = match.group(1), match.group(2).strip()
        if not current:
            start_line = number
        current[key] = value
    flush(len(lines) + 1)

    if not entries:
        raise ValueError("%s: не найдено ни одной пары вопрос–ответ" % path)
    return entries


def score(query_tokens, entry):
    """Доля слов вопроса, нашедшихся в записи, с бонусом за синонимы."""
    if not query_tokens:
        return 0.0
    hits = 0
    bonus = 0.0
    for token in query_tokens:
        if token in entry.question_tokens:
            hits += 1
        elif token in entry.keyword_tokens:
            hits += 1
            bonus += KEYWORD_BONUS
    if not hits:
        return 0.0
    return hits / len(query_tokens) + bonus


def find_best(query, entries):
    """Возвращает (Entry, score) или (None, score) если ничего не подошло."""
    query_tokens = set(normalize(query))
    best, best_score = None, 0.0
    for entry in entries:
        value = score(query_tokens, entry)
        if value > best_score:
            best, best_score = entry, value
    if best is None or best_score < MIN_SCORE:
        return None, best_score
    return best, best_score


def answer(query, entries):
    """Текст ответа или None, если бот не знает."""
    best, _ = find_best(query, entries)
    return best.answer if best else None


def help_text(entries):
    lines = ["Я знаю ответы на эти вопросы:"]
    for entry in entries:
        lines.append("  • " + entry.question)
    lines.append("Команды: /help — этот список, выход — закончить чат.")
    return "\n".join(lines)


UNKNOWN = (
    "Не знаю. Я отвечаю только про репетицию: время, команду, трек, сдачу и призы. "
    "Наберите /help, чтобы увидеть список вопросов."
)


def repl(entries):
    print("FAQ-бот репетиции. Задайте вопрос, /help — список тем, «выход» — закончить.")
    while True:
        try:
            query = input("вы  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in EXIT_COMMANDS:
            break
        if query.lower() in ("/help", "help", "/?", "помощь"):
            print(help_text(entries))
            continue
        print("бот > " + (answer(query, entries) or UNKNOWN))
    print("бот > Удачи на репетиции!")


def main(argv):
    args = list(argv)
    path = DEFAULT_FAQ
    if "--faq" in args:
        index = args.index("--faq")
        try:
            path = args[index + 1]
        except IndexError:
            print("Ошибка: после --faq нужен путь к файлу", file=sys.stderr)
            return 2
        del args[index:index + 2]

    try:
        entries = load_faq(path)
    except (OSError, ValueError) as error:
        print("Не удалось прочитать базу вопросов: %s" % error, file=sys.stderr)
        return 1

    if args:
        query = " ".join(args)
        print(answer(query, entries) or UNKNOWN)
        return 0

    repl(entries)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
