from flask import Flask, render_template, request, redirect, url_for, session
import json
import google.generativeai as genai
import os
import re
from flask_session import Session

# --- API 키 설정 ---
# 실제 키로 교체해주세요.
genai.configure(api_key="AIzaSyAfGPl2HJfwtLkEzdqVLeSftLKXCj9rXfA")

# --- Gemini 모델 초기화: 최신 모델로 변경 ---
try:
    # 가장 최신이고 강력한 모델로 변경합니다.
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
except Exception as e:
    print(f"모델 초기화 실패: {e}")
    model = None

# 1단계: 전체 텍스트에서 등장인물 목록만 추출하는 함수
def extract_characters(text):
    if not model: return []
    prompt = f"""다음 텍스트에서 모든 등장인물의 이름을 추출해서 JSON 리스트 형식으로 반환해줘.
다른 설명은 절대 추가하지 말고, 오직 JSON 리스트만 반환해야 해.
예시: ["김철수", "이영희", "박민준"]

---
텍스트:
{text}
---
"""
    try:
        print(f"Gemini API 호출 중 (이름 추출)...")
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        characters = json.loads(json_text)
        # 중복 제거 및 긴 이름 순으로 정렬
        return sorted(list(set(characters)), key=len, reverse=True)
    except Exception as e:
        print(f"이름 추출 중 오류 발생: {e}")
        return []

# 2단계: 전체 등장인물 목록으로 새 이름을 제안받는 함수 (출신에 맞는 이름으로 자동 변경)
def get_new_name_suggestions(characters):
    if not model or not characters: return {}
    prompt = f"""다음은 소설에 등장하는 인물들의 이름 목록이야. 각 인물의 이름을 분석해서 그 출신에 맞는 새로운 이름을 제안해줘.

규칙:
1. 한국 이름(김철수, 이영희, 박민준 등)이면 → 새로운 한국 이름으로 변경
2. 영미권 이름(John, Mary, David, Emma 등)이면 → 새로운 영미권 이름으로 변경  
3. 일본 이름(히로시, 사쿠라, 타나카 등)이면 → 새로운 일본 이름으로 변경
4. 중국 이름(왕밍, 리웨이 등)이면 → 새로운 중국 이름으로 변경
5. 기타 지역 이름들도 각각의 문화권에 맞게 변경

성별도 고려해서 적절한 이름을 제안해줘.
결과는 반드시 아래와 같은 JSON 형식으로만 응답해야 해. 다른 설명은 절대 추가하지 마.

{{
  "기존 이름1": "새 이름1",
  "기존 이름2": "새 이름2"
}}

---
등장인물 목록:
{json.dumps(characters, ensure_ascii=False)}
---
"""
    try:
        print(f"Gemini API 호출 중 (문화권별 새 이름 제안)...")
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        name_map = json.loads(json_text)
        return name_map
    except Exception as e:
        print(f"새 이름 제안 중 오류 발생: {e}")
        return {"오류": "새 이름 제안에 실패했습니다."}

