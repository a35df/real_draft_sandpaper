# 🔥 웹소설 분할 프로그램

VS Code 환경에**AI 분할 방법:**
- 🚀 **Google Gemini 2.0 Flash Pro**: 구글의 최고 성능 AI 모델 (API 키 필요)
- 🧠 **OpenAI GPT**: ChatGPT 모델 사용 (API 키 필요)
- 🏠 **로컬 LLM**: Ollama 등 로컬 모델 사용
- 🔧 **하이브리드**: 정규식 + AI 검증 (가장 권장)
- ⚡ **정규표현식**: 기존 방식 (빠름)텍스트를 화별로 자동 분할하는 Python 스크립트입니다.  
**AI 버전**, **GUI 버전**, **CLI 버전** 모두 제공됩니다!

## 📁 프로젝트 구조

```
webnovel-spliter/
├── splitter.py         # CLI 버전 (터미널)
├── splitter_gui.py     # GUI 버전 (그래픽 인터페이스)
├── splitter_ai.py      # 🤖 AI 버전 (LLM 기반 지능 분할)
├── .env.example        # 환경변수 설정 예시 파일
├── .env                # API 키 설정 파일 (직접 생성)
├── original.txt        # 원본 소설 파일
├── sample_novel.txt    # 샘플 파일 (GUI에서 생성)
├── complex_sample.txt  # 복잡한 구조 샘플 (AI에서 생성)
├── episodes/           # 분할된 화별 파일들
│   ├── 001화.txt
│   ├── 002화.txt
│   └── ...
└── README.md          # 사용법 안내
```

## 🚀 사용 방법

### 📋 사전 준비
1. `.env.example` 파일을 `.env`로 복사
2. `.env` 파일에 Gemini API 키 추가:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### 🤖 AI 버전 (가장 정확함) ⭐
```bash
python splitter_ai.py
```

**AI 분할 방법:**
- 🧠 **OpenAI GPT**: ChatGPT 모델 사용 (API 키 필요)
- 🏠 **로컬 LLM**: Ollama 등 로컬 모델 사용
- � **하이브리드**: 정규식 + AI 검증 (가장 권장)
- ⚡ **정규표현식**: 기존 방식 (빠름)

**AI 버전 장점:**
- **Google Gemini 2.0 Flash Pro**: 최고 성능의 사고 능력을 가진 AI 모델
- **환경변수 지원**: .env 파일로 API 키 안전하게 관리
- 복잡한 제목 구조 정확 인식
- 본문 중 "n화" 단어 무시
- 다양한 형식 자동 처리: "1화", "제1화", "Episode 1", "Chapter 1"
- 컨텍스트 기반 지능 분할

### 💻 CLI 버전 (터미널)
```bash
python splitter.py
```

### 🎯 VS Code 작업 실행
- `Cmd + Shift + P` → "Tasks: Run Task" 선택
- "웹소설 분할 GUI 실행" 또는 "웹소설 분할 실행" 선택

## 📋 지원하는 구분자 패턴

이 프로그램은 다양한 화 구분 패턴을 자동으로 인식합니다:

- `1화`, `2화`, `3화` ...
- `제1화`, `제2화`, `제3화` ...
- `Episode 1`, `Episode 2` ...
- `1장`, `2장`, `3장` ...
- `Chapter 1`, `Chapter 2` ...

## ⚙️ 프로그램 특징

✅ **자동 패턴 인식**: 다양한 화 구분 형식을 자동으로 감지  
✅ **에러 처리**: 파일 없음, 구분자 없음 등의 상황을 안전하게 처리  
✅ **샘플 생성**: 테스트용 샘플 파일 자동 생성 기능  
✅ **한글 지원**: UTF-8 인코딩으로 한글 텍스트 완벽 지원  
✅ **파일명 정렬**: 001화.txt, 002화.txt 형식으로 순서대로 정렬  

## 🔧 문제 해결

### Q: "original.txt 파일을 찾을 수 없습니다" 오류가 나요
A: 프로그램 파일과 같은 폴더에 `original.txt` 파일이 있는지 확인하세요.

### Q: 화가 제대로 분할되지 않아요
A: 원본 텍스트에서 화 구분자가 정확한지 확인하세요. (예: "1화", "2화")

### Q: 특별한 패턴을 사용하고 싶어요
A: `splitter.py` 파일의 `patterns` 리스트에 정규표현식을 추가하세요.

## 📝 사용 예시

**원본 파일 (original.txt):**
```
프롤로그
이야기의 시작...

1화 새로운 시작
주인공이 등장하고...

2화 모험의 시작
새로운 여행이 시작되고...
```

**실행 결과:**
- `episodes/001화.txt`: "1화 새로운 시작" + 해당 내용
- `episodes/002화.txt`: "2화 모험의 시작" + 해당 내용

## 🔧 API 설정

### 환경변수 설정 (권장)
1. `.env.example` 파일을 `.env`로 복사
2. `.env` 파일에 API 키 입력:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```
3. 프로그램 실행시 자동으로 키 로드

### Google Gemini API
1. [Google AI Studio](https://makersuite.google.com/app/apikey)에서 API 키 생성
2. `.env` 파일에 `GEMINI_API_KEY` 설정
3. AI 버전 실행 후 "Google Gemini" 선택

### OpenAI API  
1. [OpenAI Platform](https://platform.openai.com/api-keys)에서 API 키 생성
2. `.env` 파일에 `OPENAI_API_KEY` 설정
3. AI 버전 실행 후 "OpenAI GPT" 선택

## 🎯 추가 기능

필요에 따라 다음 기능들을 추가로 구현할 수 있습니다:

- PDF 파일 지원
- 웹 크롤링을 통한 자동 다운로드
- GUI 인터페이스
- 다양한 출력 형식 (EPUB, PDF 등)

---

**개발자**: GitHub Copilot  
**라이센스**: MIT  
**버전**: 1.0.0
