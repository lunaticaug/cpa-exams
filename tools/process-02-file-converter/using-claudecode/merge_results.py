"""
기능: Vision API로 추출한 페이지별 JSON을 하나의 Markdown으로 통합
입력: workspace/vision_output/ 폴더의 JSON 파일들
출력: 통합된 Markdown 파일
버전: v2.00
"""

import json
from pathlib import Path
import sys


def merge_extracted_pages(input_dir="workspace/vision_output", output_file=None):
    """
    페이지별 JSON 파일을 하나의 Markdown으로 통합
    """
    input_dir = Path(input_dir)
    
    if not input_dir.exists():
        print(f"❌ 입력 디렉토리를 찾을 수 없습니다: {input_dir}")
        return
    
    # JSON 파일 찾기
    json_files = sorted(input_dir.glob("page_*_extracted.json"))
    
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
        existing_files = list(Path(".").glob("원가회계_2024_v*.md"))
        if existing_files:
            # 가장 높은 버전 번호 찾기
            versions = []
            for f in existing_files:
                try:
                    version_str = f.stem.split('_v')[1].split('_')[0]
                    versions.append(float(version_str))
                except:
                    continue
            
            if versions:
                next_version = max(versions) + 0.01
            else:
                next_version = 2.00
        else:
            next_version = 2.00
        
        output_file = f"원가회계_2024_v{next_version:.2f}_vision추출.md"
    
    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"\n✅ 통합 완료!")
    print(f"📄 출력 파일: {output_file}")
    print(f"📊 통계:")
    print(f"  - 총 페이지: {len(json_files)}")
    print(f"  - 총 문제: {len(all_problems)}")
    
    # 문제별 요약
    if all_problems:
        print("\n📋 문제 요약:")
        for prob in all_problems:
            print(f"  - 문제 {prob['number']}: {prob['points']}점")
    
    # 구조 정보도 JSON으로 저장
    structure_file = output_file.replace('.md', '_구조.json')
    with open(structure_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_pages': len(json_files),
            'problems': all_problems,
            'output_file': output_file
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