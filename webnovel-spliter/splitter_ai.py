import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import os
import threading
import json
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# LLM 관련 import (선택적으로 사용)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class NovelSplitterAI:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 AI 웹소설 분할 프로그램")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 변수 초기화
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar(value="episodes")
        self.selected_method = tk.StringVar(value="Google Gemini 2.5 Flash (빠름)")
        self.api_key = tk.StringVar(value=os.getenv('GEMINI_API_KEY', '') or os.getenv('OPENAI_API_KEY', ''))
        
        # 분할 방법 목록
        self.methods = {
            "정규표현식 (빠름)": "regex",
            "Google Gemini 2.5 Flash (빠름)": "gemini_flash",
            "Google Gemini 2.5 Flash-Lite (매우 빠름)": "gemini_flash_lite",
            "Google Gemini 2.5 Pro (최고 정확도)": "gemini",
            "하이브리드 (AI + 정규식)": "hybrid"
        }
        
        self.create_widgets()
        self.center_window()
        
        # 초기화 메시지
        self.log("🚀 AI 웹소설 분할 프로그램 시작")
        if os.getenv('GEMINI_API_KEY'):
            self.log("✅ Gemini API 키가 환경변수에서 로드되었습니다")
        if os.getenv('OPENAI_API_KEY'):
            self.log("✅ OpenAI API 키가 환경변수에서 로드되었습니다")
        if not os.getenv('GEMINI_API_KEY') and not os.getenv('OPENAI_API_KEY'):
            self.log("ℹ️ API 키를 직접 입력하거나 .env 파일을 설정하세요")
        self.log("🔧 .env.example 파일을 .env로 복사하여 API 키를 설정할 수 있습니다")
    
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
        title_label = ttk.Label(main_frame, text="🤖 AI 웹소설 분할 프로그램", 
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
        
        # 분할 방법 선택 섹션
        method_frame = ttk.LabelFrame(main_frame, text="🤖 분할 방법 선택", padding="10")
        method_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(method_frame, text="분할 방법:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        method_combo = ttk.Combobox(method_frame, textvariable=self.selected_method, 
                                   values=list(self.methods.keys()), state="readonly", width=40)
        method_combo.grid(row=1, column=0, sticky=(tk.W, tk.E))
        method_combo.bind('<<ComboboxSelected>>', self.on_method_changed)
        
        # AI 설정 프레임
        self.ai_frame = ttk.LabelFrame(main_frame, text="🔧 AI 설정", padding="10")
        self.ai_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # OpenAI 설정
        self.openai_frame = ttk.Frame(self.ai_frame)
        
        ttk.Label(self.openai_frame, text="Gemini API Key:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        api_key_entry = ttk.Entry(self.openai_frame, textvariable=self.api_key, width=50, show="*")
        api_key_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.openai_frame.columnconfigure(0, weight=1)
        
        # 초기에는 AI 설정 숨김
        self.toggle_ai_settings()
        
        # 실행 버튼 섹션
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        self.run_button = ttk.Button(button_frame, text="🚀 AI 분할 실행", 
                                   command=self.run_split, style="Accent.TButton")
        self.run_button.grid(row=0, column=0, padx=(0, 10))
        
        self.sample_button = ttk.Button(button_frame, text="📝 샘플 파일 생성", 
                                      command=self.create_sample)
        self.sample_button.grid(row=0, column=1, padx=(0, 10))
        
        self.preview_button = ttk.Button(button_frame, text="👀 AI 미리보기", 
                                       command=self.preview_split)
        self.preview_button.grid(row=0, column=2, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="🗑️ 로그 지우기", 
                                     command=self.clear_log)
        self.clear_button.grid(row=0, column=3)
        
        # 진행률 표시
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 로그 출력 섹션
        log_frame = ttk.LabelFrame(main_frame, text="📄 실행 로그", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        file_frame.columnconfigure(0, weight=1)
        method_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 초기 로그 메시지
        self.log("🤖 AI 웹소설 분할 프로그램이 시작되었습니다!")
        self.log("📁 원본 소설 파일을 선택하고 AI 분할 방법을 선택해보세요.")
    
    def on_method_changed(self, event=None):
        """분할 방법이 변경될 때 호출"""
        self.toggle_ai_settings()
    
    def toggle_ai_settings(self):
        """선택된 방법에 따라 AI 설정 표시/숨김"""
        method = self.selected_method.get()
        
        if "Gemini" in method or "하이브리드" in method:
            self.openai_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            self.ai_frame.grid()
        elif "정규표현식" in method:
            self.ai_frame.grid_remove()
        else:
            self.ai_frame.grid_remove()
    
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
        """복잡한 샘플 파일 생성"""
        sample_content = """작가의 말
이 소설은 복잡한 구조를 가지고 있어서 정규표현식으로는 정확히 분할하기 어려울 수 있습니다.

프롤로그 - 시작
옛날 옛적에... 이것은 프롤로그입니다.

제1화: 새로운 세상
주인공 김민수는 평범한 학생이었다. "이 소설은 10화 정도에서 재미있어질 거야"라고 친구가 말했지만, 
이것은 실제 화 제목이 아닙니다.

어느 날 그는 이상한 능력을 얻게 되었다.

2화 - 능력의 발견
[2화는 대시가 있는 형태입니다]

민수는 자신의 능력을 시험해보기 시작했다. "3화에서 더 설명할게"라고 생각했지만, 
이것도 대화문일 뿐입니다.

Episode 3: 첫 번째 전투
영어 형태의 제목도 있습니다.

갑작스럽게 나타난 적과의 전투가 시작되었다.

4화
제목만 간단히 있는 경우도 있습니다.

전투는 치열했다.

제5화 - 새로운 동료
다시 한국어 형태로 돌아왔습니다.

새로운 동료가 나타났다.

Chapter 6: The Alliance
영어와 한국어가 섞여있는 복잡한 구조입니다.

동맹이 결성되었다.

7화: 비밀의 발견
민수는 중요한 비밀을 발견했다. 
"이건 100화쯤 되어야 밝혀질 줄 알았는데"라고 생각했지만, 이것은 내용입니다.

에필로그
모든 이야기가 끝났다."""
        
        try:
            sample_path = "complex_sample.txt"
            with open(sample_path, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            
            self.input_file.set(os.path.abspath(sample_path))
            self.log(f"📄 복잡한 구조의 샘플 파일이 생성되었습니다: {sample_path}")
            messagebox.showinfo("완료", "복잡한 구조의 샘플 파일이 생성되었습니다!\n\nAI 분할 방법으로 정확하게 처리할 수 있습니다.")
            
        except Exception as e:
            self.log(f"❌ 샘플 파일 생성 실패: {str(e)}")
            messagebox.showerror("오류", f"샘플 파일 생성에 실패했습니다: {str(e)}")
    
    def preview_split(self):
        """AI를 사용한 분할 미리보기"""
        if not self.input_file.get():
            messagebox.showwarning("경고", "원본 소설 파일을 선택해주세요.")
            return
        
        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("오류", "선택한 파일이 존재하지 않습니다.")
            return
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=self._preview_split_thread)
        thread.daemon = True
        thread.start()
    
    def _preview_split_thread(self):
        """미리보기를 별도 스레드에서 실행"""
        try:
            filename = self.input_file.get()
            
            with open(filename, 'r', encoding='utf-8') as file:
                text = file.read()
            
            method = self.methods[self.selected_method.get()]
            
            if method == "regex":
                episodes = self.split_with_regex(text)
            elif method == "gemini":
                episodes = self.split_with_gemini(text, preview_only=True)
            elif method == "gemini_flash":
                episodes = self.split_with_gemini_flash(text, preview_only=True)
            elif method == "gemini_flash_lite":
                episodes = self.split_with_gemini_flash_lite(text, preview_only=True)
            elif method == "hybrid":
                episodes = self.split_with_hybrid(text, preview_only=True)
            
            # 메인 스레드에서 미리보기 창 표시
            self.root.after(0, lambda: self.show_preview_window(episodes))
            
        except Exception as e:
            self.log(f"❌ 미리보기 오류: {str(e)}")
            error_msg = str(e)
            self.root.after(0, lambda: messagebox.showerror("오류", f"미리보기 중 오류가 발생했습니다:\n{error_msg}"))
    
    def show_preview_window(self, episodes):
        """미리보기 창 표시"""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("🤖 AI 분할 미리보기")
        preview_window.geometry("600x500")
        
        frame = ttk.Frame(preview_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"총 {len(episodes)}개의 에피소드가 발견되었습니다:", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # 트리뷰로 더 자세한 정보 표시
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree = ttk.Treeview(tree_frame, columns=('title', 'length'), show='tree headings')
        tree.heading('#0', text='순서')
        tree.heading('title', text='제목')
        tree.heading('length', text='길이')
        
        tree.column('#0', width=50)
        tree.column('title', width=300)
        tree.column('length', width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        for i, episode in enumerate(episodes):
            tree.insert('', tk.END, text=f"{i+1:03d}", 
                       values=(episode['title'], f"{len(episode.get('content', '')):,}자"))
        
        ttk.Button(frame, text="확인", command=preview_window.destroy).pack(pady=(10, 0))
    
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
            
            self.log(f"🚀 AI 분할 작업을 시작합니다...")
            self.log(f"📖 파일: {os.path.basename(filename)}")
            self.log(f"📁 출력 폴더: {output_dir}")
            self.log(f"🤖 분할 방법: {self.selected_method.get()}")
            
            # 파일 읽기
            with open(filename, 'r', encoding='utf-8') as file:
                text = file.read()
            
            self.log(f"✅ 파일을 성공적으로 읽었습니다. (크기: {len(text):,} 글자)")
            
            # 선택된 방법에 따라 분할
            method = self.methods[self.selected_method.get()]
            
            if method == "regex":
                episodes = self.split_with_regex(text)
            elif method == "gemini":
                episodes = self.split_with_gemini(text)
            elif method == "gemini_flash":
                episodes = self.split_with_gemini_flash(text)
            elif method == "gemini_flash_lite":
                episodes = self.split_with_gemini_flash_lite(text)
            elif method == "hybrid":
                episodes = self.split_with_hybrid(text)
            
            if not episodes:
                self.log("❌ 화를 찾을 수 없습니다.")
                self.root.after(0, lambda: messagebox.showerror("오류", "화를 찾을 수 없습니다."))
                return
            
            # 출력 폴더 생성
            os.makedirs(output_dir, exist_ok=True)
            
            # 파일 저장
            saved_count = 0
            for i, episode in enumerate(episodes):
                try:
                    filename_out = os.path.join(output_dir, f"{i+1:03d}화.txt")
                    
                    full_content = f"{episode['title']}\n\n{episode.get('content', '')}"
                    
                    with open(filename_out, 'w', encoding='utf-8') as ep_file:
                        ep_file.write(full_content)
                    
                    saved_count += 1
                    self.log(f"✅ 저장 완료: {os.path.basename(filename_out)} ({len(episode.get('content', '')):,} 글자)")
                    
                except Exception as ep_error:
                    self.log(f"❌ {i+1}번째 에피소드 저장 실패: {str(ep_error)}")
                    continue
            
            self.log(f"\n🎉 AI 분할 완료! 총 {saved_count}개의 에피소드가 저장되었습니다!")
            self.log(f"📁 저장 위치: {os.path.abspath(output_dir)}")
            
            # 성공 메시지
            self.root.after(0, lambda: messagebox.showinfo("완료", 
                f"AI 분할이 완료되었습니다!\n\n"
                f"저장된 에피소드: {saved_count}개\n"
                f"저장 위치: {os.path.abspath(output_dir)}\n"
                f"분할 방법: {self.selected_method.get()}"))
            
        except Exception as e:
            self.log(f"❌ 오류 발생: {str(e)}")
            import traceback
            self.log(f"🔍 상세 오류: {traceback.format_exc()}")
            error_msg = str(e)
            self.root.after(0, lambda: messagebox.showerror("오류", f"분할 중 오류가 발생했습니다:\n{error_msg}"))
        
        finally:
            # UI 재활성화
            self.root.after(0, self.finish_split)
    
    def split_with_regex(self, text):
        """정규표현식을 사용한 분할"""
        self.log("🔍 정규표현식으로 분할 중...")
        
        patterns = [
            r'^\s*(\d+화.*?)\s*$',                    # "1화", "2화" 형식
            r'^\s*(제\s*\d+화.*?)\s*$',               # "제1화", "제 1화" 형식
            r'^\s*(\d+\..*?)\s*$',                    # "1.", "2." 형식
            r'^\s*(Episode\s*\d+.*?)\s*$',            # "Episode 1" 형식
            r'^\s*(\d+장.*?)\s*$',                    # "1장", "2장" 형식
            r'^\s*(Chapter\s*\d+.*?)\s*$',            # "Chapter 1" 형식
            r'^\n\s*(.{10,50})\s*\n\s*\n',           # 공백으로 둘러싸인 제목 (10-50자)
        ]
        
        episodes = []
        used_pattern = None
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE))
            if matches:
                used_pattern = pattern
                self.log(f"✅ 패턴 '{pattern}' 사용, {len(matches)}개 발견")
                break
        
        if not used_pattern:
            return []
        
        for i, match in enumerate(matches):
            start_pos = match.start()
            title = match.group(1).strip()
            
            # 다음 매치의 시작점까지가 내용
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
                content = text[start_pos:end_pos].strip()
            else:
                content = text[start_pos:].strip()
            
            # 제목 부분 제거
            content_lines = content.split('\n', 1)
            if len(content_lines) > 1:
                content = content_lines[1].strip()
            else:
                content = ""
            
            episodes.append({
                'title': title,
                'content': content
            })
        
        # 화 길이 검증 및 로그
        valid_episodes = []
        for i, episode in enumerate(episodes):
            length = len(episode['content'])
            if 2000 <= length <= 20000:  # 허용 범위를 넓게 설정
                valid_episodes.append(episode)
                self.log(f"✅ {episode['title']}: {length:,}자")
            else:
                self.log(f"⚠️ {episode['title']}: {length:,}자 (길이 주의)")
                valid_episodes.append(episode)  # 일단 포함시키되 경고만
        
        return valid_episodes
    
    def split_with_gemini(self, text, preview_only=False):
        """Google Gemini를 사용한 분할"""
        if not GEMINI_AVAILABLE:
            raise Exception("google-generativeai 라이브러리가 설치되지 않았습니다. 'pip install google-generativeai' 실행하세요.")
        
        if not self.api_key.get():
            raise Exception("Gemini API 키를 입력해주세요.")
        
        self.log("🚀 Google Gemini 2.5 Pro로 분할 중...")
        
        # Gemini 설정
        genai.configure(api_key=self.api_key.get())
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # 텍스트가 너무 긴 경우 청크로 나누기
        max_chunk_size = 15000 if preview_only else 25000
        chunks = self.split_text_into_chunks(text, max_chunk_size)
        
        all_episodes = []
        
        for i, chunk in enumerate(chunks):
            self.log(f"🔄 청크 {i+1}/{len(chunks)} 처리 중...")
            
            prompt = f"""웹소설을 화별로 구분하세요.

텍스트:
{chunk}

화 구분 기준:
1. "1화", "2화" 형식
2. "1.", "2." 형식
3. 각 화의 고유 제목
4. 화 제목 앞뒤에 여러 줄의 공백(빈 줄)이 있음
5. 각 화는 대략 5000~10000자 길이

JSON 형식:{{
  "episodes": [
    {{
      "title": "화 제목",
      "content": "화 내용"
    }}
  ]
}}"""

            try:
                response = model.generate_content(prompt)
                result_text = response.text.strip()
                
                # JSON 파싱
                if result_text.startswith('```json'):
                    result_text = result_text[7:-3]
                elif result_text.startswith('```'):
                    result_text = result_text[3:-3]
                
                result = json.loads(result_text)
                episodes = result.get('episodes', [])
                
                all_episodes.extend(episodes)
                self.log(f"✅ 청크 {i+1}에서 {len(episodes)}개 화 발견")
                
            except Exception as e:
                self.log(f"❌ 청크 {i+1} 처리 실패: {str(e)}")
                continue
        
        self.log(f"🎉 Gemini 2.5 Pro 분할 완료: 총 {len(all_episodes)}개 화")
        return all_episodes
    
    def split_with_gemini_flash(self, text, preview_only=False):
        """Google Gemini 2.5 Flash를 사용한 분할 (빠름)"""
        if not GEMINI_AVAILABLE:
            raise Exception("google-generativeai 라이브러리가 설치되지 않았습니다. 'pip install google-generativeai' 실행하세요.")
        
        if not self.api_key.get():
            raise Exception("Gemini API 키를 입력해주세요.")
        
        self.log("⚡ Google Gemini 2.5 Flash로 분할 중...")
        
        # Gemini 설정
        genai.configure(api_key=self.api_key.get())
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 텍스트가 너무 긴 경우 청크로 나누기
        max_chunk_size = 12000 if preview_only else 20000
        chunks = self.split_text_into_chunks(text, max_chunk_size)
        
        all_episodes = []
        
        for i, chunk in enumerate(chunks):
            self.log(f"🔄 청크 {i+1}/{len(chunks)} 처리 중...")
            
            prompt = f"""웹소설을 화별로 구분하세요.

텍스트:
{chunk}

화 구분 기준:
1. "1화", "2화" 형식
2. "1.", "2." 형식
3. 각 화의 고유 제목
4. 화 제목 앞뒤에 여러 줄의 공백(빈 줄)이 있음
5. 각 화는 대략 5000~10000자 길이

JSON 형식:{{
  "episodes": [
    {{
      "title": "화 제목",
      "content": "화 내용"
    }}
  ]
}}"""

            try:
                response = model.generate_content(prompt)
                result_text = response.text.strip()
                
                # JSON 파싱
                if result_text.startswith('```json'):
                    result_text = result_text[7:-3]
                elif result_text.startswith('```'):
                    result_text = result_text[3:-3]
                
                result = json.loads(result_text)
                episodes = result.get('episodes', [])
                
                all_episodes.extend(episodes)
                self.log(f"✅ 청크 {i+1}에서 {len(episodes)}개 화 발견")
                
            except Exception as e:
                self.log(f"❌ 청크 {i+1} 처리 실패: {str(e)}")
                continue
        
        self.log(f"🎉 Gemini 2.5 Flash 분할 완료: 총 {len(all_episodes)}개 화")
        return all_episodes
    
    def split_with_gemini_flash_lite(self, text, preview_only=False):
        """Google Gemini 2.5 Flash-Lite를 사용한 분할 (매우 빠름)"""
        if not GEMINI_AVAILABLE:
            raise Exception("google-generativeai 라이브러리가 설치되지 않았습니다. 'pip install google-generativeai' 실행하세요.")
        
        if not self.api_key.get():
            raise Exception("Gemini API 키를 입력해주세요.")
        
        self.log("🚀 Google Gemini 2.5 Flash-Lite로 분할 중...")
        
        # Gemini 설정
        genai.configure(api_key=self.api_key.get())
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # 텍스트가 너무 긴 경우 청크로 나누기
        max_chunk_size = 10000 if preview_only else 15000
        chunks = self.split_text_into_chunks(text, max_chunk_size)
        
        all_episodes = []
        
        for i, chunk in enumerate(chunks):
            self.log(f"🔄 청크 {i+1}/{len(chunks)} 처리 중...")
            
            prompt = f"""웹소설 텍스트를 화별로 구분하세요:

{chunk}

팁: 화 제목은 앞뒤에 빈 줄이 많음

JSON 형식으로 응답:
{{
  "episodes": [
    {{"title": "화 제목", "content": "화 내용"}}
  ]
}}"""

            try:
                response = model.generate_content(prompt)
                result_text = response.text.strip()
                
                # JSON 파싱
                if result_text.startswith('```json'):
                    result_text = result_text[7:-3]
                elif result_text.startswith('```'):
                    result_text = result_text[3:-3]
                
                result = json.loads(result_text)
                episodes = result.get('episodes', [])
                
                all_episodes.extend(episodes)
                self.log(f"✅ 청크 {i+1}에서 {len(episodes)}개 화 발견")
                
            except Exception as e:
                self.log(f"❌ 청크 {i+1} 처리 실패: {str(e)}")
                continue
        
        self.log(f"🎉 Gemini 2.5 Flash-Lite 분할 완료: 총 {len(all_episodes)}개 화")
        return all_episodes
    
    def split_with_hybrid(self, text, preview_only=False):
        """하이브리드 방식: 정규식으로 1차 분할 후 AI로 검증"""
        self.log("🔄 하이브리드 방식으로 분할 중...")
        
        # 1단계: 정규식으로 1차 분할
        regex_episodes = self.split_with_regex(text)
        self.log(f"📊 정규식 1차 분할: {len(regex_episodes)}개 발견")
        
        if not regex_episodes:
            return []
        
        # 2단계: 긴 화부터 우선 검증 (길이순 정렬)
        # 화별로 길이 정보 추가
        for episode in regex_episodes:
            episode['length'] = len(episode['content'])
        
        # 길이가 긴 순서대로 정렬 (15000자 이상을 우선 검증)
        sorted_episodes = sorted(regex_episodes, key=lambda x: x['length'], reverse=True)
        
        verified_episodes = []
        
        for i, episode in enumerate(sorted_episodes):
            length = episode['length']
            priority = "🚨 긴 분량" if length > 15000 else "📏 일반 분량" if length > 8000 else "📝 짧은 분량"
            self.log(f"🔍 {priority} 화 검증 중: {episode['title']} ({length:,}자)")
            
            # 긴 화는 더 많은 텍스트로 검증
            preview_length = 2000 if length > 15000 else 1000
            episode_text = f"{episode['title']}\n\n{episode['content'][:preview_length]}..."
            
            try:
                if self.api_key.get() and GEMINI_AVAILABLE:
                    # Gemini로 검증
                    genai.configure(api_key=self.api_key.get())
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    char_count = len(episode['content'])
                    char_info = ""
                    if char_count > 15000:
                        char_info = " (주의: 매우 긴 분량, 여러 화가 합쳐졌을 가능성 높음)"
                    elif char_count > 10000:
                        char_info = " (긴 분량, 분할 검토 필요)"
                    elif char_count < 3000:
                        char_info = " (짧은 분량, 분할 오류 가능성)"
                    
                    prompt = f"""다음 텍스트가 웹소설의 한 화로 올바르게 분할되었는지 확인하세요:

텍스트 길이: {char_count}자{char_info}
일반적인 화 길이: 5000-10000자

{episode_text}

다음 기준으로 판단하세요:
1. 하나의 완성된 화인가?
2. 여러 화가 합쳐져 있지는 않은가?
3. 화가 중간에 끊어져 있지는 않은가?
4. 적절한 길이인가? (5000-10000자가 이상적)

올바른 화 분할인지 "yes" 또는 "no"로만 답하고, 더 나은 제목을 제안해주세요.

형식: yes/no|제안제목"""
                    
                    response = model.generate_content(prompt)
                    result = response.text.strip()
                    parts = result.split('|')
                    
                    if parts[0].lower() == 'yes':
                        if len(parts) > 1 and parts[1].strip():
                            episode['title'] = parts[1].strip()
                        verified_episodes.append(episode)
                        self.log(f"✅ 화 {i+1} 검증 통과")
                    else:
                        self.log(f"⚠️ 화 {i+1} 검증 실패")
                else:
                    # API 키가 없으면 정규식 결과 그대로 사용
                    verified_episodes.append(episode)
                    
            except Exception as e:
                self.log(f"❌ 화 {i+1} 검증 오류: {str(e)}")
                # 오류 시 원본 사용
                verified_episodes.append(episode)
        
        self.log(f"🎉 하이브리드 분할 완료: {len(verified_episodes)}개 화")
        return verified_episodes
    
    def split_text_into_chunks(self, text, max_size):
        """텍스트를 청크로 나누기"""
        chunks = []
        current_chunk = ""
        
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > max_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = paragraph
                else:
                    # 단일 문단이 너무 긴 경우
                    chunks.append(paragraph[:max_size])
                    current_chunk = paragraph[max_size:]
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def finish_split(self):
        """분할 작업 완료 후 UI 상태 복원"""
        self.progress.stop()
        self.run_button.config(state="normal")

def main():
    """메인 함수"""
    root = tk.Tk()
    
    # 스타일 설정
    style = ttk.Style()
    style.theme_use('clam')
    
    app = NovelSplitterAI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.quit()

if __name__ == "__main__":
    main()