app = Flask(__name__)
# 세션 및 요청 크기 제한 설정
app.config["SECRET_KEY"] = "a-very-secret-key-for-session"
app.config["SESSION_TYPE"] = "filesystem"
# 요청 크기 제한은 만약을 위해 넉넉하게 유지합니다.
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
Session(app)

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    """텍스트 조각을 받아 처리하거나, 마지막 조각 처리 후 자동으로 이름을 변경합니다."""
    is_chunk = request.form.get('is_chunk') == 'true'
    
    if is_chunk:
        # 청크 처리 모드
        chunk_text = request.form['novel_text']
        chunk_index = int(request.form.get('chunk_index', 0))
        total_chunks = int(request.form.get('total_chunks', 1))
        
        # 세션에 원본 텍스트 조립
        if 'original_text' not in session:
            session['original_text'] = ""
            session['all_characters'] = []
        
        session['original_text'] += chunk_text
        
        # 이 청크에서 등장인물 추출
        characters = extract_characters(chunk_text)
        session['all_characters'].extend(characters)
        
        # 마지막 청크인 경우 자동으로 이름 변경 적용
        if chunk_index == total_chunks - 1:
            # 중복 제거 및 정렬
            unique_characters = sorted(list(set(session['all_characters'])), key=len, reverse=True)
            
            if not unique_characters:
                return render_template('result.html', final_text="오류: 텍스트에서 등장인물을 찾을 수 없습니다.")
            else:
                # 2단계: 새 이름 제안 받기
                suggested_map = get_new_name_suggestions(unique_characters)
                print(f"제안된 이름 매핑: {suggested_map}")
                
                # 3단계: 자동으로 이름 변경 적용
                modified_text = session['original_text']
                sorted_names = sorted(suggested_map.keys(), key=len, reverse=True)
                print(f"정렬된 이름들: {sorted_names}")
                
                for old_name in sorted_names:
                    new_name = suggested_map[old_name]
                    if new_name and new_name != "오류":
                        print(f"'{old_name}' -> '{new_name}' 변경 시도")
                        before_count = modified_text.count(old_name)
                        
                        # 단순한 전체 단어 매칭 방식 사용
                        # 한글과 영문 모두에 대응
                        import re
                        
                        # 정확한 단어 경계를 위한 패턴들
                        patterns_to_try = [
                            # 1. 정확히 단어로만 존재하는 경우 (앞뒤 공백 또는 구두점)
                            r'(?<![가-힣a-zA-Z])' + re.escape(old_name) + r'(?![가-힣a-zA-Z])',
                            # 2. 더 단순한 방식: 공백 또는 특수문자로 둘러싸인 경우  
                            r'(\s|^)' + re.escape(old_name) + r'(\s|[.,!?은는이가을를에게서와과의도로부터까지만]|$)',
                        ]
                        
                        # 각 패턴을 시도해보고 가장 잘 작동하는 것 사용
                        replaced = False
                        for pattern in patterns_to_try:
                            try:
                                new_text = re.sub(pattern, lambda m: m.group(1) + new_name + m.group(2) if len(m.groups()) >= 2 else new_name, modified_text)
                                if new_text != modified_text:
                                    modified_text = new_text
                                    replaced = True
                                    break
                            except:
                                continue
                        
                        # 패턴이 작동하지 않으면 단순 교체
                        if not replaced:
                            modified_text = modified_text.replace(old_name, new_name)
                        
                        after_count = modified_text.count(old_name)
                        replaced_count = modified_text.count(new_name)
                        print(f"변경 전: {before_count}개, 변경 후: {after_count}개, 새 이름: {replaced_count}개")
                
                return render_template('result.html', final_text=modified_text)
        
        return "", 200  # 청크 처리 완료 응답
    
    else:
        # 일반 처리 모드 (작은 텍스트의 경우)
        original_text = request.form['novel_text']
        if not original_text:
            return redirect(url_for('index'))

        # 1단계: 등장인물 추출
        characters = extract_characters(original_text)
        
        if not characters:
            return render_template('result.html', final_text="오류: 텍스트에서 등장인물을 찾을 수 없습니다.")

        # 2단계: 새 이름 제안 받기
        suggested_map = get_new_name_suggestions(characters)
        print(f"제안된 이름 매핑: {suggested_map}")
        
        # 3단계: 자동으로 이름 변경 적용
        modified_text = original_text
        sorted_names = sorted(suggested_map.keys(), key=len, reverse=True)
        print(f"정렬된 이름들: {sorted_names}")
        
        for old_name in sorted_names:
            new_name = suggested_map[old_name]
            if new_name and new_name != "오류":
                print(f"'{old_name}' -> '{new_name}' 변경 시도")
                before_count = modified_text.count(old_name)
                
                # 단순한 전체 단어 매칭 방식 사용
                # 한글과 영문 모두에 대응
                import re
                
                # 정확한 단어 경계를 위한 패턴들
                patterns_to_try = [
                    # 1. 정확히 단어로만 존재하는 경우 (앞뒤 공백 또는 구두점)
                    r'(?<![가-힣a-zA-Z])' + re.escape(old_name) + r'(?![가-힣a-zA-Z])',
                    # 2. 더 단순한 방식: 공백 또는 특수문자로 둘러싸인 경우  
                    r'(\s|^)' + re.escape(old_name) + r'(\s|[.,!?은는이가을를에게서와과의도로부터까지만]|$)',
                ]
                
                # 각 패턴을 시도해보고 가장 잘 작동하는 것 사용
                replaced = False
                for pattern in patterns_to_try:
                    try:
                        new_text = re.sub(pattern, lambda m: m.group(1) + new_name + m.group(2) if len(m.groups()) >= 2 else new_name, modified_text)
                        if new_text != modified_text:
                            modified_text = new_text
                            replaced = True
                            break
                    except:
                        continue
                
                # 패턴이 작동하지 않으면 단순 교체
                if not replaced:
                    modified_text = modified_text.replace(old_name, new_name)
                
                after_count = modified_text.count(old_name)
                replaced_count = modified_text.count(new_name)
                print(f"변경 전: {before_count}개, 변경 후: {after_count}개, 새 이름: {replaced_count}개")
        
        return render_template('result.html', final_text=modified_text)

if __name__ == '__main__':
    app.run(debug=True, port=5001)