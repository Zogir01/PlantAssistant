import subprocess
import time
import pyautogui
import os
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
UPLOAD_DIR = Path(os.path.join(SCRIPT_DIR, "upload"))
CACHE_FILE = Path(os.path.join(SCRIPT_DIR, "upload_cache.json"))

def file_mtime(path: Path) -> float:
    return path.stat().st_mtime


def update_files():
    """Aktualizacja tylko zmienionych plików"""
    if not CACHE_FILE.exists():
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)

    changed_files = []
    for path in UPLOAD_DIR.rglob("*"):
        if path.is_file():
            rel_path = str(path.relative_to(UPLOAD_DIR))
            mtime = file_mtime(path)
            if rel_path not in cache or cache[rel_path] != mtime:
                changed_files.append(path)

    if not changed_files:
        print("Brak zmian — nic nie zostało wysłane.")
    else:
        print(f"Wykryto {len(changed_files)} zmodyfikowanych plików:")
        for f in changed_files:
            print(" •", f.name)

        for path in changed_files:
            rel_path = str(path.relative_to(UPLOAD_DIR)).replace("\\", "/")
            print(f"Wgrywam {rel_path}...")
            subprocess.run(["mpremote", "fs", "cp", str(path), f":/{rel_path}"], check=True)

        for path in changed_files:
            rel_path = str(path.relative_to(UPLOAD_DIR))
            cache[rel_path] = file_mtime(path)

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)

def clear_files():
    print("Usuwam wszystkie pliki z urządzenia...")
    subprocess.run(['mpremote', 'fs', 'rm', '-r', ':/'], check=False)

def full_upload():
    """Usuwa wszystko z urządzenia i wgrywa cały katalog upload/"""
    print("Deleting all files...")
    subprocess.run(['mpremote', 'fs', 'rm', '-r', ':/'], check=False)

    print("Uploading files...")
    subprocess.run(['mpremote', 'fs', 'cp', '--recursive', str(UPLOAD_DIR) + '\\.', ':/'], check=True)

    print("Updating cache...")
    cache = {}
    for path in UPLOAD_DIR.rglob("*"):
        if path.is_file():
            rel_path = str(path.relative_to(UPLOAD_DIR)).replace("\\", "/")
            cache[rel_path] = file_mtime(path)

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def run_mpremote_shell():
    """Uruchamia MicroPython shell"""
    print("\nSukces. Uruchamiam MicroPython shell...")
    subprocess.Popen(['start', 'cmd', '/k', 'mpremote'], shell=True)
    # subprocess.run(['mpremote'], check=True)
    time.sleep(2)
    pyautogui.press('enter')
    pyautogui.hotkey('ctrl', 'd')


def main():
    if len(sys.argv) < 2:
        print("Użycie:")
        print("  python upload.py update   - aktualizacja tylko zmienionych plików")
        print("  python upload.py full     - pełne czyszczenie i wgranie wszystkich plików")
        print("  python upload.py clear    - usunięcie wszystkich plików")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "update":
        update_files()
    elif mode == "full":
        full_upload()
    elif mode == "clear":
        clear_files()
        time.sleep(1)
    else:
        print(f"Nieznany tryb: {mode}")
        sys.exit(1)

    #run_mpremote_shell()


if __name__ == "__main__":
    main()


# STARY SKRYPT
#
# import subprocess
# import time
# import pyautogui
# import os

# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# UPLOAD_DIR = os.path.join(SCRIPT_DIR, "upload")

# # Wgrywanie plików
# subprocess.run(['mpremote', 'fs', 'rm', '-r', ':/'], check=False)
# subprocess.run(['mpremote', 'fs', 'cp', '--recursive', UPLOAD_DIR + '\\.', ':/'], check=True)

# print("Sukces. Uruchamiam MicroPython shell...")

# subprocess.run(['mpremote'], check=True)

# # Uruchamiamy mpremote w nowym oknie terminala
# #proc = subprocess.Popen(['start', 'cmd', '/k', 'mpremote'], shell=True)

# # Czekamy aż terminal się otworzy
# time.sleep(2)  # dopasuj jeśli trzeba

# # Wysyłamy Enter
# pyautogui.press('enter')

# # Wysyłamy Ctrl+D (kombinacja ctrl + d)
# pyautogui.hotkey('ctrl', 'd')
