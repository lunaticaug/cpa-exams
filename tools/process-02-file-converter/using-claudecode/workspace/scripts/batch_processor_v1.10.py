"""
기능: 개선된 일괄 PDF to Markdown 변환
입력: source 폴더의 PDF 파일들
출력: 구조화된 Markdown 파일들
"""

from pathlib import Path
import json
from datetime import datetime
from process_08_improved_pdf_converter import ImprovedPDFConverter

def batch_convert_improved():
    """개선된 일괄 변환 실행"""
    print("=== 개선된 PDF → Markdown 일괄 변환 ===\n")
    
    # 설정
    source_dir = Path("source")
    output_dir = Path("output/markdown_final")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 기존 출력 삭제 옵션
    if output_dir.exists():
        existing_files = list(output_dir.glob("*.md"))
        if existing_files:
            print(f"기존 파일 {len(existing_files)}개 발견")
            response = input("기존 파일을 덮어쓰시겠습니까? (y/n): ")
            if response.lower() != 'y':
                print("변환 취소")
                return
    
    # PDF 파일 목록
    pdf_files = sorted(source_dir.glob("*.pdf"), 
                      key=lambda x: x.name.split('_')[0], 
                      reverse=True)
    
    print(f"\n총 {len(pdf_files)}개 PDF 파일 발견")
    
    # 변환기 생성
    converter = ImprovedPDFConverter()
    
    # 변환 실행
    results = []
    success_count = 0
    
    for pdf_file in pdf_files:
        output_file = output_dir / f"{pdf_file.stem}.md"
        
        try:
            converter.convert_single_pdf(pdf_file, output_file)
            success_count += 1
            results.append({
                "file": pdf_file.name,
                "status": "success",
                "output": str(output_file),
                "table_count": converter.table_counter
            })
        except Exception as e:
            results.append({
                "file": pdf_file.name,
                "status": "error",
                "error": str(e)
            })
            print(f"  ✗ 오류: {pdf_file.name} - {e}")
    
    # 결과 요약
    print(f"\n=== 변환 완료 ===")
    print(f"성공: {success_count}/{len(pdf_files)}")
    print(f"실패: {len(pdf_files) - success_count}/{len(pdf_files)}")
    
    # 상세 보고서 생성
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(pdf_files),
        "success": success_count,
        "failed": len(pdf_files) - success_count,
        "output_directory": str(output_dir),
        "conversion_details": results
    }
    
    with open("output-10-final-conversion-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n상세 보고서: output-10-final-conversion-report.json")
    print(f"변환된 파일들: {output_dir}/")
    
    # HWP 파일 상태 확인
    hwp_files = list(source_dir.glob("*.hwp"))
    hwp_only = []
    
    for hwp in hwp_files:
        year = hwp.name.split('_')[0]
        pdf_exists = any(pdf.name.startswith(year) for pdf in pdf_files)
        if not pdf_exists:
            hwp_only.append(hwp.name)
    
    if hwp_only:
        print(f"\n【HWP → DOCX 변환 필요】")
        print(f"PDF 버전이 없는 HWP 파일: {len(hwp_only)}개")
        for hwp in hwp_only[:5]:  # 처음 5개만 표시
            print(f"  - {hwp}")
        if len(hwp_only) > 5:
            print(f"  ... 외 {len(hwp_only) - 5}개")
        print("\n변환 가이드: HWP_CONVERSION_GUIDE.md 참조")

if __name__ == "__main__":
    # process_08 모듈이 없는 경우를 대비한 폴백
    try:
        batch_convert_improved()
    except ImportError:
        print("process_08_improved_pdf_converter.py 파일이 필요합니다.")
        print("파일명을 process_08_improved_pdf_converter.py로 변경해주세요.")