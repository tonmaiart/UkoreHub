import os
import sys
import subprocess

# นำเข้า Win32 API constant สำหรับการซ่อนหน้าต่าง Console
# ใช้ได้เฉพาะบน Windows
if sys.platform == "win32":
    CREATE_NO_WINDOW = 0x08000000
else:
    CREATE_NO_WINDOW = 0

def main():
    # ในกรณีที่รันจาก .exe (frozen), sys.executable คือตัว .exe เอง
    # ดังนั้นเราจะใช้ pythonw.exe ซึ่งอยู่ในตำแหน่งเดียวกับ python.exe
    # หรือในกรณีที่รันจาก .py ธรรมดา เราจะใช้ pythonw ในสภาพแวดล้อม
    if sys.platform == "win32":
        # แทนที่ 'python.exe' ด้วย 'pythonw.exe' เพื่อซ่อน Console
        pythonw_exe = sys.executable.replace("python.exe", "pythonw.exe")
    else:
        # สำหรับระบบอื่น (Linux/Mac) ให้ใช้ sys.executable ปกติ
        pythonw_exe = sys.executable

    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    target_script = os.path.join(current_dir, "start.py")

    if not os.path.exists(target_script):
        print(f"[ERROR] ไม่พบไฟล์: {target_script}")
        os.system("pause")
        return

    # ล้างข้อความ Launching เพราะ Console จะถูกซ่อน
    # print(f"Launching: {os.path.basename(target_script)}\n") 

    try:
        # ใช้ creationflags=CREATE_NO_WINDOW เพื่อซ่อน Console
        # ใช้ shell=False และไม่ใช้ check=True เพราะการซ่อนหน้าต่างทำให้ตรวจสอบ error ยากขึ้น
        subprocess.run(
            [pythonw_exe, target_script],
            creationflags=CREATE_NO_WINDOW,
            check=False, # ไม่ใช้ check=True เพราะการซ่อน Console ทำให้การรายงาน error ยาก
            # เราสามารถ redirect output เพื่อป้องกันไม่ให้เกิด Console ชั่วคราว
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        # ในโหมดซ่อน Console ข้อความเหล่านี้จะไม่แสดงผล เว้นแต่จะถูกบันทึกใน Log
        print(f"\n[CRITICAL ERROR] เกิดข้อผิดพลาดไม่คาดคิดในการรัน launcher:\n{e}")
        # ไม่ควรใช้ os.system("pause") เพราะมันจะเปิด Console ขึ้นมา
        

if __name__ == "__main__":
    # ตรวจสอบว่ามี pythonw.exe ในสภาพแวดล้อมหรือไม่ (ถ้าไม่ใช้ PyInstaller)
    if sys.platform == "win32" and not os.path.exists(sys.executable.replace("python.exe", "pythonw.exe")):
         print(f"[WARNING] ไม่พบ pythonw.exe รันด้วย python.exe แทน (จะมี Console ปรากฏ)")
         # ในกรณีนี้ยังไงก็ต้องมี Console เพราะต้องใช้สำหรับรัน .py
    
    main()