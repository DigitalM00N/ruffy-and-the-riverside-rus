"""Проверка структуры перевода: python -I tools/check.py <путь-префикс внутри orig/en, напр. dialogs/farm>
Сравнивает orig/en/<...> с ru/<...>: число строк, неизменность служебных строк, ключи, плейсхолдеры."""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN = os.path.join(ROOT, "orig", "en"); RU = os.path.join(ROOT, "ru")
prefixes = sys.argv[1:] or [""]
errs = 0; missing = 0; ok = 0
def kind(rel):
    top = rel.replace("\\", "/").split("/")[0]
    if top == "dialogs": return "dialog"
    if top == "questlog": return "lines"
    return "kv"
def is_text(l):  # строки диалога, которые переводятся
    return l.startswith((" ", "\t")) and l.strip() != "" or l.startswith("* ")
for pre in prefixes:
    base = os.path.join(EN, pre)
    files = [base] if os.path.isfile(base) else [os.path.join(r, f) for r, _, fs in os.walk(base) for f in fs]
    for ef in sorted(files):
        rel = os.path.relpath(ef, EN); rf = os.path.join(RU, rel)
        if not os.path.exists(rf):
            print("MISSING", rel); missing += 1; continue
        e = open(ef, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
        try: r = open(rf, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
        except UnicodeDecodeError: print("NOT UTF-8", rel); errs += 1; continue
        if r and r[0].startswith("﻿"): print("BOM", rel); errs += 1
        bad = []
        if len(e) != len(r): bad.append(f"line count {len(e)} != {len(r)}")
        else:
            k = kind(rel)
            for i, (a, b) in enumerate(zip(e, r), 1):
                if k == "dialog":
                    if is_text(a):
                        if not is_text(b): bad.append(f"L{i}: text line lost its indent/'* ' prefix")
                        elif a.startswith("* ") != b.startswith("* "): bad.append(f"L{i}: '* ' prefix mismatch")
                        elif a.strip() and re.search(r"[A-Za-z]{4,}", b) and not re.search(r"[А-Яа-яЁё]", b) and a.strip() not in ("...",):
                            bad.append(f"L{i}: looks untranslated: {b.strip()[:60]}")
                    elif a != b: bad.append(f"L{i}: service line changed: {a!r} -> {b!r}")
                elif k == "kv":
                    if ":" in a:
                        ka = a.split(":", 1)[0]
                        if ":" not in b or b.split(":", 1)[0] != ka: bad.append(f"L{i}: key changed {ka!r}")
                        elif b.count(":") > a.count(":"): bad.append(f"L{i}: extra ':' in value (запрещено)")
                    elif a.strip() != b.strip() and a.strip() == "": bad.append(f"L{i}: blank line changed")
                else:
                    if (a.strip() == "") != (b.strip() == ""): bad.append(f"L{i}: blank/non-blank mismatch")
                for ph in re.findall(r"\{\d+\}|<[^>]+>", a):
                    if ph not in b: bad.append(f"L{i}: placeholder/tag {ph} missing")
        if bad:
            errs += 1; print("ERR", rel); [print("   ", x) for x in bad[:10]]
        else: ok += 1
print(f"OK {ok}, errors {errs}, missing {missing}")
