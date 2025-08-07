#!/bin/bash

# 웹소설 다운로더 실행 스크립트
echo "웹소설 다운로더를 시작합니다..."
echo "필요한 패키지를 확인하고 설치합니다..."

# 현재 스크립트의 디렉토리로 이동
cd "$(dirname "$0")"

# Python3가 설치되어 있는지 확인
if ! command -v python3 &> /dev/null; then
    echo "오류: Python3가 설치되어 있지 않습니다."
    echo "Python3를 먼저 설치해주세요: https://www.python.org/downloads/"
    read -p "아무 키나 눌러서 종료..."
    exit 1
fi

# pip3가 설치되어 있는지 확인
if ! command -v pip3 &> /dev/null; then
    echo "pip3를 설치합니다..."
    python3 -m ensurepip --upgrade
fi

# 필요한 패키지 설치
echo "필요한 패키지를 설치합니다..."
echo "이 작업은 처음 실행 시에만 시간이 걸릴 수 있습니다..."

# 기본 패키지 및 selenium 설치 (고급 우회 기능용)
pip3 install --user --upgrade requests beautifulsoup4 urllib3 selenium webdriver-manager undetected-chromedriver pyautogui || {
    echo "pip3 설치 실패 시 python3 -m pip 사용..."
    python3 -m pip install --user --upgrade requests beautifulsoup4 urllib3 selenium webdriver-manager undetected-chromedriver pyautogui || {
        echo "패키지 설치 중 일부 경고가 있을 수 있지만 정상적으로 진행됩니다."
    }
}

echo "웹소설 다운로더를 실행합니다..."
echo ""

# Python 스크립트 실행 (오류 표시 포함)
if python3 webnovel_downloader.py; then
    echo ""
    echo "프로그램이 정상 종료되었습니다."
else
    echo ""
    echo "프로그램 실행 중 오류가 발생했습니다."
    echo "오류 내용을 확인해주세요."
fi

echo ""
echo "프로그램이 종료되었습니다."
read -p "아무 키나 눌러서 창을 닫으세요..."
