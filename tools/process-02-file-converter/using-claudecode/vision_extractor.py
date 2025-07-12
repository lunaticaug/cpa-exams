"""
기능: Claude Vision을 통해 이미지에서 구조화된 텍스트 추출
입력: 페이지 이미지 파일
출력: workspace/vision_output/ 폴더에 페이지별 JSON
버전: v2.00
"""

import json
from pathlib import Path
import sys


def create_extraction_prompt():
    """Vision API용 프롬프트 생성"""
    return """이 이미지는 한국 공인회계사 시험 문제입니다. 2단 편집된 PDF에서 변환된 이미지입니다.

다음 규칙에 따라 텍스트를 추출해주세요:

1. **읽기 순서**: 왼쪽 열을 위에서 아래로 읽은 후, 오른쪽 열을 위에서 아래로 읽기
2. **구조 보존**:
   - 문제 번호: 【문제 X】 (X점)
   - 자료 상자: <자료 X> 내용 </자료>
   - 물음: (물음 X)
   - 답안양식: **[답안양식]**

3. **표 처리**:
   - 표는 마크다운 형식으로 변환
   - 셀 병합이 있는 경우 명시
   - 빈 셀은 공백으로 표시

4. **특수 요소**:
   - 수식은 원문 그대로 유지
   - 단위 표시 (￦, % 등) 정확히 보존
   - 들여쓰기와 번호 매기기 유지

JSON 형식으로 다음 구조로 반환해주세요:
{
    "page_number": 페이지번호,
    "content": "추출된 전체 텍스트 (마크다운 형식)",
    "problems": [
        {
            "number": 문제번호,
            "points": 배점,
            "materials": ["자료1내용", "자료2내용"],
            "questions": ["물음1", "물음2"],
            "tables": [표 정보]
        }
    ],
    "extraction_notes": "특이사항이나 주의사항"
}"""


def extract_from_image(image_path, page_num):
    """
    이미지에서 텍스트 추출 (실제 구현 시 Claude API 호출)
    
    현재는 사용자가 직접 이미지를 읽고 결과를 입력하도록 안내
    """
    print(f"\n{'='*60}")
    print(f"📄 페이지 {page_num} 처리")
    print(f"이미지 경로: {image_path}")
    print(f"{'='*60}")
    
    print("\n다음 명령어로 이미지를 Claude에게 보여주세요:")
    print(f"Read {image_path}")
    
    print("\n그리고 다음 프롬프트를 사용하세요:")
    print("-" * 60)
    print(create_extraction_prompt())
    print("-" * 60)
    
    # 실제 구현에서는 여기서 API 호출
    # 현재는 더미 데이터 반환
    return {
        "page_number": page_num,
        "content": f"[페이지 {page_num} 내용 - Claude가 추출할 예정]",
        "problems": [],
        "extraction_notes": "수동 추출 필요"
    }


def process_all_images(input_dir="workspace/vision_input", output_dir="workspace/vision_output"):
    """모든 이미지 처리"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    if not input_dir.exists():
        print(f"❌ 입력 디렉토리를 찾을 수 없습니다: {input_dir}")
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 이미지 파일 찾기
    image_files = sorted(input_dir.glob("page_*.png"))
    
    if not image_files:
        print(f"❌ {input_dir}에서 이미지 파일을 찾을 수 없습니다")
        return
    
    print(f"🔍 {len(image_files)}개 이미지 발견")
    
    # 각 이미지 처리
    results = []
    for img_path in image_files:
        # 페이지 번호 추출
        page_num = int(img_path.stem.split('_')[1])
        
        # 이미지에서 텍스트 추출
        result = extract_from_image(str(img_path), page_num)
        
        # 결과 저장
        output_path = output_dir / f"page_{page_num:03d}_extracted.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        results.append(result)
        print(f"  ✅ 저장: {output_path.name}")
    
    print(f"\n✨ 처리 완료! 총 {len(results)}개 페이지")
    print(f"📁 저장 위치: {output_dir}")
    
    # 요약 정보 저장
    summary_path = output_dir / "extraction_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_pages": len(results),
            "status": "manual_extraction_required",
            "next_step": "각 이미지를 Claude에게 보여주고 텍스트 추출"
        }, f, ensure_ascii=False, indent=2)


def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        # 특정 이미지 파일 처리
        image_path = sys.argv[1]
        page_num = 1
        if len(sys.argv) > 2:
            page_num = int(sys.argv[2])
        
        result = extract_from_image(image_path, page_num)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 전체 이미지 처리
        process_all_images()


if __name__ == "__main__":
    main()