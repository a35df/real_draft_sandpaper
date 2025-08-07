import re
import os
import glob
from datetime import datetime

def filter_novel_urls(input_file, output_file):
    """
    소설 URL 파일에서 유효한 소설 페이지 링크만 필터링
    """
    # 소설 각 화 링크 패턴: https://booktoki*.com/novel/숫자?쿼리파라미터
    # 쿼리 파라미터가 있는 경우만 (실제 각 화 링크)
    novel_pattern = re.compile(r'^https?://booktoki\d*\.com/novel/\d+\?.*')
    
    # 제거할 패턴: javascript 링크, linkbn.php 등
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
    
    except FileNotFoundError:
        print(f"오류: 파일을 찾을 수 없습니다 - {input_file}")
        return 0, 0
    except Exception as e:
        print(f"오류 발생: {e}")
        return 0, 0

def process_all_url_files():
    """
    현재 디렉토리의 모든 *url.txt 파일을 처리
    """
    # *url.txt 패턴으로 파일 찾기
    url_files = glob.glob("*url.txt")
    
    if not url_files:
        print("*url.txt 패턴에 맞는 파일이 없습니다.")
        print("파일명이 다음 형식인지 확인해주세요: '소설제목 url.txt'")
        return
    
    print(f"발견된 URL 파일: {len(url_files)}개")
    print("=" * 60)
    
    total_processed = 0
    total_filtered_links = 0
    failed_files = []
    
    for i, input_file in enumerate(url_files, 1):
        print(f"[{i}/{len(url_files)}] 처리 중: {input_file}")
        
        # 출력 파일명 생성: "소설제목 url.txt" -> "소설제목 filtered_urls.txt"
        if input_file.endswith(" url.txt"):
            novel_title = input_file[:-8]  # " url.txt" 제거
            output_file = f"{novel_title} filtered_urls.txt"
        else:
            # "소설제목url.txt" 형태인 경우
            novel_title = input_file[:-7]  # "url.txt" 제거
            output_file = f"{novel_title} filtered_urls.txt"
        
        filtered_count, total_count = filter_novel_urls(input_file, output_file)
        
        if total_count > 0:
            print(f"  📊 전체 링크: {total_count}개")
            print(f"  ✅ 필터링된 링크: {filtered_count}개")
            print(f"  💾 저장 위치: {output_file}")
            total_processed += 1
            total_filtered_links += filtered_count
            
            if filtered_count == 0:
                print("  ⚠️  경고: 유효한 소설 링크가 없습니다.")
        else:
            print(f"  ❌ 파일 처리 실패")
            failed_files.append(input_file)
        
        print("-" * 50)
    
    # 최종 결과 요약
    print(f"\n📋 처리 완료 요약:")
    print(f"  ✅ 성공: {total_processed}개 파일")
    print(f"  📊 총 추출된 링크: {total_filtered_links}개")
    
    if failed_files:
        print(f"  ❌ 실패: {len(failed_files)}개 파일")
        print("  실패한 파일들:")
        for failed_file in failed_files:
            print(f"    - {failed_file}")
    
    print(f"\n처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return total_processed, total_filtered_links

def check_files_before_processing():
    """
    처리 전에 파일들을 미리 확인
    """
    url_files = glob.glob("*url.txt")
    
    if not url_files:
        print("❌ *url.txt 패턴에 맞는 파일이 없습니다.")
        print("파일명 예시: '소설제목 url.txt'")
        return False
    
    print(f"🔍 발견된 파일들 ({len(url_files)}개):")
    for i, file in enumerate(url_files, 1):
        file_size = os.path.getsize(file)
        print(f"  {i:2d}. {file} ({file_size:,} bytes)")
    
    return True

def create_summary_report(total_processed, total_filtered_links):
    """
    처리 결과 요약 리포트 생성
    """
    report_filename = f"filtering_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("웹소설 URL 필터링 결과 리포트\n")
        f.write("=" * 50 + "\n")
        f.write(f"처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"처리된 파일 수: {total_processed}개\n")
        f.write(f"총 추출된 링크 수: {total_filtered_links}개\n\n")
        
        f.write("처리된 파일 목록:\n")
        for file in glob.glob("*filtered_urls.txt"):
            with open(file, 'r', encoding='utf-8') as filtered_file:
                link_count = len([line for line in filtered_file if line.strip()])
            f.write(f"  - {file}: {link_count}개 링크\n")
    
    print(f"📊 상세 리포트가 생성되었습니다: {report_filename}")

def main():
    print("🚀 웹소설 URL 일괄 필터링 프로그램")
    print("=" * 60)
    
    # 1. 파일 사전 확인
    if not check_files_before_processing():
        return
    
    print("\n▶️  처리를 시작합니다...\n")
    
    # 2. 모든 URL 파일 처리
    total_processed, total_filtered_links = process_all_url_files()
    
    # 3. 요약 리포트 생성
    if total_processed > 0:
        create_summary_report(total_processed, total_filtered_links)
    
    print("\n🎉 모든 작업이 완료되었습니다!")

if __name__ == "__main__":
    main()
