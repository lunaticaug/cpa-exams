"""
기능: Claude Vision 기반 PDF 구조 분석 및 변환 가이드
입력: PDF 파일 (이미지로 변환 후 분석)
출력: 정확한 구조 추출을 위한 가이드
"""

from pathlib import Path
import PyPDF2
from pdf2image import convert_from_path
import tempfile
import os

class ClaudeVisionGuide:
    def __init__(self):
        self.structure_template = {
            "format_rules": {
                "main_questions": "### 【문제 X】 (XX점)",
                "sub_questions": "#### (물음 X)",
                "notes": "> ※ 내용",
                "data_sections": "##### <자료 X>",
                "answer_format": "**[답안양식]**",
                "tables": "Markdown 표 형식"
            },
            "reading_order": "좌측 컬럼 위→아래, 이후 우측 컬럼 위→아래"
        }
    
    def prepare_for_vision_analysis(self, pdf_path: Path, output_dir: Path):
        """
        PDF를 Vision 분석을 위한 이미지로 준비
        
        Args:
            pdf_path: 입력 PDF 경로
            output_dir: 이미지 저장 경로
        """
        print(f"Vision 분석을 위한 이미지 준비: {pdf_path.name}")
        
        # 출력 디렉토리 생성
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # PDF를 이미지로 변환
        images = convert_from_path(pdf_path, dpi=300)
        
        saved_paths = []
        for i, image in enumerate(images, 1):
            image_path = output_dir / f"page_{i:02d}.png"
            image.save(image_path, 'PNG')
            saved_paths.append(image_path)
            print(f"  - 페이지 {i} 저장: {image_path.name}")
        
        # 분석 가이드 생성
        guide_path = output_dir / "vision_analysis_guide.md"
        self._create_analysis_guide(guide_path, saved_paths, pdf_path.stem)
        
        print(f"\n✅ 이미지 준비 완료!")
        print(f"📁 저장 위치: {output_dir}")
        print(f"📋 분석 가이드: {guide_path.name}")
        
        return saved_paths
    
    def _create_analysis_guide(self, guide_path: Path, image_paths: List[Path], title: str):
        """Vision 분석을 위한 가이드 문서 생성"""
        guide_content = f"""# Vision 분석 가이드 - {title}

## 분석 요청사항

다음 이미지들을 분석하여 정확한 Markdown으로 변환해주세요.

### 변환 규칙

1. **읽기 순서**: {self.structure_template['reading_order']}

2. **포맷 규칙**:
   - {self.structure_template['format_rules']['main_questions']}
   - {self.structure_template['format_rules']['sub_questions']}
   - {self.structure_template['format_rules']['notes']}
   - {self.structure_template['format_rules']['data_sections']}
   - {self.structure_template['format_rules']['answer_format']}
   - 표: {self.structure_template['format_rules']['tables']}

3. **주의사항**:
   - 2단 레이아웃의 올바른 순서 유지
   - 수식, 숫자, 한글 텍스트 정확히 보존
   - 표의 구조 정확히 재현

## 이미지 목록

"""
        for i, path in enumerate(image_paths, 1):
            guide_content += f"- 페이지 {i}: `{path.name}`\n"
        
        guide_content += """
## 분석 후 확인사항

1. 모든 문제 번호가 순서대로 있는지
2. 각 물음이 해당 문제 아래에 올바르게 위치하는지
3. 표가 정확히 변환되었는지
4. 수식과 숫자가 정확한지
"""
        
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
    
    def create_structure_template(self, analyzed_content: Dict) -> str:
        """
        Vision 분석 결과를 바탕으로 구조 템플릿 생성
        
        Args:
            analyzed_content: Vision으로 분석한 내용
            
        Returns:
            str: 구조화된 템플릿
        """
        # 이 메서드는 Vision 분석 후 결과를 구조화하는데 사용
        pass


def main():
    """PDF를 Vision 분석용 이미지로 준비"""
    guide = ClaudeVisionGuide()
    
    # 2024년 원가회계 파일 준비
    base_dir = Path(__file__).parent.parent.parent  # using-claudecode 디렉토리로 이동
    pdf_path = base_dir / "_source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf"
    output_dir = base_dir / "output/vision_ready"
    
    if pdf_path.exists():
        image_paths = guide.prepare_for_vision_analysis(pdf_path, output_dir)
        
        print("\n다음 단계:")
        print("1. 생성된 이미지를 Claude에 제공")
        print("2. vision_analysis_guide.md의 지침에 따라 분석 요청")
        print("3. 분석 결과를 Markdown 파일로 저장")
    else:
        print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")


if __name__ == "__main__":
    main()