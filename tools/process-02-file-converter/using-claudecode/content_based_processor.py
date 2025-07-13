"""
콘텐츠 기반 PDF 처리 시스템
구조가 아닌 실제 데이터의 정확도를 평가합니다.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pdfplumber
from datetime import datetime
import difflib

class ContentBasedProcessor:
    def __init__(self):
        self.evaluation_weights = {
            'numbers_accuracy': 0.4,      # 숫자 정확도
            'table_data_accuracy': 0.3,   # 표 데이터 정확도
            'key_terms_presence': 0.2,    # 핵심 용어 존재
            'structural_quality': 0.1     # 구조 품질
        }
    
    def extract_content_only(self, text: str) -> Dict:
        """텍스트에서 순수 콘텐츠만 추출"""
        # 마크다운 제거
        content = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # 헤더 제거
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)       # 볼드 제거
        content = re.sub(r'\*([^*]+)\*', r'\1', content)           # 이탤릭 제거
        
        # 표에서 데이터 추출
        table_data = []
        # 마크다운 표 찾기
        table_lines = re.findall(r'\|[^|\n]+\|', content)
        for line in table_lines:
            # 구분선 제외
            if not re.match(r'^\|[\s\-:|]+\|$', line.strip()):
                # | 로 둘러싸인 내용에서 데이터 추출
                cells = [cell.strip() for cell in re.split(r'\|', line) if cell.strip()]
                table_data.extend(cells)
        
        # Text Layer의 표 형식 (공백으로 구분된 데이터)도 추출
        if not table_data:  # 마크다운 표가 없으면
            # 연속된 숫자나 용어가 있는 라인 찾기
            lines = content.split('\n')
            for line in lines:
                # 공백으로 구분된 여러 값이 있는 라인
                tokens = line.split()
                if len(tokens) >= 3 and any(token.isdigit() or '￦' in token for token in tokens):
                    table_data.extend(tokens)
        
        # 일반 텍스트 (표 제외)
        text_without_tables = re.sub(r'^\|.*\|$', '', content, flags=re.MULTILINE)
        
        # 숫자 추출
        numbers = re.findall(r'[\d,]+(?:\.\d+)?', content)
        numbers = [n.replace(',', '') for n in numbers]  # 콤마 제거
        
        # 핵심 용어 추출
        key_terms = re.findall(r'[가-힣]+부문|[가-힣]+원가|￦[\d,]+', content)
        
        return {
            'pure_text': text_without_tables.strip(),
            'table_data': table_data,
            'numbers': numbers,
            'key_terms': key_terms
        }
    
    def evaluate_content_accuracy(self, text_content: Dict, vision_content: Dict) -> Dict:
        """콘텐츠 정확도 평가"""
        scores = {}
        
        # 1. 숫자 정확도
        text_nums = set(text_content['numbers'])
        vision_nums = set(vision_content['numbers'])
        
        if text_nums or vision_nums:
            common_nums = text_nums & vision_nums
            all_nums = text_nums | vision_nums
            scores['numbers_accuracy'] = len(common_nums) / len(all_nums) if all_nums else 0
        else:
            scores['numbers_accuracy'] = 1.0  # 숫자가 없으면 만점
        
        # 2. 표 데이터 정확도
        if text_content['table_data'] or vision_content['table_data']:
            # 순서 무관하게 비교
            text_cells = set(text_content['table_data'])
            vision_cells = set(vision_content['table_data'])
            
            common_cells = text_cells & vision_cells
            all_cells = text_cells | vision_cells
            scores['table_data_accuracy'] = len(common_cells) / len(all_cells) if all_cells else 0
        else:
            scores['table_data_accuracy'] = 1.0
        
        # 3. 핵심 용어 존재
        text_terms = set(text_content['key_terms'])
        vision_terms = set(vision_content['key_terms'])
        
        if text_terms or vision_terms:
            common_terms = text_terms & vision_terms
            important_terms = text_terms if len(text_terms) > len(vision_terms) else vision_terms
            scores['key_terms_presence'] = len(common_terms) / len(important_terms) if important_terms else 0
        else:
            scores['key_terms_presence'] = 1.0
        
        # 4. 구조 품질 (Vision API가 표를 인식했는가?)
        has_structured_table = len(vision_content['table_data']) > 0
        scores['structural_quality'] = 1.0 if has_structured_table else 0.7
        
        # 가중 평균
        total_score = sum(scores[key] * self.evaluation_weights[key] 
                         for key in self.evaluation_weights)
        
        return {
            'total_score': total_score,
            'details': scores,
            'confidence_level': self.get_confidence_level(total_score)
        }
    
    def get_confidence_level(self, score: float) -> str:
        """점수를 신뢰도 레벨로 변환"""
        if score >= 0.9:
            return "매우 높음"
        elif score >= 0.8:
            return "높음"
        elif score >= 0.7:
            return "보통"
        elif score >= 0.6:
            return "낮음"
        else:
            return "매우 낮음"
    
    def process_page_content_based(self, pdf_path: Path, page_num: int, 
                                  vision_json_path: Optional[Path] = None) -> Dict:
        """콘텐츠 기반 페이지 처리"""
        # Text Layer 추출
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num - 1]
            text_raw = page.extract_text() or ""
        
        text_content = self.extract_content_only(text_raw)
        
        # Vision API 결과
        if vision_json_path and vision_json_path.exists():
            with open(vision_json_path, 'r', encoding='utf-8') as f:
                vision_data = json.load(f)
                vision_raw = vision_data.get('content', '')
            vision_content = self.extract_content_only(vision_raw)
            
            # 평가
            evaluation = self.evaluate_content_accuracy(text_content, vision_content)
            
            # Vision API가 더 많은 구조 정보를 포함하면 사용
            if len(vision_content['table_data']) > len(text_content['table_data']):
                final_content = vision_raw
                source = "vision_enhanced"
            else:
                final_content = text_raw
                source = "text_layer"
        else:
            final_content = text_raw
            source = "text_only"
            evaluation = {'total_score': 0.85, 'confidence_level': '높음'}
        
        return {
            'content': final_content,
            'confidence': evaluation['total_score'],
            'confidence_level': evaluation['confidence_level'],
            'source': source,
            'evaluation_details': evaluation.get('details', {})
        }
    
    def demonstrate_evaluation(self):
        """평가 방식 시연"""
        print("\n" + "="*60)
        print("콘텐츠 기반 평가 시연")
        print("="*60)
        
        # 예시 데이터
        text_example = """
        원가회계
        【문제 1】(24점)
        수선부문 400 160 160 480 800
        식당부문 54 60 162 108 216
        실제 변동원가 수선시간당 ￦47 1명당 ￦50
        """
        
        vision_example = """
        # 원가회계
        
        【문제 1】 (24점)
        
        | 제공부문 | 수선 | 식당 | X | Y | Z |
        |---------|------|------|---|---|---|
        | 수선부문 | 400 | 160 | 160 | 480 | 800 |
        | 식당부문 | 54 | 60 | 162 | 108 | 216 |
        
        | 구분 | 수선부문 | 식당부문 |
        |------|----------|----------|
        | 실제 변동원가 | 수선시간당 ￦47 | 1명당 ￦50 |
        """
        
        # 콘텐츠 추출
        text_content = self.extract_content_only(text_example)
        vision_content = self.extract_content_only(vision_example)
        
        print("\n[Text Layer 추출 결과]")
        print(f"숫자: {text_content['numbers'][:10]}...")
        print(f"표 데이터: {text_content['table_data'][:5]}...")
        
        print("\n[Vision API 추출 결과]")
        print(f"숫자: {vision_content['numbers'][:10]}...")
        print(f"표 데이터: {vision_content['table_data'][:5]}...")
        
        # 평가
        evaluation = self.evaluate_content_accuracy(text_content, vision_content)
        
        print("\n[평가 결과]")
        print(f"총점: {evaluation['total_score']:.2%}")
        print(f"신뢰도: {evaluation['confidence_level']}")
        print("\n세부 점수:")
        for key, score in evaluation['details'].items():
            print(f"  - {key}: {score:.2%}")

def main():
    """메인 실행"""
    processor = ContentBasedProcessor()
    
    # 시연
    processor.demonstrate_evaluation()
    
    # 실제 파일 테스트
    pdf_path = Path("_source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf")
    vision_path = Path("__temp/workspace/vision_output/page_001_추출_4.json")
    
    if pdf_path.exists() and vision_path.exists():
        print("\n\n" + "="*60)
        print("실제 파일 평가")
        print("="*60)
        
        result = processor.process_page_content_based(pdf_path, 1, vision_path)
        
        print(f"\n최종 신뢰도: {result['confidence']:.2%}")
        print(f"신뢰도 레벨: {result['confidence_level']}")
        print(f"데이터 소스: {result['source']}")
        print("\n세부 평가:")
        for key, score in result['evaluation_details'].items():
            print(f"  - {key}: {score:.2%}")

if __name__ == "__main__":
    main()