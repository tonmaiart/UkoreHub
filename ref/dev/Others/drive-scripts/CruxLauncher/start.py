import sys
import subprocess
import importlib

# === ตรวจสอบและติดตั้ง package ที่จำเป็น ===
REQUIRED_PACKAGES = ["PySide6", "oauth2client", "gspread", "google-api-python-client","pyperclip"]


def ensure_packages_installed():
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package.lower())
        except ImportError:
            print(f"🔧 Installing missing package: {package} ...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    # pickle เป็น built-in module ไม่ต้องติดตั้ง
    print("✅ All required packages are installed.")


# === เรียกใช้ฟังก์ชันเช็กก่อนรันโปรแกรม ===
ensure_packages_installed()


# === Path และ Import CruxLauncher ===
sys.path.append(r"G:\My Drive\Mellowstar\dev\drive-scripts")

from CruxLauncher.interface import MainWindow
from PySide6 import QtWidgets


# === เริ่มรันแอป ===
if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setProperty("qt.platform.theme", "none")

    window = MainWindow()
    window.show()
    # window.showMaximized()

    sys.exit(app.exec())
