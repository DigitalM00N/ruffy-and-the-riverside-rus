import os, re
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator

GAME_DIR_NAME = "Ruffy and the Riverside"


def find_game():
    """Путь к игре: переменная RUFFY_GAME или поиск по библиотекам Steam."""
    env = os.environ.get("RUFFY_GAME")
    if env:
        return env.rstrip("/\\")
    libs = []
    try:
        import winreg
        for hive, key in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                          (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
            try:
                with winreg.OpenKey(hive, key) as k:
                    for val in ("SteamPath", "InstallPath"):
                        try:
                            libs.append(winreg.QueryValueEx(k, val)[0])
                        except OSError:
                            pass
            except OSError:
                pass
    except ImportError:
        pass
    for steam in list(libs):
        vdf = os.path.join(steam, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf):
            libs += [p.replace("\\\\", "\\") for p in re.findall(r'"path"\s+"([^"]+)"', open(vdf, encoding="utf-8").read())]
    for lib in libs:
        cand = os.path.join(lib, "steamapps", "common", GAME_DIR_NAME)
        if os.path.exists(os.path.join(cand, GAME_DIR_NAME + "_Data")):
            return cand
    raise SystemExit("Игра не найдена. Укажите путь: install.bat \"C:\\...\\Ruffy and the Riverside\"")


GAME = find_game().replace("\\", "/")
DATA = GAME + "/" + GAME_DIR_NAME + "_Data"
_gen = None


def gen():
    global _gen
    if _gen is None:
        _gen = TypeTreeGenerator("2022.3.30f1")
        _gen.load_local_game(GAME)
    return _gen


def load(*files):
    env = UnityPy.load(*[DATA + "/" + f for f in files])
    env.typetree_generator = gen()
    return env


# UnityPy добавляет «.dll» к имени сборки, а генератор IL2CPP ждёт имя без расширения
_orig_get_nodes = TypeTreeGenerator.get_nodes


def _get_nodes(self, assembly, fullname):
    if assembly.endswith(".dll"):
        assembly = assembly[:-4]
    return _orig_get_nodes(self, assembly, fullname)


TypeTreeGenerator.get_nodes = _get_nodes
