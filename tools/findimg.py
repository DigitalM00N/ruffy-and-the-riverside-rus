import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from common import *
import UnityPy
env = UnityPy.load(DATA + "/globalgamemanagers.assets")
g = list(env.files.values())[0]
ids = {}
for o in g.objects.values():
    if o.type.name == "MonoScript":
        s = o.read()
        if s.m_ClassName in ("LanguageSprite", "TranslatableImage", "LanguageOverride", "TranslatedText", "TranslatedTextPro", "TranslatableChild", "Translatable"):
            ids[o.path_id] = s.m_ClassName
print(ids)
open("scriptids.txt","w").write(repr(ids))
