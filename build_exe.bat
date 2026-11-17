@echo off
rem Сборка RuffyRus.exe (нужны: pip install -r requirements.txt pyinstaller)
cd /d "%~dp0"
python -m PyInstaller --noconfirm --clean --onefile --console --name RuffyRus ^
  --distpath dist --workpath build_exe --specpath build_exe ^
  --collect-all UnityPy --collect-all TypeTreeGeneratorAPI --collect-all etcpak --collect-all texture2ddecoder ^
  --collect-all fmod_toolkit --collect-all pyfmodex --collect-all archspec --collect-all astc_encoder ^
  --collect-all tpk_ar --collect-all lz4 --collect-all brotli ^
  --exclude-module tkinter --exclude-module scipy --exclude-module cv2 --exclude-module matplotlib ^
  --add-data "%~dp0ru;ru" --add-data "%~dp0img\ru;img\ru" --add-data "%~dp0data;data" ^
  --add-data "%~dp0tools\build.py;tools" --add-data "%~dp0tools\common.py;tools" ^
  tools\install.py
