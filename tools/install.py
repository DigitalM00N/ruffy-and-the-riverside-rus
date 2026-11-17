"""Установка/удаление русификатора Ruffy and the Riverside.

    python tools/install.py [путь к игре]            — установить
    python tools/install.py --uninstall [путь к игре] — вернуть оригинальные файлы

Оригинальные файлы игры сохраняются в «<папка игры>/rus_backup».
"""
import os, sys, json, shutil, hashlib, subprocess, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
UNINSTALL = "--uninstall" in sys.argv
if args:
    os.environ["RUFFY_GAME"] = args[0]
sys.path.insert(0, os.path.join(ROOT, "tools"))
from common import GAME, DATA  # noqa: E402  (ищет игру)

BK = os.path.join(GAME, "rus_backup")
MAN = os.path.join(BK, "manifest.json")


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Ruffy and the Riverside.exe"],
                             capture_output=True, text=True).stdout
        return "Ruffy and the Riverside.exe" in out
    except Exception:
        return False


def touched_files():
    files = {"resources.assets", "level1", "level2"}
    imgs = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(ROOT, "img", "ru"))}
    for line in open(os.path.join(ROOT, "data", "alltex.tsv"), encoding="utf-8"):
        r = line.rstrip("\n").split("\t")
        if r[1] == "Texture2D" and r[3] in imgs:
            files.add(r[0])
    return sorted(files)


print("Игра:", GAME)
if game_running():
    sys.exit("Закройте игру и запустите ещё раз.")
man = json.load(open(MAN, encoding="utf-8")) if os.path.exists(MAN) else {}

if UNINSTALL:
    if not man:
        sys.exit("Бэкап не найден — русификатор не устанавливался этим установщиком.")
    for fn in man:
        shutil.copy2(os.path.join(BK, fn), os.path.join(DATA, fn))
        print("восстановлен", fn)
    shutil.rmtree(BK)
    print("Готово: игра возвращена к оригиналу.")
    sys.exit(0)

# 1. бэкап оригиналов (обновляется, если игра обновилась после прошлой установки)
os.makedirs(BK, exist_ok=True)
for fn in touched_files():
    cur = os.path.join(DATA, fn)
    if not os.path.exists(cur):
        sys.exit(f"Нет файла {fn} — версия игры не поддерживается.")
    h = sha(cur)
    rec = man.get(fn)
    if rec and h in (rec["orig"], rec.get("patched")):
        continue
    if rec:
        print("игра обновилась, обновляю бэкап:", fn)
    shutil.copy2(cur, os.path.join(BK, fn))
    man[fn] = {"orig": h}
json.dump(man, open(MAN, "w", encoding="utf-8"), indent=1)

# 2. сборка патча из оригиналов
out = tempfile.mkdtemp(prefix="ruffy_rus_")
env = dict(os.environ, RUFFY_GAME=GAME, RUFFY_BACKUP=BK, RUFFY_OUT=out)
print("Сборка патча (1–3 минуты)...")
r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build.py")], env=env)
if r.returncode:
    shutil.rmtree(out, ignore_errors=True)
    sys.exit("Ошибка сборки, игра не изменена.")

# 3. установка
for fn in os.listdir(out):
    shutil.copy2(os.path.join(out, fn), os.path.join(DATA, fn))
    man.setdefault(fn, {"orig": sha(os.path.join(BK, fn))})["patched"] = sha(os.path.join(DATA, fn))
json.dump(man, open(MAN, "w", encoding="utf-8"), indent=1)
shutil.rmtree(out, ignore_errors=True)
print("\nГотово! В игре: Настройки -> Язык -> «Русский».")
