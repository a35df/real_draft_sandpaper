import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import os
import threading
from pathlib import Path

class NovelSplitterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔥 웹소설 분할 프로그램 GUI")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 변수 초기화
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar(value="episodes")
        self.selected_pattern = tk.StringVar(value="자동 감지")
        self.keep_original_numbers = tk.BooleanVar(value=False)  # 원본 번호 유지 여부
        
        # 패턴 목록 - 더 정확한 매칭을 위해 개선
        self.patterns = {
            "자동 감지": "auto",
            "1화, 2화 형식 (줄 시작)": r'^(\d+화)',
            "제1화, 제2화 형식 (줄 시작)": r'^(제\s*\d+화)',
            "Episode 1, Episode 2 형식": r'^(Episode\s*\d+)',
            "1장, 2장 형식 (줄 시작)": r'^(\d+장)',
            "Chapter 1, Chapter 2 형식": r'^(Chapter\s*\d+)',
            "엄격한 화 구분 (앞뒤 공백)": r'(?:^|\n\n)(\d+화)(?:\s|$)',
        }
        
        self.create_widgets()
        self.center_window()
    
    def center_window(self):
        """창을 화면 중앙에 배치"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """GUI 위젯들을 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="🔥 웹소설 분할 프로그램", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 파일 선택 섹션
        file_frame = ttk.LabelFrame(main_frame, text="📁 파일 선택", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(file_frame, text="원본 소설 파일:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        file_entry_frame = ttk.Frame(file_frame)
        file_entry_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.file_entry = ttk.Entry(file_entry_frame, textvariable=self.input_file, width=60)
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(file_entry_frame, text="찾아보기", command=self.select_file).grid(row=0, column=1)
        
        file_entry_frame.columnconfigure(0, weight=1)
        
        # 출력 폴더 설정
        ttk.Label(file_frame, text="출력 폴더:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        output_frame = ttk.Frame(file_frame)
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_dir, width=60)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(output_frame, text="폴더 선택", command=self.select_output_dir).grid(row=0, column=1)
        
        output_frame.columnconfigure(0, weight=1)
        
        # 패턴 선택 섹션
        pattern_frame = ttk.LabelFrame(main_frame, text="🔍 분할 패턴 선택", padding="10")
        pattern_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(pattern_frame, text="화 구분 패턴:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        pattern_combo = ttk.Combobox(pattern_frame, textvariable=self.selected_pattern, 
                                   values=list(self.patterns.keys()), state="readonly", width=40)
        pattern_combo.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 파일명 옵션
        ttk.Label(pattern_frame, text="파일명 방식:").grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        
        numbering_frame = ttk.Frame(pattern_frame)
        numbering_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        ttk.Radiobutton(numbering_frame, text="텍스트 순서대로 (001화, 002화, ...)", 
                       variable=self.keep_original_numbers, value=False).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(numbering_frame, text="원본 번호 유지 (1화→001화, 5화→005화, ...)", 
                       variable=self.keep_original_numbers, value=True).grid(row=1, column=0, sticky=tk.W)
        
        # 실행 버튼 섹션
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        self.run_button = ttk.Button(button_frame, text="🚀 분할 실행", 
                                   command=self.run_split, style="Accent.TButton")
        self.run_button.grid(row=0, column=0, padx=(0, 10))
        
        self.sample_button = ttk.Button(button_frame, text="📝 샘플 파일 생성", 
                                      command=self.create_sample)
        self.sample_button.grid(row=0, column=1, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="🗑️ 로그 지우기", 
                                     command=self.clear_log)
        self.clear_button.grid(row=0, column=2, padx=(0, 10))
        
        self.preview_button = ttk.Button(button_frame, text="👀 미리보기", 
                                       command=self.preview_split)
        self.preview_button.grid(row=0, column=3)
        
        # 진행률 표시
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 로그 출력 섹션
        log_frame = ttk.LabelFrame(main_frame, text="📄 실행 로그", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        file_frame.columnconfigure(0, weight=1)
        pattern_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 초기 로그 메시지
        self.log("🔥 웹소설 분할 프로그램 GUI가 시작되었습니다!")
        self.log("📁 원본 소설 파일을 선택하고 분할을 실행해보세요.")
    
    def log(self, message):
        """로그 메시지를 출력"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """로그를 지움"""
        self.log_text.delete(1.0, tk.END)
        self.log("🗑️ 로그가 지워졌습니다.")
    
    def select_file(self):
        """파일 선택 대화상자"""
        filename = filedialog.askopenfilename(
            title="웹소설 파일 선택",
            filetypes=[
                ("텍스트 파일", "*.txt"),
                ("모든 파일", "*.*")
            ]
        )
        if filename:
            self.input_file.set(filename)
            self.log(f"📖 파일 선택됨: {os.path.basename(filename)}")
    
    def select_output_dir(self):
        """출력 폴더 선택 대화상자"""
        dirname = filedialog.askdirectory(title="출력 폴더 선택")
        if dirname:
            self.output_dir.set(dirname)
            self.log(f"📁 출력 폴더 선택됨: {dirname}")
    
    def create_sample(self):
        """샘플 파일 생성"""
        sample_content = """프롤로그
이것은 GUI 버전 테스트용 샘플 웹소설입니다.
중간에 "5화나 6화쯤 되면 재미있어질 것 같다"는 말이 나와도 분할되지 않아야 합니다.

1화 새로운 시작
평범한 고등학생 김민수는 어느 날 아침, 눈을 뜨자마자 이상한 창이 떠있는 것을 발견했다.

[시스템이 활성화되었습니다]
[플레이어: 김민수]
[레벨: 1]

"이게 뭐지?" 민수는 눈을 비비며 중얼거렸다. 하지만 창은 사라지지 않았다.
"아마 10화 정도 되면 익숙해질 거야"라고 생각했지만, 이 말은 제목이 아니므로 분할되지 않습니다.

학교에 가는 길에도 계속 떠있던 그 창은, 민수의 인생을 완전히 바꿔놓을 시작이었다.

2화 능력의 각성
학교 체육시간, 민수는 자신의 신체 능력이 이상하게 향상된 것을 느꼈다.

100미터를 10초대로 뛰어내고, 턱걸이를 30개나 할 수 있었다.

"민수야, 너 언제 이렇게 운동신경이 좋아졌어?" 친구 태호가 놀라며 물었다.
"3화에서 설명할게"라고 농담했지만, 이것도 본문이므로 분할 기준이 아닙니다.

민수는 대답할 수 없었다. 자신도 모르는 일이었으니까.

그 순간 또다시 시스템 창이 나타났다.

[체력 스탯이 10 증가했습니다]
[새로운 스킬을 습득했습니다: 강화술 Lv.1]

3화 숨겨진 세계
방과 후, 민수는 혼자 남아서 새로운 능력을 실험해보고 있었다.

"강화술!" 하고 외치자, 손에 푸른 빛이 감돌며 주먹의 힘이 강해지는 것을 느꼈다.

그 때, 교실 문이 열리며 한 소녀가 들어왔다.

"역시 각성자였군요." 소녀는 미소를 지으며 말했다.

"각성자? 그게 뭐예요?" 민수가 당황하며 물었다.

"저처럼 시스템의 힘을 받은 사람들을 말해요. 저는 이지은이에요. 같은 반이죠."

지은이는 손을 들어 보이자, 작은 불꽃이 손바닥 위에서 춤을 추었다.
"보통 4화 정도에서 이런 능력자들이 나타나죠"라고 설명했지만, 이것도 대화문이므로 무시됩니다.

에필로그
이것으로 샘플 이야기가 끝납니다. 중간에 "7화", "8화" 같은 단어가 나와도 줄 시작이 아니면 분할되지 않습니다."""
        
        try:
            sample_path = "sample_novel.txt"
            with open(sample_path, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            
            self.input_file.set(os.path.abspath(sample_path))
            self.log(f"📄 샘플 파일이 생성되었습니다: {sample_path}")
            messagebox.showinfo("완료", "개선된 샘플 파일이 생성되었습니다!\n\n중간에 'n화' 단어가 있어도 정확히 분할됩니다.")
            
        except Exception as e:
            self.log(f"❌ 샘플 파일 생성 실패: {str(e)}")
            messagebox.showerror("오류", f"샘플 파일 생성에 실패했습니다: {str(e)}")
    
    def preview_split(self):
        """분할 결과를 미리보기"""
        if not self.input_file.get():
            messagebox.showwarning("경고", "원본 소설 파일을 선택해주세요.")
            return
        
        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("오류", "선택한 파일이 존재하지 않습니다.")
            return
        
        try:
            filename = self.input_file.get()
            
            # 파일 읽기
            with open(filename, 'r', encoding='utf-8') as file:
                text = file.read()
            
            # 패턴 선택 및 찾기 - 더 정확한 매칭
            selected = self.selected_pattern.get()
            if selected == "자동 감지":
                patterns = [
                    r'^(\d+화)',           # 줄 시작에 있는 "1화", "2화"...
                    r'^(제\s*\d+화)',      # 줄 시작에 있는 "제1화", "제 1화"...
                    r'^(Episode\s*\d+)',   # 줄 시작에 있는 "Episode 1", "Episode 2"...
                    r'^(\d+장)',           # 줄 시작에 있는 "1장", "2장"...
                    r'^(Chapter\s*\d+)',   # 줄 시작에 있는 "Chapter 1", "Chapter 2"...
                    r'(?:^|\n\n)(\d+화)(?:\s|$)',  # 앞뒤로 공백이나 줄바꿈이 있는 경우
                ]
                
                used_pattern = None
                for pattern in patterns:
                    matches = re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
                    if matches:
                        used_pattern = pattern
                        break
            else:
                used_pattern = self.patterns[selected]
            
            if not used_pattern:
                messagebox.showerror("오류", "에피소드 구분자를 찾을 수 없습니다.")
                return
            
            # 패턴의 위치를 순서대로 찾기
            episodes_data = []
            for match in re.finditer(used_pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                title = match.group(1)
                number_match = re.search(r'(\d+)', title)
                if number_match:
                    ep_num = int(number_match.group(1))
                    episodes_data.append({
                        'number': ep_num,
                        'title': title,
                    })
            
            # ❌ 정렬하지 않음! 텍스트에 나타나는 순서 그대로 유지
            # episodes_data.sort(key=lambda x: x['number'])  # 이 줄을 제거
            
            # 미리보기 창 생성
            preview_window = tk.Toplevel(self.root)
            preview_window.title("🔍 분할 미리보기")
            preview_window.geometry("500x400")
            
            # 리스트박스로 에피소드 목록 표시
            frame = ttk.Frame(preview_window, padding="10")
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text=f"총 {len(episodes_data)}개의 에피소드가 발견되었습니다:", 
                     font=("Arial", 12, "bold")).pack(pady=(0, 10))
            
            listbox_frame = ttk.Frame(frame)
            listbox_frame.pack(fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(listbox_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            
            for i, episode in enumerate(episodes_data):
                listbox.insert(tk.END, f"{i+1:03d}화: {episode['title']} (원본: {episode['number']}화)")
            
            ttk.Button(frame, text="확인", 
                      command=preview_window.destroy).pack(pady=(10, 0))
            
        except Exception as e:
            messagebox.showerror("오류", f"미리보기 중 오류가 발생했습니다:\n{str(e)}")
    
    def run_split(self):
        """분할 작업을 별도 스레드에서 실행"""
        if not self.input_file.get():
            messagebox.showwarning("경고", "원본 소설 파일을 선택해주세요.")
            return
        
        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("오류", "선택한 파일이 존재하지 않습니다.")
            return
        
        # UI 비활성화
        self.run_button.config(state="disabled")
        self.progress.start()
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=self.split_novel)
        thread.daemon = True
        thread.start()
    
    def split_novel(self):
        """실제 분할 작업 수행"""
        try:
            filename = self.input_file.get()
            output_dir = self.output_dir.get()
            
            self.log(f"🚀 분할 작업을 시작합니다...")
            self.log(f"📖 파일: {os.path.basename(filename)}")
            self.log(f"📁 출력 폴더: {output_dir}")
            
            # 파일 읽기
            with open(filename, 'r', encoding='utf-8') as file:
                text = file.read()
            
            self.log(f"✅ 파일을 성공적으로 읽었습니다. (크기: {len(text):,} 글자)")
            
            # 패턴 선택 및 찾기 - 더 정확한 매칭
            selected = self.selected_pattern.get()
            if selected == "자동 감지":
                patterns = [
                    r'^(\d+화)',           # 줄 시작에 있는 "1화", "2화"...
                    r'^(제\s*\d+화)',      # 줄 시작에 있는 "제1화", "제 1화"...
                    r'^(Episode\s*\d+)',   # 줄 시작에 있는 "Episode 1", "Episode 2"...
                    r'^(\d+장)',           # 줄 시작에 있는 "1장", "2장"...
                    r'^(Chapter\s*\d+)',   # 줄 시작에 있는 "Chapter 1", "Chapter 2"...
                    r'(?:^|\n\n)(\d+화)(?:\s|$)',  # 앞뒤로 공백이나 줄바꿈이 있는 경우
                ]
                
                used_pattern = None
                for pattern in patterns:
                    matches = re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
                    if matches:
                        used_pattern = pattern
                        self.log(f"🔍 패턴 '{pattern}' 사용하여 분할합니다. ({len(matches)}개 발견)")
                        break
            else:
                used_pattern = self.patterns[selected]
                matches = re.findall(used_pattern, text, flags=re.IGNORECASE | re.MULTILINE)
                self.log(f"🔍 선택된 패턴 '{used_pattern}' 사용하여 분할합니다. ({len(matches)}개 발견)")
            
            if not used_pattern:
                self.log("❌ 에피소드 구분자를 찾을 수 없습니다.")
                self.root.after(0, lambda: messagebox.showerror("오류", "에피소드 구분자를 찾을 수 없습니다. 파일 내용을 확인해주세요."))
                return
            
            # 출력 폴더 생성
            os.makedirs(output_dir, exist_ok=True)
            
            # 패턴의 위치를 텍스트 순서대로 찾기 (정렬하지 않음!)
            episodes_data = []
            for match in re.finditer(used_pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                start_pos = match.start()
                title = match.group(1)
                
                # 숫자 추출
                number_match = re.search(r'(\d+)', title)
                if number_match:
                    ep_num = int(number_match.group(1))
                    
                    # 추가 검증: 제목이 줄의 시작이나 독립된 줄에 있는지 확인
                    line_start = text.rfind('\n', 0, start_pos) + 1
                    line_end = text.find('\n', start_pos)
                    if line_end == -1:
                        line_end = len(text)
                    
                    current_line = text[line_start:line_end].strip()
                    
                    # 제목만 있는 줄이거나, 제목으로 시작하는 줄인지 확인
                    if (current_line == title or 
                        current_line.startswith(title + ' ') or
                        current_line == title.strip()):
                        
                        episodes_data.append({
                            'number': ep_num,
                            'title': title,
                            'start_pos': start_pos,
                            'match_obj': match,
                            'line': current_line
                        })
                        self.log(f"🔍 발견된 제목: '{current_line}' (위치: {start_pos})")
                    else:
                        self.log(f"⚠️ 무시된 패턴: '{title}' (전체 줄: '{current_line}')")
            
            # ❌ 정렬하지 않음! 텍스트에 나타나는 순서 그대로 유지
            # episodes_data.sort(key=lambda x: x['number'])  # 이 줄을 제거
            self.log(f"📊 총 {len(episodes_data)}개의 유효한 에피소드를 텍스트 순서대로 처리합니다.")
            
            saved_count = 0
            
            # 각 에피소드의 내용 추출 및 저장 (텍스트 순서대로)
            for i, episode in enumerate(episodes_data):
                try:
                    # 현재 에피소드의 시작 위치
                    current_start = episode['start_pos']
                    
                    # 다음 에피소드의 시작 위치 (마지막이면 텍스트 끝까지)
                    if i + 1 < len(episodes_data):
                        next_start = episodes_data[i + 1]['start_pos']
                        content = text[current_start:next_start].strip()
                    else:
                        content = text[current_start:].strip()
                    
                    # 제목과 내용 분리
                    lines = content.split('\n', 1)
                    if len(lines) > 1:
                        episode_content = lines[1].strip()
                    else:
                        episode_content = ""
                    
                    # 파일명 생성 방식 선택
                    if self.keep_original_numbers.get():
                        # 원본 번호 유지
                        filename_out = os.path.join(output_dir, f"{episode['number']:03d}화.txt")
                        self.log(f"✅ 저장 완료: {os.path.basename(filename_out)} (원본: {episode['title']}, {len(episode_content):,} 글자)")
                    else:
                        # 텍스트 순서대로 번호 매기기
                        sequence_num = i + 1
                        filename_out = os.path.join(output_dir, f"{sequence_num:03d}화.txt")
                        self.log(f"✅ 저장 완료: {os.path.basename(filename_out)} (원본: {episode['title']}, {len(episode_content):,} 글자)")
                    
                    # 파일 내용 구성 (제목 + 내용)
                    full_content = f"{episode['title']}\n\n{episode_content}"
                    
                    # 파일 저장
                    with open(filename_out, 'w', encoding='utf-8') as ep_file:
                        ep_file.write(full_content)
                    
                    saved_count += 1
                    
                except Exception as ep_error:
                    self.log(f"❌ {i+1}번째 에피소드({episode.get('title', 'Unknown')}) 저장 실패: {str(ep_error)}")
                    continue
            
            self.log(f"\n🎉 분할 완료! 총 {saved_count}개의 에피소드가 저장되었습니다!")
            self.log(f"📁 저장 위치: {os.path.abspath(output_dir)}")
            
            numbering_method = "원본 번호 유지" if self.keep_original_numbers.get() else "텍스트 순서"
            self.log(f"📋 파일명 방식: {numbering_method}")
            
            # 성공 메시지 (메인 스레드에서 실행)
            self.root.after(0, lambda: messagebox.showinfo("완료", 
                f"분할이 완료되었습니다!\n\n"
                f"저장된 에피소드: {saved_count}개\n"
                f"저장 위치: {os.path.abspath(output_dir)}\n"
                f"파일명 방식: {numbering_method}"))
            
        except Exception as e:
            self.log(f"❌ 오류 발생: {str(e)}")
            import traceback
            self.log(f"🔍 상세 오류: {traceback.format_exc()}")
            self.root.after(0, lambda: messagebox.showerror("오류", f"분할 중 오류가 발생했습니다:\n{str(e)}"))
        
        finally:
            # UI 재활성화
            self.root.after(0, self.finish_split)
    
    def finish_split(self):
        """분할 작업 완료 후 UI 상태 복원"""
        self.progress.stop()
        self.run_button.config(state="normal")

def main():
    """메인 함수"""
    root = tk.Tk()
    
    # 스타일 설정
    style = ttk.Style()
    style.theme_use('clam')  # 'clam', 'alt', 'default', 'classic' 등 사용 가능
    
    app = NovelSplitterGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.quit()

if __name__ == "__main__":
    main()
