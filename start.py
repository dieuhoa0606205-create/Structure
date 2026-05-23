# start.py —— 
import subprocess
import sys
import os

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(base_dir, "main.py")

    if not os.path.exists(main_script):
        print(f"❌ 找不到 {main_script}")
        sys.exit(1)

    print("🛫 正在启动 AeroStructCalc ...")
    print("浏览器打开 http://localhost:8501 即可查看")
    print("按 Ctrl+C 停止运行\n")

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", main_script])
    except KeyboardInterrupt:
        print("\n🛬 程序已优雅退出。")

if __name__ == "__main__":
    main()