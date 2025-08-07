import re
import os

def split_and_save(filename):
    """
    웹소설 원본 파일을 화별로 분할하여 저장하는 함수
    
    Args:
        filename (str): 원본 소설 파일명
    """
    try:
        # 원본 텍스트 읽기
        with open(filename, 'r', encoding='utf-8') as file:
            text = file.read()
        
        print(f"📖 '{filename}' 파일을 읽었습니다.")
        
        # 에피소드 단위로 나누기 (다양한 패턴 지원) - 더 정확한 매칭
        # 패턴: 줄 시작에 있는 "1화", "제1화", "Episode 1", "1장" 등
        patterns = [
            r'^(\d+화)',           # 줄 시작에 있는 "1화", "2화"...
            r'^(제\s*\d+화)',      # 줄 시작에 있는 "제1화", "제 1화"...
            r'^(Episode\s*\d+)',   # 줄 시작에 있는 "Episode 1", "Episode 2"...
            r'^(\d+장)',           # 줄 시작에 있는 "1장", "2장"...
            r'^(Chapter\s*\d+)',   # 줄 시작에 있는 "Chapter 1", "Chapter 2"...
            r'(?:^|\n\n)(\d+화)(?:\s|$)',  # 앞뒤로 공백이나 줄바꿈이 있는 경우
        ]
        
        episodes = []
        used_pattern = None
        for pattern in patterns:
            episodes = re.split(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if len(episodes) > 1:
                used_pattern = pattern
                print(f"✅ 패턴 '{pattern}' 사용하여 분할합니다.")
                break
        
        if len(episodes) <= 1:
            print("❌ 에피소드 구분자를 찾을 수 없습니다. 파일 내용을 확인해주세요.")
            return
        
        # 빈 문자열 제거 및 공백 정리
        episodes = [ep.strip() for ep in episodes if ep.strip()]
        
        # 결과 저장 폴더 생성
        output_dir = "episodes"
        os.makedirs(output_dir, exist_ok=True)
        
        saved_count = 0
        
        # 파일로 저장 (텍스트 순서 그대로 유지)
        episodes_found = []
        
        # 패턴 위치를 순서대로 찾기
        for match in re.finditer(used_pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            start_pos = match.start()
            title = match.group(1)
            
            # 숫자 추출
            number_match = re.search(r'(\d+)', title)
            if number_match:
                ep_num = int(number_match.group(1))
                episodes_found.append({
                    'number': ep_num,
                    'title': title,
                    'start_pos': start_pos
                })
        
        print(f"📊 총 {len(episodes_found)}개의 에피소드를 텍스트 순서대로 처리합니다.")
        
        # 텍스트 순서대로 저장 (정렬하지 않음)
        for i, episode in enumerate(episodes_found):
            try:
                # 현재 에피소드의 시작 위치
                current_start = episode['start_pos']
                
                # 다음 에피소드의 시작 위치 (마지막이면 텍스트 끝까지)
                if i + 1 < len(episodes_found):
                    next_start = episodes_found[i + 1]['start_pos']
                    content = text[current_start:next_start].strip()
                else:
                    content = text[current_start:].strip()
                
                # 제목과 내용 분리
                lines = content.split('\n', 1)
                if len(lines) > 1:
                    episode_content = lines[1].strip()
                else:
                    episode_content = ""
                
                # 파일명 생성 (텍스트 순서대로)
                sequence_num = i + 1
                filename = os.path.join(output_dir, f"{sequence_num:03d}화.txt")
                
                # 파일 내용 구성 (제목 + 내용)
                full_content = f"{episode['title']}\n\n{episode_content}"
                
                with open(filename, 'w', encoding='utf-8') as ep_file:
                    ep_file.write(full_content)
                
                saved_count += 1
                print(f"✅ 저장 완료: {os.path.basename(filename)} (원본: {episode['title']})")
                
            except Exception as ep_error:
                print(f"❌ {i+1}번째 에피소드 저장 실패: {str(ep_error)}")
                continue
        
        print(f"\n🎉 총 {saved_count}개의 에피소드가 저장되었습니다!")
        print(f"📁 저장 위치: {os.path.abspath(output_dir)}")
        
    except FileNotFoundError:
        print(f"❌ '{filename}' 파일을 찾을 수 없습니다.")
        print("💡 파일이 같은 폴더에 있는지 확인해주세요.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")

def create_sample_file():
    """
    테스트용 샘플 파일을 생성하는 함수
    """
    sample_content = """프롤로그
이것은 샘플 웹소설입니다.

1화 새로운 시작
주인공은 평범한 학생이었다. 어느 날 신비로운 능력을 얻게 되는데...
이것은 첫 번째 화의 내용입니다.

2화 능력의 각성
능력이 각성되면서 주인공의 삶이 변하기 시작했다.
새로운 세계가 그의 앞에 펼쳐졌다.

3화 새로운 만남
학교에서 비슷한 능력을 가진 소녀를 만나게 되었다.
그녀는 주인공에게 중요한 정보를 알려주었다.

4화 첫 번째 시련
갑작스럽게 나타난 적들과의 첫 번째 전투가 시작되었다.
주인공은 자신의 능력을 시험받게 되었다.

에pilogue
이것으로 샘플 이야기가 끝납니다."""
    
    with open("original.txt", 'w', encoding='utf-8') as f:
        f.write(sample_content)
    
    print("📄 샘플 파일 'original.txt'가 생성되었습니다.")

def main():
    """
    메인 함수
    """
    print("=" * 50)
    print("🔥 웹소설 분할 프로그램 🔥")
    print("=" * 50)
    
    # 원본 파일이 있는지 확인
    original_filename = "original.txt"
    
    if not os.path.exists(original_filename):
        print(f"❌ '{original_filename}' 파일이 없습니다.")
        create_sample = input("📝 테스트용 샘플 파일을 생성하시겠습니까? (y/n): ")
        
        if create_sample.lower() in ['y', 'yes', '예', 'ㅇ']:
            create_sample_file()
            print("\n🚀 샘플 파일로 분할을 시작합니다...\n")
        else:
            print("💡 'original.txt' 파일을 만들어서 웹소설 내용을 넣어주세요.")
            return
    
    # 분할 실행
    split_and_save(original_filename)

if __name__ == "__main__":
    main()
