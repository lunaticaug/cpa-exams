"""
기능: Vision API 기반 PDF to Markdown 변환기
입력: PDF 파일
출력: 정확한 구조의 Markdown 파일
"""

import base64
import requests
from pathlib import Path
from typing import Dict, List, Optional
import PyPDF2
from pdf2image import convert_from_path
import tempfile
import os

class VisionAPIConverter:
    def __init__(self, api_key: Optional[str] = None):
        """
        Vision API 변환기 초기화
        
        Args:
            api_key: OpenAI API key (환경변수 OPENAI_API_KEY로도 설정 가능)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
    def convert_pdf(self, pdf_path: Path, output_path: Path) -> bool:
        """
        PDF를 Vision API를 사용하여 Markdown으로 변환
        
        Args:
            pdf_path: 입력 PDF 경로
            output_path: 출력 Markdown 경로
            
        Returns:
            bool: 성공 여부
        """
        print(f"Vision API 변환 시작: {pdf_path.name}")
        
        try:
            # PDF를 이미지로 변환
            images = self._pdf_to_images(pdf_path)
            
            # 각 페이지를 Vision API로 분석
            all_content = []
            for i, image_path in enumerate(images, 1):
                print(f"\n페이지 {i}/{len(images)} 분석 중...")
                page_content = self._analyze_page_with_vision(image_path, i)
                all_content.append(page_content)
                
                # 임시 이미지 파일 삭제
                os.remove(image_path)
            
            # 전체 내용 조합
            final_markdown = self._combine_pages(all_content, pdf_path.stem)
            
            # 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_markdown)
            
            print(f"\n변환 완료: {output_path}")
            return True
            
        except Exception as e:
            print(f"변환 중 오류 발생: {e}")
            return False
    
    def _pdf_to_images(self, pdf_path: Path) -> List[str]:
        """PDF를 페이지별 이미지로 변환"""
        with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(pdf_path, dpi=300)
            image_paths = []
            
            for i, image in enumerate(images):
                image_path = f"{temp_dir}/page_{i+1}.png"
                image.save(image_path, 'PNG')
                image_paths.append(image_path)
            
            return image_paths
    
    def _encode_image(self, image_path: str) -> str:
        """이미지를 base64로 인코딩"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _analyze_page_with_vision(self, image_path: str, page_num: int) -> str:
        """Vision API로 페이지 분석"""
        base64_image = self._encode_image(image_path)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "system",
                    "content": """You are an expert at converting Korean CPA exam PDFs to Markdown.
                    The document has a 2-column layout. Read from top to bottom in the left column first,
                    then continue with the right column.
                    
                    Format rules:
                    - Main questions: ### 【문제 X】 (XX점)
                    - Sub questions: #### (물음 X)
                    - Notes: > ※ Note content
                    - Data sections: ##### <자료 X>
                    - Tables: Convert to Markdown tables
                    - Answer format sections: **[답안양식]**
                    
                    Preserve all mathematical formulas, numbers, and Korean text exactly as shown.
                    """
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Convert this exam page (page {page_num}) to Markdown following the format rules. Read left column first, then right column:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 4096
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
    
    def _combine_pages(self, pages: List[str], title: str) -> str:
        """페이지들을 하나의 Markdown으로 조합"""
        lines = [f"# {title}\n"]
        lines.append("> Vision API로 정확하게 변환된 문서\n")
        
        for i, page_content in enumerate(pages, 1):
            if i > 1:
                lines.append("\n---\n")
            lines.append(f"\n## 페이지 {i}\n")
            lines.append(page_content)
        
        return '\n'.join(lines)


def main():
    """테스트 실행"""
    converter = VisionAPIConverter()
    
    # 2024년 원가회계 파일 변환
    base_dir = Path(__file__).parent.parent.parent  # using-claudecode 디렉토리로 이동
    pdf_path = base_dir / "_source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf"
    output_path = base_dir / "output/converted_files/2024_원가회계_v2.00_vision_api.md"
    
    if pdf_path.exists():
        success = converter.convert_pdf(pdf_path, output_path)
        if success:
            print("\n✅ Vision API 변환 성공!")
            
            # 결과 미리보기
            with open(output_path, 'r', encoding='utf-8') as f:
                preview = f.read()[:2000]
                print("\n=== 변환 결과 미리보기 ===")
                print(preview)
                print("...")
    else:
        print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")


if __name__ == "__main__":
    main()