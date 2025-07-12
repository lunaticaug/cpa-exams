"""
기능: 변환 대상 파일 목록 생성 및 우선순위 설정
입력: source 폴더의 HWP/PDF 파일
출력: 변환 작업 목록 JSON
"""

from pathlib import Path
import json
from datetime import datetime

def create_conversion_list():
    source_dir = Path("source")
    
    # 모든 파일 수집
    all_files = {}
    
    # HWP 파일 처리
    for hwp in source_dir.glob("*.hwp"):
        year = hwp.name.split('_')[0]
        if year not in all_files:
            all_files[year] = {"hwp": None, "pdf": None}
        all_files[year]["hwp"] = hwp.name
    
    # PDF 파일 처리
    for pdf in source_dir.glob("*.pdf"):
        year = pdf.name.split('_')[0]
        if year not in all_files:
            all_files[year] = {"hwp": None, "pdf": None}
        all_files[year]["pdf"] = pdf.name
    
    # 변환 작업 목록 생성
    conversion_tasks = []
    
    for year in sorted(all_files.keys(), reverse=True):  # 최신 연도부터
        files = all_files[year]
        
        task = {
            "year": year,
            "hwp_file": files.get("hwp"),
            "pdf_file": files.get("pdf"),
            "status": "pending",
            "priority": 1 if files.get("pdf") else 2,  # PDF 있으면 우선순위 높음
            "conversion_needed": "HWP_TO_PDF" if not files.get("pdf") else "NONE",
            "markdown_output": f"{year}_2차_원가회계.md"
        }
        
        conversion_tasks.append(task)
    
    # 통계 생성
    stats = {
        "total_years": len(all_files),
        "pdf_available": len([t for t in conversion_tasks if t["pdf_file"]]),
        "hwp_only": len([t for t in conversion_tasks if t["conversion_needed"] == "HWP_TO_PDF"]),
        "created_at": datetime.now().isoformat()
    }
    
    result = {
        "stats": stats,
        "tasks": conversion_tasks
    }
    
    # 저장
    with open("output-05-conversion-tasks.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 요약 출력
    print("=== 변환 작업 목록 생성 완료 ===\n")
    print(f"총 {stats['total_years']}개 연도")
    print(f"- PDF 사용 가능: {stats['pdf_available']}개")
    print(f"- HWP→PDF 변환 필요: {stats['hwp_only']}개")
    
    print("\n【HWP→PDF 변환이 필요한 파일】")
    for task in conversion_tasks:
        if task["conversion_needed"] == "HWP_TO_PDF":
            print(f"- {task['year']}년: {task['hwp_file']}")
    
    print("\n【다음 단계】")
    print("1. HWP 전용 파일들을 온라인 도구나 한컴오피스로 PDF 변환")
    print("2. 변환된 PDF를 source 폴더에 추가")
    print("3. process-06-batch-convert.py 실행하여 일괄 Markdown 변환")
    
    return result

if __name__ == "__main__":
    create_conversion_list()