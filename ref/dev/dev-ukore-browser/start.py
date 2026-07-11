import sys
import os  # เพิ่ม os เข้ามา


# =============================================
# RESOURCE PATH HELPER (ฟังก์ชันช่วยในการค้นหาไฟล์ทรัพยากร)
# =============================================
def resource_path(relative_path):
    """
    รับเส้นทางสัมพัทธ์ของทรัพยากร (เช่น "icon.ico")
    และคืนค่าเส้นทางที่ถูกต้องเมื่อรันใน PyInstaller 'onefile'
    """
    try:
        # เมื่อรันจากไฟล์ .exe ที่ถูก bundle (onefile mode)
        # sys._MEIPASS คือเส้นทางไปยังโฟลเดอร์ชั่วคราวที่ทรัพยากรถูกแตกออกมา
        base_path = sys._MEIPASS
    except Exception:
        # เมื่อรันแบบปกติ (จากไฟล์ .py)
        base_path = os.path.abspath(".")

    # รวมเส้นทางฐานกับเส้นทางทรัพยากรที่เราเพิ่มด้วย --add-data
    return os.path.join(base_path, relative_path)


# =============================================
# IMPORT MAIN WINDOW
# =============================================

# WARNING: ลบ sys.path.append("G:\My Drive") ออก!
# PyInstaller จะหาโมดูลนี้ได้เอง ตราบใดที่โฟลเดอร์ 'UkoreBrowser' อยู่ข้างๆ start.py

import UkoreBrowser
from UkoreBrowser.interface import MainWindow

from PySide6 import QtWidgets
from PySide6.QtGui import QIcon


# =============================================
# RUN APPLICATION
# =============================================
if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setProperty("qt.platform.theme", "none")

    # NOTE: ใช้ resource_path() เพื่อให้แน่ใจว่า path ของ icon ถูกต้อง
    app_icon_path = resource_path("icon.ico")

    app.setWindowIcon(QIcon(app_icon_path))

    window = MainWindow()
    window.setWindowIcon(QIcon(app_icon_path))  # กำหนดไอคอนให้หน้าต่างหลัก
    window.show()
    # window.showMaximized()

    sys.exit(app.exec())
