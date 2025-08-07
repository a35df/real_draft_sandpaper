# -*- coding: utf-8 -*-
import time
import sys
import subprocess

def install_package(package):
    """필요한 패키지를 설치합니다."""
    try:
        # 패키지가 설치되어 있는지 확인
        __import__(package)
    except ImportError:
        print(f"'{package}' 패키지를 찾을 수 없어 설치를 시도합니다...")
        try:
            # 현재 스크립트를 실행한 python을 사용하여 pip로 패키지 설치
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"'{package}' 패키지 설치 성공!")
        except Exception as e:
            print(f"'{package}' 패키지 설치 실패: {e}")
            print("\nmacOS에서는 '손쉬운 사용' 권한이 필요할 수 있습니다.")
            print("시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용 에서 사용하는 터미널 앱(예: Terminal.app)을 추가하고 체크해주세요.")
            input("Enter를 눌러 종료하세요...")
            sys.exit(1)

# 스크립트 시작 시 pyautogui 패키지 확인 및 자동 설치
install_package("pyautogui")

import pyautogui

print("="*50)
print("마우스 좌표 확인 프로그램입니다.")
print("Cloudflare 인증 창의 '사람인지 확인' 체크박스 위에")
print("마우스 커서를 올려놓고, 아래에 표시되는 X, Y 좌표를 메모하세요.")
print("메모한 후 이 창은 닫아도 됩니다.")
print("프로그램을 종료하려면 Ctrl+C를 누르세요.")
print("="*50)

try:
    while True:
        x, y = pyautogui.position()
        position_str = f"현재 좌표 -> X: {str(x).rjust(4)} Y: {str(y).rjust(4)}"
        print(position_str, end='')
        print('\b' * (len(position_str) + 1), end='', flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n프로그램을 종료합니다.")
    sys.exit()
except Exception as e:
    print(f"\n오류 발생: {e}")
    input("Enter를 눌러 종료하세요...")
