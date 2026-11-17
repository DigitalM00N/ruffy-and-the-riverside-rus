"""Установка/удаление русификатора Ruffy and the Riverside.

    RuffyRus.exe                     — меню (установить / удалить)
    RuffyRus.exe [путь к игре]       — установить
    RuffyRus.exe --uninstall [путь]  — вернуть оригинальные файлы
(то же самое: python tools/install.py ...)

Оригинальные файлы игры сохраняются в «<папка игры>/rus_backup».
"""
import os, sys, json, shutil, hashlib, subprocess, tempfile, runpy

FROZEN = getattr(sys, "frozen", False)
ROOT = sys._MEIPASS if FROZEN else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_NAME = "Ruffy and the Riverside"


def pause():
    if FROZEN:
        try:
            input("\nНажмите Enter, чтобы закрыть окно...")
        except EOFError:
            pass


def fail(msg):
    print("\nОШИБКА:", msg)
    pause()
    sys.exit(1)


def sha(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {GAME_NAME}.exe"],
                             capture_output=True, text=True, creationflags=0x08000000).stdout
        return f"{GAME_NAME}.exe" in out
    except Exception:
        return False


def valid_game(p):
    return p and os.path.isdir(os.path.join(p, GAME_NAME + "_Data"))


def locate_game(arg):
    """Возвращает (GAME, DATA). Путь: аргумент -> автопоиск Steam -> вопрос пользователю."""
    if arg:
        os.environ["RUFFY_GAME"] = arg.strip('"').rstrip("/\\")
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    while True:
        try:
            import common  # ищет игру при импорте
            if valid_game(common.GAME):
                return common.GAME, common.DATA
            sys.modules.pop("common", None)
            print("По этому пути игра не найдена:", common.GAME)
        except SystemExit:
            sys.modules.pop("common", None)
            print("Игра не найдена автоматически.")
        try:
            p = input(f"Перетащите в это окно папку «{GAME_NAME}» (или вставьте путь) и нажмите Enter:\n> ")
        except EOFError:
            fail("путь к игре не указан")
        os.environ["RUFFY_GAME"] = p.strip().strip('"').rstrip("/\\")


def touched_files():
    files = {"resources.assets", "level1", "level2"}
    imgs = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(ROOT, "img", "ru"))}
    for line in open(os.path.join(ROOT, "data", "alltex.tsv"), encoding="utf-8"):
        r = line.rstrip("\n").split("\t")
        if r[1] == "Texture2D" and r[3] in imgs:
            files.add(r[0])
    return sorted(files)


def uninstall(GAME, DATA, BK, MAN):
    if not os.path.exists(MAN):
        fail("бэкап не найден — русификатор не устанавливался этим установщиком.")
    man = json.load(open(MAN, encoding="utf-8"))
    for fn in man:
        shutil.copy2(os.path.join(BK, fn), os.path.join(DATA, fn))
        print("восстановлен", fn)
    shutil.rmtree(BK)
    print("\nГотово: игра возвращена к оригиналу.")


def install(GAME, DATA, BK, MAN):
    man = json.load(open(MAN, encoding="utf-8")) if os.path.exists(MAN) else {}
    # 1. бэкап оригиналов (обновляется, если игра обновилась после прошлой установки)
    os.makedirs(BK, exist_ok=True)
    for fn in touched_files():
        cur = os.path.join(DATA, fn)
        if not os.path.exists(cur):
            fail(f"нет файла {fn} — версия игры не поддерживается.")
        h = sha(cur)
        rec = man.get(fn)
        if rec and h in (rec["orig"], rec.get("patched")):
            continue
        if rec:
            print("игра обновилась, обновляю бэкап:", fn)
        shutil.copy2(cur, os.path.join(BK, fn))
        man[fn] = {"orig": h}
    json.dump(man, open(MAN, "w", encoding="utf-8"), indent=1)

    # 2. сборка патча из оригиналов (в этом же процессе)
    out = tempfile.mkdtemp(prefix="ruffy_rus_")
    os.environ.update(RUFFY_GAME=GAME, RUFFY_BACKUP=BK, RUFFY_OUT=out)
    print("Сборка патча, это займёт 1–3 минуты...")
    try:
        runpy.run_path(os.path.join(ROOT, "tools", "build.py"), run_name="__main__")
    except SystemExit as e:
        shutil.rmtree(out, ignore_errors=True)
        fail(f"{e} Игра не изменена.")
    except Exception as e:
        shutil.rmtree(out, ignore_errors=True)
        fail(f"сборка не удалась ({type(e).__name__}: {e}). Игра не изменена.")

    # 3. установка
    for fn in os.listdir(out):
        shutil.copy2(os.path.join(out, fn), os.path.join(DATA, fn))
        man.setdefault(fn, {"orig": sha(os.path.join(BK, fn))})["patched"] = sha(os.path.join(DATA, fn))
    json.dump(man, open(MAN, "w", encoding="utf-8"), indent=1)
    shutil.rmtree(out, ignore_errors=True)
    print("\nГотово! В игре: Настройки -> Язык -> «Русский».")


def main():
    print("=== Русификатор Ruffy and the Riverside ===\n")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mode = "uninstall" if "--uninstall" in sys.argv else ("install" if args or not FROZEN else None)
    GAME, DATA = locate_game(args[0] if args else None)
    print("Игра:", GAME)
    BK = os.path.join(GAME, "rus_backup")
    MAN = os.path.join(BK, "manifest.json")
    if mode is None:
        installed = os.path.exists(MAN)
        print("\n1 — установить" + (" / обновить" if installed else "") + " русификатор")
        if installed:
            print("2 — удалить русификатор (вернуть оригинал)")
        try:
            ch = input("\nВыберите и нажмите Enter [1]: ").strip() or "1"
        except EOFError:
            ch = "1"
        mode = "uninstall" if ch == "2" and installed else "install"
    while game_running():
        try:
            input("\nИгра запущена — закройте её и нажмите Enter...")
        except EOFError:
            fail("закройте игру и запустите установщик ещё раз.")
    (uninstall if mode == "uninstall" else install)(GAME, DATA, BK, MAN)
    pause()


if __name__ == "__main__":
    main()
