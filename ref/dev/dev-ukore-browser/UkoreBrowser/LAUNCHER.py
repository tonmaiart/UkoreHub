import os
import sys
import subprocess


def main():
    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    target_script = os.path.join(current_dir, "start.py")

    if not os.path.exists(target_script):
        print(f"[ERROR] ไม่พบไฟล์: {target_script}")
        os.system("pause")
        return

    # ใช้ pythonw.exe เพื่อไม่ให้ขึ้น taskbar เป็น Python
    if getattr(sys, "frozen", False):
        # ถ้าถูก build เป็น .exe แล้ว
        python_exe = "pythonw"
    else:
        # ถ้ารันแบบ development
        python_exe = sys.executable.replace("python.exe", "pythonw.exe")

    print(f"Launching: {os.path.basename(target_script)}\n")

    try:
        subprocess.Popen([python_exe, target_script], shell=False)
    except Exception as e:
        print(f"\n[ERROR] เกิดข้อผิดพลาดไม่คาดคิด:\n{e}")
        os.system("pause")


if __name__ == "__main__":
    main()
