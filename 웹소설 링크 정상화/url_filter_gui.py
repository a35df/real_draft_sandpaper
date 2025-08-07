import re
import os
import glob
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import threading

class NovelURLFilterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("웹소설 URL 필터링 프로그램")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 변수들
        self.input_files = []
        self.output_folder = tk.StringVar()
        self.is_processing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="🚀 웹소설 URL 필터링 프로그램", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 파일 선택 섹션
        file_frame = ttk.LabelFrame(main_frame, text="📁 입력 파일 선택", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(file_frame, text="URL 파일들 선택", 
                  command=self.select_files).grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(file_frame, text="폴더에서 모든 .txt 파일 선택", 
                  command=self.select_folder_files).grid(row=0, column=1)
        
        # 선택된 파일 목록
        list_frame = ttk.Frame(file_frame)
        list_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(list_frame, text="선택된 파일들:").grid(row=0, column=0, sticky=tk.W)
        
        # 리스트박스와 스크롤바
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.file_listbox = tk.Listbox(listbox_frame, height=6)
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        file_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", 
                                      command=self.file_listbox.yview)
        file_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.file_listbox.configure(yscrollcommand=file_scrollbar.set)
        
        ttk.Button(list_frame, text="선택된 파일 제거", 
                  command=self.remove_selected_file).grid(row=2, column=0, pady=(5, 0))
        
        # 출력 폴더 선택 섹션
        output_frame = ttk.LabelFrame(main_frame, text="💾 출력 폴더 선택", padding="10")
        output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(output_frame, text="저장 폴더:").grid(row=0, column=0, sticky=tk.W)
        
        folder_frame = ttk.Frame(output_frame)
        folder_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.output_folder, 
                                     state="readonly", width=60)
        self.folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(folder_frame, text="폴더 선택", 
                  command=self.select_output_folder).grid(row=0, column=1)
        
        # 필터링 옵션 섹션
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ 필터링 옵션", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.create_report_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="처리 완료 후 리포트 생성", 
                       variable=self.create_report_var).grid(row=0, column=0, sticky=tk.W)
        
        # 실행 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))
        
        self.process_button = ttk.Button(button_frame, text="🚀 필터링 시작", 
                                        command=self.start_processing, style="Accent.TButton")
        self.process_button.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(button_frame, text="❌ 종료", 
                  command=self.root.quit).grid(row=0, column=1)
        
        # 진행 상황 섹션
        progress_frame = ttk.LabelFrame(main_frame, text="📊 진행 상황", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.status_label = ttk.Label(progress_frame, text="대기 중...")
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        # 로그 섹션
        log_frame = ttk.LabelFrame(main_frame, text="📝 처리 로그", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = tk.Text(log_text_frame, height=10, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient="vertical", 
                                     command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        file_frame.columnconfigure(0, weight=1)
        listbox_frame.columnconfigure(0, weight=1)
        folder_frame.columnconfigure(0, weight=1)
        progress_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        log_text_frame.columnconfigure(0, weight=1)
        log_text_frame.rowconfigure(0, weight=1)
        
    def select_files(self):
        """개별 파일들 선택"""
        files = filedialog.askopenfilenames(
            title="URL 파일들을 선택하세요",
            filetypes=[
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ]
        )
        
        for file in files:
            if file not in self.input_files:
                self.input_files.append(file)
                self.file_listbox.insert(tk.END, os.path.basename(file))
        
        self.log(f"선택된 파일 {len(files)}개 추가됨")
        
    def select_folder_files(self):
        """폴더에서 모든 .txt 파일 선택"""
        folder = filedialog.askdirectory(title="URL 파일들이 있는 폴더를 선택하세요")
        
        if folder:
            pattern = os.path.join(folder, "*.txt")
            files = glob.glob(pattern)
            
            if files:
                for file in files:
                    if file not in self.input_files:
                        self.input_files.append(file)
                        self.file_listbox.insert(tk.END, os.path.basename(file))
                
                self.log(f"폴더에서 {len(files)}개의 .txt 파일을 찾아 추가했습니다")
            else:
                messagebox.showwarning("경고", "선택한 폴더에 .txt 파일이 없습니다.")
    
    def remove_selected_file(self):
        """선택된 파일을 목록에서 제거"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            removed_file = self.input_files.pop(index)
            self.file_listbox.delete(index)
            self.log(f"파일 제거됨: {os.path.basename(removed_file)}")
    
    def select_output_folder(self):
        """출력 폴더 선택"""
        folder = filedialog.askdirectory(title="필터링된 파일들을 저장할 폴더를 선택하세요")
        if folder:
            self.output_folder.set(folder)
            self.log(f"출력 폴더 설정됨: {folder}")
    
    def log(self, message):
        """로그 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_processing(self):
        """필터링 처리 시작"""
        if not self.input_files:
            messagebox.showerror("오류", "처리할 파일을 선택해주세요.")
            return
        
        if not self.output_folder.get():
            messagebox.showerror("오류", "출력 폴더를 선택해주세요.")
            return
        
        if self.is_processing:
            messagebox.showwarning("경고", "이미 처리 중입니다.")
            return
        
        # 별도 스레드에서 처리 실행
        self.is_processing = True
        self.process_button.configure(state="disabled", text="처리 중...")
        
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()
    
    def process_files(self):
        """파일들을 실제로 처리"""
        try:
            total_files = len(self.input_files)
            total_processed = 0
            total_filtered_links = 0
            failed_files = []
            
            self.log("=" * 50)
            self.log(f"필터링 시작: {total_files}개 파일 처리")
            self.log("=" * 50)
            
            for i, input_file in enumerate(self.input_files):
                progress = (i / total_files) * 100
                self.progress_var.set(progress)
                self.status_label.configure(text=f"처리 중: {os.path.basename(input_file)} ({i+1}/{total_files})")
                
                self.log(f"[{i+1}/{total_files}] 처리 중: {os.path.basename(input_file)}")
                
                # 출력 파일명 생성
                base_name = os.path.basename(input_file)
                if base_name.endswith(" url.txt"):
                    # "소설제목 url.txt" -> "소설제목 filtered_urls.txt"
                    novel_title = base_name[:-8]
                    output_filename = f"{novel_title} filtered_urls.txt"
                elif base_name.endswith("url.txt"):
                    # "소설제목url.txt" -> "소설제목 filtered_urls.txt"
                    novel_title = base_name[:-7]
                    output_filename = f"{novel_title} filtered_urls.txt"
                elif base_name.endswith(".txt"):
                    # "소설제목.txt" -> "소설제목 filtered_urls.txt"
                    novel_title = base_name[:-4]
                    output_filename = f"{novel_title} filtered_urls.txt"
                else:
                    # 확장자가 없는 경우
                    novel_title = base_name
                    output_filename = f"{novel_title} filtered_urls.txt"
                
                output_file = os.path.join(self.output_folder.get(), output_filename)
                
                # 필터링 수행
                filtered_count, total_count = self.filter_novel_urls(input_file, output_file)
                
                if total_count > 0:
                    self.log(f"  📊 전체 링크: {total_count}개")
                    self.log(f"  ✅ 필터링된 링크: {filtered_count}개")
                    self.log(f"  💾 저장됨: {output_filename}")
                    total_processed += 1
                    total_filtered_links += filtered_count
                    
                    if filtered_count == 0:
                        self.log("  ⚠️  경고: 유효한 소설 링크가 없습니다.")
                else:
                    self.log(f"  ❌ 파일 처리 실패")
                    failed_files.append(input_file)
                
                self.log("-" * 30)
            
            # 완료 처리
            self.progress_var.set(100)
            self.status_label.configure(text="처리 완료!")
            
            # 최종 결과
            self.log("=" * 50)
            self.log("📋 처리 완료 요약:")
            self.log(f"  ✅ 성공: {total_processed}개 파일")
            self.log(f"  📊 총 추출된 링크: {total_filtered_links}개")
            
            if failed_files:
                self.log(f"  ❌ 실패: {len(failed_files)}개 파일")
                for failed_file in failed_files:
                    self.log(f"    - {os.path.basename(failed_file)}")
            
            # 리포트 생성
            if self.create_report_var.get():
                self.create_summary_report(total_processed, total_filtered_links)
            
            self.log("🎉 모든 작업이 완료되었습니다!")
            messagebox.showinfo("완료", f"필터링이 완료되었습니다!\n\n성공: {total_processed}개 파일\n총 링크: {total_filtered_links}개")
            
        except Exception as e:
            self.log(f"❌ 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"처리 중 오류가 발생했습니다:\n{str(e)}")
        
        finally:
            self.is_processing = False
            self.process_button.configure(state="normal", text="🚀 필터링 시작")
    
    def filter_novel_urls(self, input_file, output_file):
        """개별 파일 필터링"""
        # 소설 각 화 링크 패턴: https://booktoki*.com/novel/숫자?쿼리파라미터
        novel_pattern = re.compile(r'^https?://booktoki\d*\.com/novel/\d+\?.*')
        
        # 제거할 패턴들
        remove_patterns = [
            re.compile(r'javascript:'), 
            re.compile(r'linkbn\.php'),
            re.compile(r'void\(0\)'),
            re.compile(r'#'),
            re.compile(r'mailto:'),
        ]
        
        filtered_count = 0
        total_count = 0
        
        try:
            with open(input_file, 'r', encoding='utf-8') as fin, \
                 open(output_file, 'w', encoding='utf-8') as fout:
                
                for line in fin:
                    line = line.strip()
                    total_count += 1
                    
                    if not line:
                        continue
                    
                    # "제목 | 링크" 형식인 경우 링크 부분만 검증하지만 전체 라인을 보존
                    if ' | ' in line:
                        parts = line.split(' | ')
                        if len(parts) >= 2:
                            url = parts[1].strip()  # 검증용 URL
                            original_line = line    # 원본 라인 보존
                        else:
                            continue
                    else:
                        url = line  # 링크만 있는 경우
                        original_line = line
                    
                    if not url:
                        continue
                    
                    # 소설 링크가 아니면 건너뛰기
                    if not novel_pattern.match(url):
                        continue
                    
                    # 제거 패턴에 걸리면 건너뛰기
                    if any(p.search(url) for p in remove_patterns):
                        continue
                    
                    fout.write(original_line + '\n')  # 원본 라인 전체를 저장
                    filtered_count += 1
            
            return filtered_count, total_count
        
        except Exception as e:
            self.log(f"파일 처리 오류 ({os.path.basename(input_file)}): {str(e)}")
            return 0, 0
    
    def find_novel_groups(self, lines):
        """연속된 소설 페이지 그룹들을 찾아서 반환"""
        # 소설 링크 패턴
        novel_pattern = re.compile(r'^https?://booktoki\d*\.com/novel/(\d+)\?.*')
        
        # 제거할 패턴들
        remove_patterns = [
            re.compile(r'javascript:'), 
            re.compile(r'linkbn\.php'),
            re.compile(r'void\(0\)'),
            re.compile(r'#'),
            re.compile(r'mailto:'),
        ]
        
        # 1단계: 모든 유효한 소설 링크 추출
        valid_novels = []
        for i, line in enumerate(lines):
            if not line:
                continue
            
            # "제목 | 링크" 형식 처리
            if ' | ' in line:
                parts = line.split(' | ')
                if len(parts) >= 2:
                    url = parts[1].strip()
                else:
                    continue
            else:
                url = line
            
            if not url:
                continue
            
            # 제거 패턴 확인
            if any(p.search(url) for p in remove_patterns):
                continue
            
            # 소설 링크 패턴 확인
            match = novel_pattern.match(url)
            if match:
                novel_id = match.group(1)
                prefix = novel_id[:4]  # 앞 4자리
                valid_novels.append({
                    'line_index': i,
                    'url': url,
                    'novel_id': novel_id,
                    'prefix': prefix
                })
        
        if not valid_novels:
            return []
        
        # 2단계: 연속된 그룹 찾기
        groups = []
        current_group = []
        current_prefix = None
        
        for novel in valid_novels:
            if current_prefix != novel['prefix']:
                # 새로운 소설 시작
                if current_group and len(current_group) >= 3:  # 최소 3개 이상의 화가 있어야 유효한 그룹
                    groups.append([item['url'] for item in current_group])
                current_group = [novel]
                current_prefix = novel['prefix']
            else:
                # 같은 소설의 다음 화
                # 연속성 확인 (라인 인덱스가 크게 떨어지지 않는지)
                if not current_group or (novel['line_index'] - current_group[-1]['line_index']) <= 10:
                    current_group.append(novel)
                else:
                    # 너무 떨어져 있으면 새로운 그룹 시작
                    if current_group and len(current_group) >= 3:
                        groups.append([item['url'] for item in current_group])
                    current_group = [novel]
        
        # 마지막 그룹 추가
        if current_group and len(current_group) >= 3:
            groups.append([item['url'] for item in current_group])
        
        return groups
    
    def create_summary_report(self, total_processed, total_filtered_links):
        """처리 결과 요약 리포트 생성"""
        report_filename = f"filtering_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = os.path.join(self.output_folder.get(), report_filename)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("웹소설 URL 필터링 결과 리포트\n")
                f.write("=" * 50 + "\n")
                f.write(f"처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"처리된 파일 수: {total_processed}개\n")
                f.write(f"총 추출된 링크 수: {total_filtered_links}개\n\n")
                
                f.write("처리된 파일 목록:\n")
                for file in glob.glob(os.path.join(self.output_folder.get(), "*filtered_urls.txt")):
                    try:
                        with open(file, 'r', encoding='utf-8') as filtered_file:
                            link_count = len([line for line in filtered_file if line.strip()])
                        f.write(f"  - {os.path.basename(file)}: {link_count}개 링크\n")
                    except:
                        f.write(f"  - {os.path.basename(file)}: 링크 수 확인 실패\n")
            
            self.log(f"📊 상세 리포트 생성됨: {report_filename}")
        except Exception as e:
            self.log(f"리포트 생성 실패: {str(e)}")

def main():
    root = tk.Tk()
    app = NovelURLFilterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
