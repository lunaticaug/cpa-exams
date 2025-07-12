"""
기능: Vision API로 추출한 페이지별 JSON을 하나의 Markdown으로 통합 (개선판)
입력: workspace/vision_output/ 폴더의 JSON 파일들
출력: 통합된 Markdown 파일
버전: v2.01
변경사항: 
  - 한글 파일명 지원 (page_XXX_추출_N.json)
  - 같은 페이지의 여러 버전 중 최신 버전 사용
"""

import json
from pathlib import Path
import sys
import re


def get_latest_page_files(input_dir):
    """각 페이지별로 최신 버전의 파일만 선택"""
    input_dir = Path(input_dir)
    
    # 모든 JSON 파일 찾기
    all_files = list(input_dir.glob("page_*.json"))
    
    # 페이지별로 그룹화
    page_files = {}
    for file in all_files:
        # 페이지 번호 추출
        match = re.match(r'page_(\d+)', file.stem)
        if match:
            page_num = int(match.group(1))
            if page_num not in page_files:
                page_files[page_num] = []
            page_files[page_num].append(file)
    
    # 각 페이지별로 최신 파일 선택
    latest_files = []
    for page_num in sorted(page_files.keys()):
        files = page_files[page_num]
        if len(files) == 1:
            latest_files.append(files[0])
        else:
            # 여러 버전이 있으면 파일명으로 정렬 후 마지막 것 선택
            # extracted < 추출_1 < 추출_2 < 추출_3 순서
            files_sorted = sorted(files, key=lambda f: (
                '추출' in f.stem,  # 추출이 있으면 나중
                int(re.search(r'추출_(\d+)', f.stem).group(1)) if re.search(r'추출_(\d+)', f.stem) else 0
            ))
            latest_files.append(files_sorted[-1])
            print(f"  페이지 {page_num}: {files_sorted[-1].name} 선택 (총 {len(files)}개 버전 중)")
    
    return latest_files


def merge_extracted_pages(input_dir="workspace/vision_output", output_file=None):
    """
    페이지별 JSON 파일을 하나의 Markdown으로 통합
    """
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        print(f"❌ 입력 디렉토리를 찾을 수 없습니다: {input_dir}")
        return
    
    # 최신 버전의 JSON 파일들만 선택
    json_files = get_latest_page_files(input_dir)
    
    if not json_files:
        print(f"❌ {input_dir}에서 추출된 JSON 파일을 찾을 수 없습니다")
        return
    
    print(f"📄 {len(json_files)}개 페이지 발견")
    
    # 전체 내용을 저장할 리스트
    all_content = []
    all_problems = []
    
    # 각 JSON 파일 읽기
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 페이지 내용 추가
        page_num = data.get('page_number', 0)
        content = data.get('content', '')
        
        # 페이지 구분자 추가 (첫 페이지 제외)
        if page_num > 1:
            all_content.append(f"\n\n---\n[페이지 {page_num}]\n")
        
        all_content.append(content)
        
        # 문제 정보 수집
        if 'problems' in data:
            all_problems.extend(data['problems'])
    
    # 전체 내용 결합
    full_content = "\n".join(all_content)
    
    # 출력 파일명 결정
    if output_file is None:
        # 자동으로 버전 번호 결정
        existing_files = list(Path(".").glob("원가회계_2024_v*_vision추출_*.md"))
        if existing_files:
            # 가장 높은 번호 찾기
            numbers = []
            for f in existing_files:
                match = re.search(r'vision추출_(\d+)', f.stem)
                if match:
                    numbers.append(int(match.group(1)))
            
            if numbers:
                next_num = max(numbers) + 1
            else:
                next_num = 1
        else:
            next_num = 1
        
        output_file = f"원가회계_2024_v2.00_vision추출_{next_num}.md"
    
    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"\n✅ 통합 완료!")
    print(f"📄 출력 파일: {output_file}")
    print(f"📊 통계:")
    print(f"  - 총 페이지: {len(json_files)}")
    print(f"  - 총 문제: {len(set(p['number'] for p in all_problems))}")
    
    # 문제별 요약
    if all_problems:
        print("\n📋 문제 요약:")
        seen_problems = set()
        for prob in all_problems:
            if prob['number'] not in seen_problems:
                print(f"  - 문제 {prob['number']}: {prob['points']}점")
                seen_problems.add(prob['number'])
    
    # 구조 정보도 JSON으로 저장
    structure_file = output_file.replace('.md', '_구조.json')
    with open(structure_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_pages': len(json_files),
            'problems': all_problems,
            'output_file': output_file,
            'source_files': [str(f) for f in json_files]
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📋 구조 파일: {structure_file}")


def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        merge_extracted_pages(output_file=output_file)
    else:
        merge_extracted_pages()


if __name__ == "__main__":
    main()