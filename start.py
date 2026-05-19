# start.py —— 一键运行启动脚本（点击 VS Code 右上角 ▶ 运行）
import subprocess
import sys
import os

def main():
    # 获取 main.py 路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(base_dir, "main.py")

    if not os.path.exists(main_script):
        print(f"❌ 找不到 {main_script}")
        sys.exit(1)

    print("🛫 正在启动 AeroStructCalc ...")
    print("浏览器打开 http://localhost:8501 即可查看")
    print("按 Ctrl+C 停止运行\n")

    # 用当前 Python 解释器运行 streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", main_script
    ])

if __name__ == "__main__":
    main()