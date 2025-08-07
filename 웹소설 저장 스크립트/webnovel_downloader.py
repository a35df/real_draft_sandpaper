#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹소설 다운로더 - 간단하고 안정적인 버전
URL 목록 파일을 읽어서 각 페이지의 텍스트를 추출하여 저장하는 프로그램
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
import requests
import os
import threading
import time
import random
import subprocess
import sys
import json

def install_package(package):
    """필요한 패키지를 설치합니다."""
    try:
        __import__(package)
    except ImportError:
        print(f"{package} 패키지를 찾을 수 없어 설치를 시도합니다...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except Exception as e:
            print(f"'{package}' 패키지 설치 실패: {e}")
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("패키지 설치 오류", f"'{package}' 패키지를 설치할 수 없습니다.\n터미널을 열고 'pip install {package}'를 직접 실행해 보세요.")
            sys.exit(1)

# 스크립트 시작 시 필수 패키지 확인
install_package("webdriver_manager")
install_package("undetected_chromedriver")
install_package("pyautogui")


class WebnovelDownloader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("웹소설 다운로더")
        self.root.geometry("600x450") # 창 크기 조정
        
        # --- 기본 폴더 설정 및 자동 생성 ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_folder = os.path.join(script_dir, "url_lists")
        self.output_folder = os.path.join(script_dir, "downloaded_novels")
        self.state_file = os.path.join(script_dir, "download_state.json")
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)

        self.session = requests.Session()
        retry_strategy = requests.adapters.Retry(
            total=5, backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
        
        self.is_downloading = False
        self.stop_requested = False
        self.last_activity_time = 0 # 자동 재시작을 위한 마지막 활동 시간
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 설정 (간소화)"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # --- 파일/폴더 선택 UI 제거 ---
        info_label = ttk.Label(main_frame, text=f"URL 목록은 'url_lists' 폴더에, 결과는 'downloaded_novels' 폴더에 저장됩니다.", wraplength=580)
        info_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10), columnspan=2)

        settings_frame = ttk.LabelFrame(main_frame, text="설정", padding="5")
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10, columnspan=2)
        
        ttk.Label(settings_frame, text="요청 간격(초):").grid(row=0, column=0, sticky=tk.W)
        self.delay_var = tk.StringVar(value="0") # 기본 딜레이 0으로 변경
        ttk.Spinbox(settings_frame, from_=0, to=10, width=5, textvariable=self.delay_var).grid(row=0, column=1, padx=(5, 20))

        self.coord_click_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="좌표 직접 클릭 모드", variable=self.coord_click_var).grid(row=1, column=0, sticky=tk.W)
        coord_frame = ttk.Frame(settings_frame)
        coord_frame.grid(row=1, column=1, sticky=tk.W, padx=(5,0))
        ttk.Label(coord_frame, text="X:").grid(row=0, column=0)
        self.x_coord_var = tk.StringVar(value="0")
        ttk.Entry(coord_frame, width=5, textvariable=self.x_coord_var).grid(row=0, column=1)
        ttk.Label(coord_frame, text="Y:").grid(row=0, column=2, padx=(5,0))
        self.y_coord_var = tk.StringVar(value="0")
        ttk.Entry(coord_frame, width=5, textvariable=self.y_coord_var).grid(row=0, column=3)
        
        self.hybrid_mode_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="하이브리드 모드 (초고속 다운로드)", variable=self.hybrid_mode_var).grid(row=2, column=0, columnspan=2, sticky=tk.W)

        # --- 도구 프레임 ---
        tools_frame = ttk.LabelFrame(main_frame, text="도구", padding="5")
        tools_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10, columnspan=2)
        self.cleanup_btn = ttk.Button(tools_frame, text="파일 검사", command=self.inspect_and_clean_folder)
        self.cleanup_btn.grid(row=0, column=0, padx=5, pady=5)
        self.normalize_btn = ttk.Button(tools_frame, text="제목 정상화", command=self.normalize_filenames)
        self.normalize_btn.grid(row=0, column=1, padx=5, pady=5)
        self.fill_missing_btn = ttk.Button(tools_frame, text="빠진 화수 채우기", command=self.fill_missing_episodes)
        self.fill_missing_btn.grid(row=0, column=2, padx=5, pady=5)

        self.download_btn = ttk.Button(main_frame, text="다운로드 시작", command=self.start_download)
        self.download_btn.grid(row=3, column=0, pady=10, columnspan=2)
        
        self.progress_var = tk.StringVar(value="대기 중...")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=4, column=0, pady=5, columnspan=2)
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5, columnspan=2)
        
        ttk.Label(main_frame, text="로그:").grid(row=6, column=0, sticky=tk.W, pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=12)
        self.log_text.grid(row=7, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, columnspan=2)
        self.log_text.config(state='normal')
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)

    def select_file(self):
        # 이 함수는 더 이상 사용되지 않음
        pass
            
    def select_folder(self):
        # 이 함수는 더 이상 사용되지 않음
        pass
            
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def start_download(self):
        if self.is_downloading:
            return
            
        self.is_downloading = True
        self.stop_requested = False
        self.last_activity_time = time.time() # 활동 시간 초기화
        self.download_btn.config(text="다운로드 중지", command=self.stop_download)
        
        threading.Thread(target=self.download_process, daemon=True).start()
        self.watchdog_check() # 자동 재시작 감시 시작

    def stop_download(self):
        if self.is_downloading:
            self.log("다운로드 중지를 요청했습니다. 현재 작업을 완료 후 중지합니다...")
            self.stop_requested = True
            self.download_btn.config(state='disabled') # 중지 처리 중에는 버튼 비활성화
        
    def watchdog_check(self):
        """다운로드가 멈췄는지 감시하고 자동으로 재시작합니다."""
        if self.is_downloading:
            timeout_seconds = 300 # 5분
            if time.time() - self.last_activity_time > timeout_seconds:
                self.log(f"다운로드가 {timeout_seconds}초 이상 응답이 없어 자동으로 재시작합니다...")
                self.last_activity_time = time.time() # 중복 재시작 방지
                
                self.stop_download()
                
                def restart():
                    if not self.is_downloading:
                        self.log("이전 작업을 정리하고 다운로드를 다시 시작합니다.")
                        self.start_download()
                    else:
                        self.root.after(2000, restart) # 중지될 때까지 잠시 대기
                
                self.root.after(2000, restart)
                return # 재시작 절차가 완료될 때까지 다음 감시 중단

        # 30초마다 감시를 계속합니다.
        self.root.after(30000, self.watchdog_check)

    def download_process(self):
        try:
            # --- 재시도 횟수 상태 불러오기 ---
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.download_state = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                self.download_state = {}

            self.log("다운로드를 시작합니다...")
            
            # --- 기본 폴더에서 URL 파일 목록 자동 읽기 ---
            url_files = [os.path.join(self.input_folder, f) for f in os.listdir(self.input_folder) if f.endswith('.txt')]
            if not url_files:
                self.log(f"'{self.input_folder}' 폴더에 URL 파일(.txt)이 없습니다.")
                messagebox.showinfo("정보", f"'url_lists' 폴더에 다운로드할 URL 목록 파일을 넣어주세요.")
                self.is_downloading = False
                self.download_btn.config(text="다운로드 시작", command=self.start_download, state='normal')
                return

            total_urls, all_files_lines = 0, {}
            for url_file in url_files:
                with open(url_file, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    if lines:
                        all_files_lines[url_file] = lines
                        total_urls += len(lines)
            if total_urls == 0:
                self.log("처리할 유효한 URL이 없습니다.")
                messagebox.showinfo("정보", "선택된 파일에 유효한 URL이 없습니다.")
                return

            self.progress_bar['maximum'] = total_urls
            self.log(f"총 {len(all_files_lines)}개 파일, {total_urls}개 URL 처리 시작")
            
            overall_success, overall_fail, processed_urls = 0, 0, 0
            delay = float(self.delay_var.get())
            
            use_hybrid_mode = self.hybrid_mode_var.get()
            site_cookies = {}

            for url_file, lines in all_files_lines.items():
                file_basename = os.path.basename(url_file)
                subfolder_name = os.path.splitext(file_basename)[0]
                current_save_folder = os.path.join(self.output_folder, subfolder_name)
                
                # --- 완료된 폴더 건너뛰기 기능 ---
                if os.path.exists(current_save_folder):
                    try:
                        downloaded_count = len([name for name in os.listdir(current_save_folder) if name.endswith('.txt')])
                        if downloaded_count >= len(lines):
                            self.log(f"--- '{file_basename}'은(는) 이미 모든 파일이 다운로드되었습니다 (건너뜁니다) ---")
                            # 전체 진행률을 한번에 업데이트
                            processed_urls += len(lines)
                            self.progress_bar['value'] = processed_urls -1
                            continue
                    except Exception as e:
                        self.log(f"폴더 검사 중 오류 발생: {e}")

                os.makedirs(current_save_folder, exist_ok=True)
                self.log(f"--- '{file_basename}' 처리 시작 ---")

                for i, line in enumerate(lines, 1):
                    if self.stop_requested:
                        break
                    
                    processed_urls += 1
                    self.last_activity_time = time.time() # URL 처리 시작 시 활동 시간 갱신
                    
                    # --- 주기적인 휴식 시간 제거 ---
                    # if processed_urls > 1 and (processed_urls - 1) % 50 == 0:
                    #     long_break_time = random.randint(180, 300) # 3분 ~ 5분
                    #     self.log(f"50개 항목 처리 완료. {long_break_time}초 동안 긴 휴식을 시작합니다...")
                    #     time.sleep(long_break_time)
                    #     self.log("긴 휴식을 마치고 다운로드를 재개합니다.")

                    try:
                        self.progress_var.set(f"전체 진행: {processed_urls}/{total_urls}")
                        self.progress_bar['value'] = processed_urls - 1
                        
                        if '|' not in line:
                            self.log(f"[{i}/{len(lines)}] 잘못된 형식: {line}"); overall_fail += 1; continue
                        title, url = [x.strip() for x in line.split('|', 1)]
                        if not title or not url:
                            self.log(f"[{i}/{len(lines)}] 빈 제목 또는 URL"); overall_fail += 1; continue
                            
                        safe_title = "".join(c for c in title if c.isalnum() or c in ' -_')[:50]
                        # --- 파일 이름에서 번호 제거 ---
                        filename = f"{safe_title}.txt"
                        filepath = os.path.join(current_save_folder, filename)

                        # --- 오류 파일 자동 재시도 (글자 수 기준) ---
                        if os.path.exists(filepath):
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    file_content = f.read()
                                
                                content_len = len(file_content)
                                error_keywords = ["오류", "삭제", "실패", "Error", "Fail", "Cloudflare"]
                                has_error_keyword = any(keyword in file_content for keyword in error_keywords)
                                has_url = "http://" in file_content or "https://" in file_content

                                is_error_file = False
                                reason = ""

                                # 규칙 1: 내용에 URL이 있으면서 글자수가 3000자 미만일 때
                                if has_url and content_len < 3000:
                                    is_error_file = True
                                    reason = f"URL 포함 및 글자 수 부족({content_len}자)"
                                # 규칙 2: 글자수가 3000자 미만이면서 오류 키워드가 있을 때
                                elif content_len < 3000 and has_error_keyword:
                                    is_error_file = True
                                    reason = f"글자 수 부족({content_len}자) 및 오류 키워드 포함"

                                if is_error_file:
                                    retry_count = self.download_state.get(filepath, 0)
                                    if retry_count < 5:
                                        self.log(f"[{i}/{len(lines)}] 오류 파일 감지 ({reason}). 재시도 {retry_count + 1}/5: {filename}")
                                        self.download_state[filepath] = retry_count + 1
                                    else:
                                        self.log(f"[{i}/{len(lines)}] 5회 재시도 실패. {filename} 파일을 [주의] 태그와 함께 보존합니다.")
                                        warning_filename = f"[주의] {filename}"
                                        warning_filepath = os.path.join(current_save_folder, warning_filename)
                                        if not os.path.exists(warning_filepath):
                                            os.rename(filepath, warning_filepath)
                                        self.download_state.pop(filepath, None)
                                        overall_success += 1
                                        continue
                                else:
                                    self.log(f"[{i}/{len(lines)}] 이미 존재함: {filename} (건너뜁니다)")
                                    # 정상 파일이므로 재시도 횟수 초기화
                                    self.download_state.pop(filepath, None)
                                    self.last_activity_time = time.time()
                                    overall_success += 1
                                    continue
                            except Exception as e:
                                self.log(f"파일 읽기 오류: {e} (재시도합니다)")

                        content = ""
                        driver = None
                        
                        # --- 하이브리드 모드 로직 ---
                        if use_hybrid_mode:
                            from urllib.parse import urlparse
                            from bs4 import BeautifulSoup
                            domain = urlparse(url).netloc
                            
                            # 1. 빠른 다운로드 시도
                            if domain in site_cookies:
                                try:
                                    self.log(f"빠른 다운로드 시도: {url[:70]}...")
                                    response = requests.get(url, cookies=site_cookies[domain], headers=self.session.headers, timeout=20)
                                    if response.status_code == 200 and 'Cloudflare' not in response.text and 'challenge' not in response.text:
                                        soup = BeautifulSoup(response.text, 'html.parser')
                                        for selector in ['#novel_content', '.novel-content', '.view_content', '.entry-content', '.post-content', '.content']:
                                            elements = soup.select(selector)
                                            if elements: content = elements[0].get_text(strip=True); break
                                        if not content:
                                            paras = soup.find_all('p')
                                            content = '\n\n'.join(p.get_text(strip=True) for p in paras if p.get_text(strip=True))
                                        self.log("빠른 다운로드 성공!")
                                    else:
                                        self.log(f"빠른 다운로드 실패 (상태: {response.status_code}). 브라우저로 전환합니다.")
                                except Exception as e:
                                    self.log(f"빠른 다운로드 오류: {e}. 브라우저로 전환합니다.")

                        # 2. Selenium을 이용한 일반 다운로드 (하이브리드 실패 또는 비활성화 시)
                        if not content:
                            self.log(f"[{i}/{len(lines)}] 다운로드 중: {title} ({file_basename})")
                            start_time = time.time()
                            try:
                                # ... (기존 Selenium 로직) ...
                                import undetected_chromedriver as uc
                                from selenium.webdriver.common.by import By
                                from selenium.webdriver.support.ui import WebDriverWait
                                from selenium.webdriver.support import expected_conditions as EC
                                from selenium.webdriver.common.action_chains import ActionChains
                                import pyautogui

                                options = uc.ChromeOptions()
                                options.add_argument('--no-sandbox')
                                options.add_argument('--disable-dev-shm-usage')
                                options.add_argument('--disable-blink-features=AutomationControlled')
                                
                                self.log("브라우저 실행 중 (최대 45초)...")
                                
                                driver_instance = [None]
                                def create_driver():
                                    try:
                                        # --- 브라우저 버전을 138로 명시하여 버전 불일치 문제 해결 ---
                                        driver_instance[0] = uc.Chrome(options=options, use_subprocess=True, version_main=138)
                                    except Exception as e:
                                        driver_instance[0] = e
                                driver_thread = threading.Thread(target=create_driver)
                                driver_thread.start()
                                driver_thread.join(timeout=45)
                                if driver_thread.is_alive(): raise TimeoutError("브라우저 실행 시간이 45초를 초과했습니다.")
                                if isinstance(driver_instance[0], Exception): raise driver_instance[0]
                                driver = driver_instance[0]
                                
                                self.log(f"  > 브라우저 실행 완료 ({time.time() - start_time:.2f}초)")
                                driver.set_page_load_timeout(60)
                                driver.set_window_size(1920, 1080)
                                self.log("페이지 로딩 시도 (최대 60초)...")
                                load_start_time = time.time()
                                driver.get(url)
                                self.log(f"  > 페이지 로딩 완료 ({time.time() - load_start_time:.2f}초)")
                                
                                if not self.coord_click_var.get():
                                    self.log("Cloudflare 페이지 로딩 및 인증 시도...")
                                    time.sleep(1)
                                    try:
                                        wait = WebDriverWait(driver, 5)
                                        wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, 'iframe[src*="challenges.cloudflare.com"]')))
                                        checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="checkbox"]')))
                                        time.sleep(random.uniform(0.3, 0.7))
                                        ActionChains(driver).move_to_element(checkbox).click().perform()
                                        self.log("인증 버튼 클릭 성공.")
                                    except Exception:
                                        self.log("인증 버튼이 없거나 이미 통과되었습니다.")
                                    finally:
                                        driver.switch_to.default_content()

                                self.log("본문 로딩 대기 중...")
                                extract_start_time = time.time()
                                try:
                                    wait = WebDriverWait(driver, 30)
                                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#novel_content, .novel-content, .view_content, .entry-content')))
                                    self.log(f"  > 본문 로딩 성공! ({time.time() - extract_start_time:.2f}초)")
                                    for selector in ['#novel_content', '.novel-content', '.view_content', '.entry-content', '.post-content', '.content']:
                                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                                        if elements: content = elements[0].text.strip(); break
                                    if not content:
                                        paras = driver.find_elements(By.TAG_NAME, 'p')
                                        content = '\n\n'.join(p.text.strip() for p in paras if p.text.strip())
                                except Exception as wait_e:
                                    self.log(f"  > 본문 로딩 실패: {str(wait_e).splitlines()[0]} ({time.time() - extract_start_time:.2f}초)")
                                    time.sleep(2)
                                    content = f"Cloudflare 우회 실패 또는 본문 없음\nURL: {url}"

                                # 3. 하이브리드 모드를 위해 인증 정보 저장
                                if use_hybrid_mode and "실패" not in content and "오류" not in content:
                                    self.log("인증 정보를 추출하여 다음 빠른 다운로드를 위해 저장합니다.")
                                    cookies_dict = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
                                    site_cookies[urlparse(url).netloc] = cookies_dict

                                if len(content) < 50:
                                    html_source = driver.page_source
                                    html_filename = f"{safe_title}_html.txt"
                                    html_filepath = os.path.join(current_save_folder, html_filename)
                                    with open(html_filepath, 'w', encoding='utf-8') as html_f:
                                        html_f.write(html_source)
                                    content += f"\n\n[본문 HTML이 {html_filename}로 저장됨]"
                            
                            except Exception as e:
                                content = f"Selenium 오류: {str(e)}\nURL: {url}"
                            
                            finally:
                                if driver:
                                    self.log("브라우저를 닫습니다...")
                                    try:
                                        driver.quit()
                                        self.log(f"  > 브라우저 닫기 완료. (총 소요 시간: {time.time() - start_time:.2f}초)")
                                    except Exception as e:
                                        self.log(f"  > 브라우저 닫기 중 오류 발생 (이미 닫혔을 수 있음): {e}")
                        
                        filepath = os.path.join(current_save_folder, filename)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                            
                        self.log(f"[{i}/{len(lines)}] 저장 완료: {len(content)} 문자")
                        self.last_activity_time = time.time()
                        overall_success += 1
                        if processed_urls < total_urls: time.sleep(delay)
                            
                    except Exception as e:
                        self.log(f"[{i}/{len(lines)}] 처리 중 심각한 오류: {str(e)}")
                        overall_fail += 1
                    finally:
                        self.log(f"==> URL 처리 완료: {url[:70]}...")
                
                if self.stop_requested:
                    self.log("중지 요청을 확인하여 다음 파일 처리를 중단합니다.")
                    break
                    
            self.progress_bar['value'] = total_urls
            self.progress_var.set(f"완료: 성공 {overall_success}, 실패 {overall_fail}")
            self.log(f"전체 다운로드 완료! 성공: {overall_success}, 실패: {overall_fail}")
            messagebox.showinfo("완료", f"모든 파일의 다운로드가 완료되었습니다!\n성공: {overall_success}개\n실패: {overall_fail}개")
            
        except Exception as e:
            self.log(f"오류 발생: {str(e)}")
            messagebox.showerror("오류", f"오류가 발생했습니다:\n{str(e)}")
        finally:
            # --- 재시도 횟수 상태 저장 ---
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.download_state, f, indent=4, ensure_ascii=False)
            self.log("다운로드 상태를 저장했습니다.")

            self.is_downloading = False
            self.download_btn.config(text="다운로드 시작", command=self.start_download, state='normal')
            if self.stop_requested:
                self.log("다운로드가 중지되었습니다.")
                self.progress_var.set("중지됨")
            self.stop_requested = False

    def fill_missing_episodes(self):
        """선택한 폴더와 원본 URL 파일을 비교하여 빠진 화의 URL 목록을 생성합니다."""
        import re
        
        folder_path = filedialog.askdirectory(
            title="빠진 화를 채울 소설 폴더 선택",
            initialdir=self.output_folder
        )
        if not folder_path:
            return

        folder_name = os.path.basename(folder_path)
        self.log(f"--- '{folder_name}' 폴더의 빠진 화수 채우기 시작 ---")

        try:
            # 1. 원본 URL 목록 파일 찾기
            source_url_file = os.path.join(self.input_folder, f"{folder_name}.txt")
            if not os.path.exists(source_url_file):
                self.log(f"원본 URL 파일을 찾을 수 없습니다: {source_url_file}")
                messagebox.showerror("오류", f"'url_lists' 폴더에 '{folder_name}.txt' 파일이 없습니다.")
                return

            # 2. 원본 파일에서 모든 화 정보 읽기
            with open(source_url_file, 'r', encoding='utf-8') as f:
                all_lines = [line.strip() for line in f if line.strip() and '|' in line]
            
            if not all_lines:
                self.log("원본 URL 파일에 내용이 없습니다."); return

            # 3. 현재 다운로드된 파일에서 화 번호 파악
            downloaded_files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
            downloaded_ep_numbers = set()
            for filename in downloaded_files:
                numbers = re.findall(r'\d+', filename)
                if numbers:
                    downloaded_ep_numbers.add(numbers[-1]) # 문자열 형태로 저장하여 비교

            # 4. 빠진 화의 전체 라인 찾기
            missing_lines = []
            for line in all_lines:
                title = line.split('|')[0].strip()
                numbers_in_title = re.findall(r'\d+', title)
                if numbers_in_title:
                    ep_num_str = numbers_in_title[-1]
                    if ep_num_str not in downloaded_ep_numbers:
                        missing_lines.append(line)

            if not missing_lines:
                self.log("빠진 화가 없습니다.")
                messagebox.showinfo("완료", "빠진 화가 없습니다.")
                return

            self.log(f"총 {len(missing_lines)}개의 빠진 화를 찾았습니다.")

            # 5. 임시 다운로드 목록 생성
            output_filename = f"_빠진화_{folder_name}.txt"
            output_filepath = os.path.join(self.input_folder, output_filename)
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(missing_lines))

            self.log(f"'{output_filename}' 파일에 빠진 화 {len(missing_lines)}개의 URL 목록을 생성했습니다.")
            self.log("'다운로드 시작' 버튼을 눌러 빠진 화 다운로드를 시작하세요.")
            messagebox.showinfo("목록 생성 완료", f"'url_lists' 폴더에 '{output_filename}'이 생성되었습니다.\n\n'다운로드 시작' 버튼을 눌러 빠진 화를 채우세요.")

        except Exception as e:
            self.log(f"빠진 화수 채우기 중 오류 발생: {e}")
            messagebox.showerror("오류", f"빠진 화수 채우기 중 오류가 발생했습니다:\n{e}")

    def inspect_and_clean_folder(self):
        """'downloaded_novels' 폴더 전체의 오류, 중복, 특정 키워드 파일을 정리합니다."""
        import re
        keyword_to_delete = "newtoki"
        if not os.path.exists(self.output_folder):
            messagebox.showinfo("정보", f"'downloaded_novels' 폴더를 찾을 수 없습니다.")
            return

        self.log(f"--- '{self.output_folder}' 전체 폴더 검사 및 정리 시작 ---")
        total_deleted_count = 0
        try:
            subfolders = [d.path for d in os.scandir(self.output_folder) if d.is_dir()]
            if not subfolders:
                self.log("검사할 하위 폴더가 없습니다."); return

            for folder_path in subfolders:
                self.log(f"==> '{os.path.basename(folder_path)}' 폴더 검사 중...")
                all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.txt')]
                
                # 1단계: 오류 파일 삭제
                self.log("  1단계: 오류 파일 검사...")
                valid_files = []
                for f_path in all_files:
                    try:
                        with open(f_path, 'r', encoding='utf-8') as f: file_content = f.read()
                        content_len = len(file_content)
                        error_keywords = ["오류", "삭제", "실패", "Error", "Fail", "Cloudflare"]
                        has_error_keyword = any(keyword in file_content for keyword in error_keywords)
                        has_url = "http://" in file_content or "https://" in file_content
                        is_error_file = (has_url and content_len < 3000) or (content_len < 3000 and has_error_keyword)

                        if is_error_file:
                            self.log(f"    > 오류 파일 삭제: {os.path.basename(f_path)}")
                            os.remove(f_path); total_deleted_count += 1
                        else:
                            valid_files.append(f_path)
                    except Exception as e:
                        self.log(f"    > 파일 처리 중 오류: {e}")

                # 2단계: 중복 파일 삭제
                self.log("  2단계: 중복 파일 검사...")
                episode_groups = {}
                non_duplicate_files = []
                for f_path in valid_files:
                    filename = os.path.basename(f_path)
                    numbers = re.findall(r'\d+', filename)
                    if numbers:
                        episode_key = numbers[-1]
                        if episode_key not in episode_groups: episode_groups[episode_key] = []
                        episode_groups[episode_key].append(f_path)
                    else:
                        non_duplicate_files.append(f_path)

                for ep_num, file_list in episode_groups.items():
                    if len(file_list) > 1:
                        file_list.sort(key=os.path.getmtime, reverse=True)
                        non_duplicate_files.append(file_list[0])
                        for file_to_delete in file_list[1:]:
                            self.log(f"    > 중복 파일 삭제: {os.path.basename(file_to_delete)}")
                            os.remove(file_to_delete); total_deleted_count += 1
                    else:
                        non_duplicate_files.append(file_list[0])
                
                # 3단계: 뉴토끼 파일 삭제
                self.log(f"  3단계: '{keyword_to_delete}' 키워드 검사...")
                for f_path in non_duplicate_files:
                    try:
                        with open(f_path, 'r', encoding='utf-8') as f: content = f.read()
                        if keyword_to_delete in content:
                            self.log(f"    > 키워드 파일 삭제: {os.path.basename(f_path)}")
                            os.remove(f_path); total_deleted_count += 1
                    except Exception as e:
                        self.log(f"    > 파일 처리 중 오류: {e}")

            if total_deleted_count > 0:
                self.log(f"총 {total_deleted_count}개의 불필요한 파일을 삭제했습니다.")
                messagebox.showinfo("정리 완료", f"총 {total_deleted_count}개의 불필요한 파일을 삭제했습니다.")
            else:
                self.log("삭제할 파일이 없습니다. 모든 폴더가 깨끗합니다.")
                messagebox.showinfo("정리 완료", "삭제할 파일이 없습니다.")

        except Exception as e:
            self.log(f"파일 검사 중 오류 발생: {e}")
            messagebox.showerror("오류", f"파일 검사 중 오류가 발생했습니다:\n{e}")

    def run(self):
        self.root.mainloop()

def main():
    try:
        app = WebnovelDownloader()
        app.run()
    except Exception as e:
        print(f"프로그램 실행 중 오류: {e}")
        input("Enter를 눌러 종료...")

if __name__ == "__main__":
    main()
