"""
기능: 효율적인 PDF 처리 시스템 (Read 호출 최소화)
입력: PDF 파일
출력: 구조화된 데이터 with 캐싱
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple
import pdfplumber
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor


@dataclass
class PageInfo:
    """페이지 정보"""
    page_num: int
    text: str
    table_count: int
    complexity_score: float
    has_textbox: bool
    has_multiple_columns: bool


class EfficientPDFProcessor:
    def __init__(self, pdf_path: Path):
        self.pdf_path = Path(pdf_path)
        self.cache = {
            'pages': {},
            'tables': {},
            'images': {},
            'structure': {}
        }
        self.metadata = {}
        
    def analyze_pdf_once(self):
        """PDF를 한 번만 읽어서 모든 기본 정보 추출"""
        print(f"PDF 분석 시작: {self.pdf_path}")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            self.metadata['total_pages'] = len(pdf.pages)
            
            # 모든 페이지 한 번에 분석
            for idx, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                
                # 페이지 정보 수집
                page_info = PageInfo(
                    page_num=idx,
                    text=page_text,
                    table_count=len(page.extract_tables()),
                    complexity_score=self._calculate_complexity(page_text),
                    has_textbox=self._detect_textbox(page_text),
                    has_multiple_columns=self._detect_columns(page_text)
                )
                
                self.cache['pages'][idx] = page_info
                
                # 표 추출 및 캐싱
                tables = page.extract_tables()
                if tables:
                    self.cache['tables'][idx] = tables
                    
        print(f"기본 분석 완료: {len(self.cache['pages'])} 페이지")
        return self._generate_summary()
    
    def _calculate_complexity(self, text: str) -> float:
        """페이지 복잡도 계산"""
        score = 0.0
        
        # 표 지표
        score += text.count('|') * 0.5
        score += text.count('---') * 5
        
        # 숫자 밀도
        numbers = len(re.findall(r'\d+', text))
        score += numbers * 0.3
        
        # 짧은 줄 (레이아웃 문제)
        lines = text.split('\n')
        short_lines = sum(1 for line in lines if 0 < len(line.strip()) < 10)
        score += short_lines * 0.8
        
        # 특수 문자
        score += text.count('￦') * 2
        score += text.count('#') * 1.5
        
        return score
    
    def _detect_textbox(self, text: str) -> bool:
        """글상자 존재 여부 감지"""
        indicators = [
            '<자료',
            '다음과 같다',
            '㈜한국',
            '정책',
            '가정'
        ]
        return any(ind in text for ind in indicators)
    
    def _detect_columns(self, text: str) -> bool:
        """다단 편집 감지"""
        # 비정상적으로 짧은 줄이 연속으로 나타남
        lines = text.split('\n')
        short_consecutive = 0
        
        for line in lines:
            if 0 < len(line.strip()) < 20:
                short_consecutive += 1
                if short_consecutive >= 5:
                    return True
            else:
                short_consecutive = 0
                
        return False
    
    def _generate_summary(self) -> Dict:
        """분석 요약 생성"""
        complex_pages = []
        problem_pages = {}
        
        for page_num, info in self.cache['pages'].items():
            # 복잡한 페이지 식별
            if info.complexity_score > 50:
                complex_pages.append(page_num)
                
            # 문제 페이지 식별
            if match := re.search(r'문제\s*(\d+)', info.text):
                prob_num = int(match.group(1))
                if prob_num not in problem_pages:
                    problem_pages[prob_num] = []
                problem_pages[prob_num].append(page_num)
                
        return {
            'total_pages': self.metadata['total_pages'],
            'complex_pages': complex_pages,
            'problem_pages': problem_pages,
            'total_tables': sum(info.table_count for info in self.cache['pages'].values()),
            'pages_with_textbox': [p for p, info in self.cache['pages'].items() if info.has_textbox],
            'pages_with_columns': [p for p, info in self.cache['pages'].items() if info.has_multiple_columns]
        }
    
    def get_complex_pages_for_vision(self, threshold: float = 70) -> List[int]:
        """Vision 분석이 필요한 페이지 선별"""
        complex_pages = []
        
        for page_num, info in self.cache['pages'].items():
            if (info.complexity_score > threshold or 
                info.has_multiple_columns or
                (info.has_textbox and info.table_count > 1)):
                complex_pages.append(page_num)
                
        return complex_pages
    
    def convert_pages_to_images(self, page_numbers: List[int], output_dir: Path):
        """선택된 페이지만 이미지로 변환"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        doc = fitz.open(self.pdf_path)
        converted = []
        
        for page_num in page_numbers:
            if page_num < len(doc):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x 해상도
                
                img_path = output_dir / f"page_{page_num + 1:03d}.png"
                pix.save(str(img_path))
                
                converted.append(str(img_path))
                print(f"이미지 변환: 페이지 {page_num + 1} → {img_path}")
                
        doc.close()
        return converted
    
    def extract_structured_data(self, page_num: int) -> Dict:
        """특정 페이지의 구조화된 데이터 추출"""
        if page_num not in self.cache['pages']:
            return {}
            
        page_info = self.cache['pages'][page_num]
        tables = self.cache['tables'].get(page_num, [])
        
        # 자료와 물음 찾기
        materials = re.findall(r'<자료\s*(\d*)>', page_info.text)
        questions = re.findall(r'\(물음\s*(\d+)\)', page_info.text)
        
        return {
            'page': page_num + 1,
            'complexity': page_info.complexity_score,
            'materials': materials,
            'questions': questions,
            'table_count': len(tables),
            'table_sizes': [(len(t), len(t[0]) if t else 0) for t in tables],
            'needs_vision': page_info.complexity_score > 70 or page_info.has_multiple_columns
        }
    
    def save_cache(self, output_path: Path):
        """캐시 저장"""
        cache_data = {
            'pdf_path': str(self.pdf_path),
            'metadata': self.metadata,
            'summary': self._generate_summary(),
            'pages': {
                str(k): {
                    'complexity': v.complexity_score,
                    'table_count': v.table_count,
                    'has_textbox': v.has_textbox,
                    'has_columns': v.has_multiple_columns
                }
                for k, v in self.cache['pages'].items()
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        print(f"캐시 저장: {output_path}")


def main():
    # PDF 경로
    pdf_path = Path("/Users/user/GitHub/active/cpa-exams/tools/process-02-file-converter/using-claudecode/source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf")
    
    # 프로세서 생성
    processor = EfficientPDFProcessor(pdf_path)
    
    # 1. 한 번에 모든 정보 추출
    print("=== 1단계: PDF 전체 분석 ===")
    summary = processor.analyze_pdf_once()
    
    print("\n분석 결과:")
    print(f"- 총 페이지: {summary['total_pages']}")
    print(f"- 복잡한 페이지: {summary['complex_pages']}")
    print(f"- 문제별 페이지: {summary['problem_pages']}")
    print(f"- 총 표 개수: {summary['total_tables']}")
    
    # 2. Vision 분석이 필요한 페이지 선별
    print("\n=== 2단계: 복잡한 페이지 선별 ===")
    vision_pages = processor.get_complex_pages_for_vision()
    print(f"Vision 분석 필요: {len(vision_pages)}개 페이지 - {vision_pages}")
    
    # 3. 선택된 페이지만 이미지 변환
    if vision_pages[:3]:  # 처음 3개만 테스트
        print("\n=== 3단계: 이미지 변환 (샘플) ===")
        output_dir = Path("output/vision_pages")
        images = processor.convert_pages_to_images(vision_pages[:3], output_dir)
        print(f"변환 완료: {len(images)}개 이미지")
        
        # 4. CC에서 Read할 수 있도록 경로 출력
        print("\n=== 이미지 분석 준비 완료 ===")
        print("다음 명령으로 이미지를 분석하세요:")
        for img in images:
            print(f"Read {img}")
    
    # 5. 캐시 저장
    cache_path = Path("output/pdf_analysis_cache.json")
    processor.save_cache(cache_path)
    
    # 6. 구조 정보 예시
    print("\n=== 페이지별 구조 정보 (샘플) ===")
    for page in vision_pages[:3]:
        data = processor.extract_structured_data(page)
        print(f"\n페이지 {data['page']}:")
        print(f"  - 복잡도: {data['complexity']:.1f}")
        print(f"  - 표: {data['table_count']}개 {data['table_sizes']}")
        print(f"  - Vision 필요: {data['needs_vision']}")


if __name__ == "__main__":
    main()