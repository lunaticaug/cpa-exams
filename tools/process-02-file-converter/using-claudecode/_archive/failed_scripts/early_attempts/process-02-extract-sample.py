"""
기능: PDF 샘플 페이지 상세 추출
입력: PDF 파일
출력: 텍스트, 표 구조 샘플
"""

import pdfplumber
from pathlib import Path

def extract_page_details(pdf_path, page_num=0):
    """특정 페이지의 상세 내용을 추출합니다."""
    
    with pdfplumber.open(pdf_path) as pdf:
        if page_num >= len(pdf.pages):
            return None
            
        page = pdf.pages[page_num]
        
        print(f"\n=== {pdf_path.name} - 페이지 {page_num + 1} ===\n")
        
        # 텍스트 추출
        text = page.extract_text()
        if text:
            print("【텍스트 내용】")
            print("-" * 50)
            print(text[:1000])  # 처음 1000자
            print("-" * 50)
        
        # 표 추출
        tables = page.extract_tables()
        if tables:
            print(f"\n【표 발견: {len(tables)}개】")
            for i, table in enumerate(tables[:2]):  # 처음 2개 표만
                print(f"\n표 {i+1} (크기: {len(table)}행 x {len(table[0]) if table else 0}열)")
                print("-" * 50)
                # 처음 5행만 출력
                for row in table[:5]:
                    # None 값을 빈 문자열로 변환
                    cleaned_row = [cell if cell else "" for cell in row]
                    print(" | ".join(cleaned_row))
                if len(table) > 5:
                    print(f"... ({len(table) - 5}행 더 있음)")
        
        # 페이지 레이아웃 정보
        print(f"\n【페이지 정보】")
        print(f"- 크기: {page.width} x {page.height}")
        print(f"- 문자 수: {len(text) if text else 0}")

def main():
    # 2024년 PDF 샘플 분석 (최근 파일)
    pdf_path = Path("source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf")
    
    if pdf_path.exists():
        # 처음 3페이지 분석
        for page_num in range(3):
            extract_page_details(pdf_path, page_num)
    else:
        print(f"파일을 찾을 수 없습니다: {pdf_path}")

if __name__ == "__main__":
    main()