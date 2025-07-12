"""
기능: PDF를 페이지별 이미지로 변환 (Vision API 준비)
입력: PDF 파일 경로
출력: workspace/vision_input/ 폴더에 페이지별 PNG 이미지
버전: v2.00
"""

import fitz  # PyMuPDF
from pathlib import Path
import sys


def convert_pdf_to_images(pdf_path, output_dir=None, dpi=150):
    """
    PDF를 페이지별 이미지로 변환
    
    Args:
        pdf_path: PDF 파일 경로
        output_dir: 출력 디렉토리 (기본: workspace/vision_input/)
        dpi: 해상도 (기본: 150)
    
    Returns:
        list: 생성된 이미지 파일 경로 리스트
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return []
    
    # 출력 디렉토리 설정
    if output_dir is None:
        output_dir = Path("workspace/vision_input")
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # PDF 열기
    print(f"📄 PDF 변환 시작: {pdf_path.name}")
    doc = fitz.open(pdf_path)
    
    # 생성된 이미지 경로들
    image_paths = []
    
    # 각 페이지를 이미지로 변환
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 해상도 설정 (150 DPI = 약 2배 확대)
        mat = fitz.Matrix(dpi/72.0, dpi/72.0)
        pix = page.get_pixmap(matrix=mat)
        
        # 이미지 파일명
        img_filename = f"page_{page_num + 1:03d}.png"
        img_path = output_dir / img_filename
        
        # 이미지 저장
        pix.save(str(img_path))
        image_paths.append(str(img_path))
        
        print(f"  ✅ 페이지 {page_num + 1}/{len(doc)} → {img_filename}")
    
    doc.close()
    
    print(f"\n✨ 변환 완료! 총 {len(image_paths)}개 이미지 생성")
    print(f"📁 저장 위치: {output_dir}")
    
    return image_paths


def main():
    """메인 함수"""
    # 명령줄 인자 확인
    if len(sys.argv) < 2:
        print("사용법: python pdf_to_images.py <PDF파일경로> [출력디렉토리]")
        print("예시: python pdf_to_images.py _source/2024_2차_원가회계.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    # PDF를 이미지로 변환
    image_paths = convert_pdf_to_images(pdf_path, output_dir)
    
    if image_paths:
        print("\n다음 단계:")
        print("1. 생성된 이미지를 Claude가 읽어서 구조화된 텍스트 추출")
        print("2. vision_extractor.py 실행")


if __name__ == "__main__":
    main()