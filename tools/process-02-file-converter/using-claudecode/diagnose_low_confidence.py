"""
신뢰도가 낮은 원인 진단 도구
Text Layer와 Vision API 결과의 차이를 상세히 분석합니다.
"""

import json
import pdfplumber
from pathlib import Path
import difflib
import re

def diagnose_comparison(pdf_path: Path, vision_json_path: Path, page_num: int = 1):
    """Text Layer와 Vision API 비교 진단"""
    
    print(f"\n{'='*60}")
    print(f"진단: {pdf_path.name} - 페이지 {page_num}")
    print(f"{'='*60}\n")
    
    # 1. Text Layer 추출
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num - 1]
        text_layer = page.extract_text() or ""
        
    # 2. Vision API 결과 로드
    with open(vision_json_path, 'r', encoding='utf-8') as f:
        vision_data = json.load(f)
        vision_text = vision_data.get('content', '')
    
    # 3. 기본 정보 출력
    print(f"Text Layer 길이: {len(text_layer)} 문자")
    print(f"Vision API 길이: {len(vision_text)} 문자")
    
    # 4. 정규화
    def normalize(text):
        # 공백 정규화
        text = re.sub(r'\s+', ' ', text)
        # 특수문자 정규화
        text = text.replace('（', '(').replace('）', ')')
        text = text.replace('［', '[').replace('］', ']')
        return text.strip()
    
    text_layer_norm = normalize(text_layer)
    vision_text_norm = normalize(vision_text)
    
    # 5. 유사도 계산
    similarity = difflib.SequenceMatcher(None, text_layer_norm, vision_text_norm).ratio()
    print(f"\n전체 유사도: {similarity:.2%}")
    
    # 6. 라인별 비교
    text_lines = text_layer.split('\n')
    vision_lines = vision_text.split('\n')
    
    print(f"\nText Layer 라인 수: {len(text_lines)}")
    print(f"Vision API 라인 수: {len(vision_lines)}")
    
    # 7. 차이점 분석
    print("\n주요 차이점:")
    
    # 처음 10줄 비교
    print("\n[처음 10줄 비교]")
    for i in range(min(10, max(len(text_lines), len(vision_lines)))):
        t_line = text_lines[i] if i < len(text_lines) else "[없음]"
        v_line = vision_lines[i] if i < len(vision_lines) else "[없음]"
        
        if t_line.strip() != v_line.strip():
            print(f"\n라인 {i+1}:")
            print(f"  Text: {t_line[:60]}...")
            print(f"  Vision: {v_line[:60]}...")
    
    # 8. 표 구조 분석
    print("\n[표 구조 분석]")
    
    # Text Layer에서 표 감지
    text_tables = page.extract_tables() if 'page' in locals() else []
    print(f"Text Layer 표 개수: {len(text_tables)}")
    
    # Vision API에서 표 감지 (마크다운 표)
    vision_table_count = vision_text.count('\n|')
    print(f"Vision API 표 라인 수: {vision_table_count}")
    
    # 9. 숫자 패턴 분석
    print("\n[숫자 패턴 분석]")
    
    text_numbers = re.findall(r'\d+', text_layer)
    vision_numbers = re.findall(r'\d+', vision_text)
    
    print(f"Text Layer 숫자 개수: {len(text_numbers)}")
    print(f"Vision API 숫자 개수: {len(vision_numbers)}")
    
    # 처음 20개 숫자 비교
    print("\n처음 20개 숫자:")
    print(f"Text: {text_numbers[:20]}")
    print(f"Vision: {vision_numbers[:20]}")
    
    # 10. 구조적 차이
    print("\n[구조적 차이]")
    
    # 마크다운 요소
    md_headers = len(re.findall(r'^#+\s', vision_text, re.MULTILINE))
    print(f"Vision API 마크다운 헤더: {md_headers}개")
    
    # 특수 구조
    text_has_table_markers = '|' in text_layer
    vision_has_table_markers = '|' in vision_text
    print(f"Text Layer 표 마커(|): {text_has_table_markers}")
    print(f"Vision API 표 마커(|): {vision_has_table_markers}")
    
    # 11. 원인 분석
    print("\n[신뢰도가 낮은 원인]")
    
    if similarity < 0.5:
        print("⚠️  매우 낮은 유사도 - 구조적 차이가 큼")
    
    if not text_has_table_markers and vision_has_table_markers:
        print("⚠️  Text Layer에는 표 구조가 없지만 Vision API는 표를 인식함")
    
    if abs(len(text_lines) - len(vision_lines)) > 10:
        print("⚠️  라인 수 차이가 큼 - 레이아웃 해석 차이")
    
    if md_headers > 0:
        print("⚠️  Vision API가 마크다운 형식으로 구조화함")
    
    return {
        'similarity': similarity,
        'text_length': len(text_layer),
        'vision_length': len(vision_text),
        'line_diff': abs(len(text_lines) - len(vision_lines)),
        'has_structural_diff': not text_has_table_markers and vision_has_table_markers
    }

def main():
    """진단 실행"""
    # 2024년 1페이지 진단
    pdf_path = Path("_source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf")
    vision_path = Path("__temp/workspace/vision_output/page_001_추출_4.json")
    
    if pdf_path.exists() and vision_path.exists():
        result = diagnose_comparison(pdf_path, vision_path, 1)
        
        print("\n" + "="*60)
        print("진단 결과 요약")
        print("="*60)
        print(f"유사도: {result['similarity']:.2%}")
        print(f"구조적 차이 존재: {result['has_structural_diff']}")
        
        if result['similarity'] < 0.8:
            print("\n권장사항:")
            print("1. Vision API가 마크다운 형식으로 구조화하므로 Text Layer와 직접 비교는 부적절")
            print("2. 내용 기반 비교보다는 데이터 추출 정확도 중심으로 평가 필요")
            print("3. 표 데이터는 별도로 추출하여 셀 단위로 비교")

if __name__ == "__main__":
    main()