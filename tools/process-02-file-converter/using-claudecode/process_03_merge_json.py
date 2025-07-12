#!/usr/bin/env python3
"""
기능: 모든 JSON 구조를 처리할 수 있는 범용 merge 스크립트
입력: 연도별 vision_output 폴더의 JSON 파일들
출력: 통합된 Markdown 파일
버전: v1.00
특징: 
  - 문자열 content 지원
  - 딕셔너리 content 지원 (자동 변환)
  - 다양한 JSON 구조 자동 감지 및 처리
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Union

def extract_text_from_dict(data: Dict[str, Any], indent: int = 0) -> str:
    """딕셔너리를 읽기 쉬운 텍스트로 변환"""
    lines = []
    indent_str = "  " * indent
    
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{indent_str}{key}:")
            lines.append(extract_text_from_dict(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{indent_str}{key}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(extract_text_from_dict(item, indent + 1))
                else:
                    lines.append(f"{indent_str}  - {item}")
        else:
            lines.append(f"{indent_str}{key}: {value}")
    
    return "\n".join(lines)

def extract_content_from_json(data: Dict[str, Any]) -> str:
    """JSON 데이터에서 내용을 추출 (모든 형식 지원)"""
    content_parts = []
    
    # 페이지 번호 추가
    page_num = data.get('page_number', 0)
    if page_num > 0:
        content_parts.append(f"[페이지 {page_num}]")
    
    # content 필드 처리
    if 'content' in data:
        content = data['content']
        
        # 형식 A: content가 문자열
        if isinstance(content, str):
            content_parts.append(content)
        
        # 형식 B: content가 딕셔너리 (2023년 형식)
        elif isinstance(content, dict):
            # 제목 페이지 특별 처리
            if data.get('structure_type') == 'title_page':
                if 'title' in content:
                    content_parts.append(f"# {content['title']}")
                if 'exam_info' in content and isinstance(content['exam_info'], dict):
                    for key, value in content['exam_info'].items():
                        content_parts.append(f"- {key}: {value}")
                if 'organization' in content:
                    content_parts.append(f"\n{content['organization']}")
            
            # 문제 페이지 처리
            elif data.get('structure_type') == 'problem_page':
                # 헤더 정보
                if 'header' in content and isinstance(content['header'], dict):
                    header = content['header']
                    content_parts.append(f"{header.get('class', '')} {header.get('subject', '')} {header.get('page', '')}")
                
                # 문제들
                if 'questions' in content and isinstance(content['questions'], list):
                    for q in content['questions']:
                        if isinstance(q, dict):
                            content_parts.append(f"\n{q.get('number', '')}")
                            content_parts.append(q.get('text', ''))
                            
                            # 표가 있으면 추가
                            if 'table' in q:
                                table_text = extract_text_from_dict({'table': q['table']})
                                content_parts.append(table_text)
                            
                            if 'sub_text' in q:
                                content_parts.append(q['sub_text'])
            
            # 기타 딕셔너리 형식
            else:
                content_parts.append(extract_text_from_dict(content))
    
    # 추가 필드들 처리 (problems, tables_detail 등)
    for key in ['problems', 'tables_detail', 'extraction_notes', 'notes']:
        if key in data and key != 'content':
            if isinstance(data[key], str):
                content_parts.append(f"\n[{key}] {data[key]}")
            elif isinstance(data[key], (dict, list)):
                content_parts.append(f"\n[{key}]")
                if isinstance(data[key], dict):
                    content_parts.append(extract_text_from_dict(data[key]))
                else:
                    content_parts.append(json.dumps(data[key], ensure_ascii=False, indent=2))
    
    return "\n".join(content_parts)

def merge_year_universal(year: str, debug: bool = False):
    """모든 JSON 형식을 지원하는 범용 통합 함수"""
    input_folder = Path(f"{year}/vision_output")
    
    if not input_folder.exists():
        # workspace 폴더 체크
        if year == "2024":
            input_folder = Path("workspace/vision_output")
        
        if not input_folder.exists():
            print(f"❌ {input_folder} 폴더를 찾을 수 없습니다.")
            return
    
    # 페이지별로 파일 그룹화
    pages_dict = {}
    for json_file in input_folder.glob("page_*.json"):
        match = re.search(r'page_(\d{3})', json_file.name)
        if match:
            page_num = int(match.group(1))
            if page_num not in pages_dict:
                pages_dict[page_num] = []
            pages_dict[page_num].append(json_file)
    
    if not pages_dict:
        print(f"❌ {input_folder}에 JSON 파일이 없습니다.")
        return
    
    print(f"📁 폴더: {input_folder}")
    print(f"📄 발견된 페이지: {len(pages_dict)}개")
    
    # 통합할 내용
    all_content = []
    processed_pages = 0
    skipped_pages = 0
    
    # 페이지 순서대로 처리
    for page_num in sorted(pages_dict.keys()):
        files = pages_dict[page_num]
        
        # 가장 최신 버전 선택 (_추출_수정 > _추출_N > _extracted)
        def get_priority(filename):
            if '추출_수정' in filename.name:
                return 3
            elif '추출_' in filename.name:
                match = re.search(r'추출_(\d+)', filename.name)
                return 2 + (int(match.group(1)) / 100 if match else 0)
            else:
                return 1
        
        selected_file = max(files, key=get_priority)
        
        if debug:
            print(f"\n페이지 {page_num}: {selected_file.name} 선택")
        
        try:
            with open(selected_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 내용 추출 (모든 형식 지원)
            content = extract_content_from_json(data)
            
            if content.strip():
                all_content.append(content)
                processed_pages += 1
                
                if debug:
                    print(f"  ✓ 내용 추출 성공 ({len(content)} 문자)")
                    # 구조 타입 표시
                    if 'structure_type' in data:
                        print(f"  - 구조 타입: {data['structure_type']}")
                    if 'content' in data:
                        content_type = type(data['content']).__name__
                        print(f"  - content 타입: {content_type}")
            else:
                skipped_pages += 1
                if debug:
                    print(f"  ✗ 내용이 비어있음")
                    
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            skipped_pages += 1
    
    # 파일 저장
    subject = "원가관리회계" if year == "2025" else "원가회계"
    output_file = f"{subject}_{year}_v3.00_universal.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n\n---\n\n".join(all_content))
    
    # 결과 출력
    print(f"\n✅ {year}년 통합 완료!")
    print(f"📄 출력 파일: {output_file}")
    print(f"📊 통계:")
    print(f"  - 총 페이지: {len(pages_dict)}")
    print(f"  - 처리됨: {processed_pages}")
    print(f"  - 건너뜀: {skipped_pages}")
    print(f"  - 총 라인 수: {len(open(output_file, 'r', encoding='utf-8').readlines())}")

def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법: python merge_universal.py 연도 [--debug]")
        print("예시: python merge_universal.py 2023")
        print("      python merge_universal.py 2023 --debug")
        sys.exit(1)
    
    year = sys.argv[1]
    debug = len(sys.argv) > 2 and sys.argv[2] == '--debug'
    
    merge_year_universal(year, debug)

if __name__ == "__main__":
    main()