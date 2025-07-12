"""
기능: PDF/HWP 문서 구조 분석 도구
입력: PDF 또는 HWP 파일
출력: 문서 구조 분석 리포트
"""

import pdfplumber
import fitz  # PyMuPDF
from pathlib import Path
import json

def analyze_pdf_structure(pdf_path):
    """PDF 파일의 구조를 분석합니다."""
    analysis = {
        "file": str(pdf_path),
        "pages": [],
        "has_text": False,
        "has_tables": False,
        "has_images": False,
        "text_extraction_method": None
    }
    
    # pdfplumber로 텍스트와 표 분석
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_info = {
                "page_num": i + 1,
                "text_length": 0,
                "tables_count": 0,
                "has_text": False,
                "has_tables": False
            }
            
            # 텍스트 추출
            text = page.extract_text()
            if text:
                page_info["text_length"] = len(text)
                page_info["has_text"] = True
                analysis["has_text"] = True
                # 샘플 텍스트 저장 (처음 200자)
                page_info["text_sample"] = text[:200].replace('\n', ' ')
            
            # 표 감지
            tables = page.extract_tables()
            if tables:
                page_info["tables_count"] = len(tables)
                page_info["has_tables"] = True
                analysis["has_tables"] = True
                # 첫 번째 표의 구조 저장
                if tables[0]:
                    page_info["first_table_size"] = f"{len(tables[0])}x{len(tables[0][0]) if tables[0] else 0}"
            
            analysis["pages"].append(page_info)
    
    # PyMuPDF로 이미지 분석
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc):
        image_list = page.get_images()
        if image_list:
            analysis["has_images"] = True
            analysis["pages"][i]["images_count"] = len(image_list)
            analysis["pages"][i]["has_images"] = True
    doc.close()
    
    # 최적 추출 방법 결정
    if analysis["has_text"]:
        if analysis["has_tables"]:
            analysis["text_extraction_method"] = "hybrid (pdfplumber for text/tables + vision for complex layouts)"
        else:
            analysis["text_extraction_method"] = "pdfplumber (direct text extraction)"
    else:
        analysis["text_extraction_method"] = "OCR required (no text layer found)"
    
    return analysis

def main():
    # 샘플 PDF 파일 분석
    source_dir = Path("source")
    pdf_files = list(source_dir.glob("*.pdf"))[:3]  # 처음 3개만
    
    results = []
    for pdf_file in pdf_files:
        print(f"\n분석 중: {pdf_file.name}")
        try:
            result = analyze_pdf_structure(pdf_file)
            results.append(result)
            
            # 간단한 요약 출력
            print(f"  - 페이지 수: {len(result['pages'])}")
            print(f"  - 텍스트 레이어: {'있음' if result['has_text'] else '없음'}")
            print(f"  - 표: {'있음' if result['has_tables'] else '없음'}")
            print(f"  - 이미지: {'있음' if result['has_images'] else '없음'}")
            print(f"  - 권장 추출 방법: {result['text_extraction_method']}")
            
            if result['pages'] and result['pages'][0].get('text_sample'):
                print(f"  - 텍스트 샘플: {result['pages'][0]['text_sample'][:100]}...")
        except Exception as e:
            print(f"  - 오류 발생: {e}")
    
    # 결과 저장
    with open("output-01-document-analysis.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n분석 완료. 결과가 output-01-document-analysis.json에 저장되었습니다.")

if __name__ == "__main__":
    main()