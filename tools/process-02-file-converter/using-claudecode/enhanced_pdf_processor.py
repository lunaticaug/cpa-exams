"""
향상된 PDF 처리기 - Vision API와 Text Layer 교차 검증
PDF의 텍스트 레이어와 Vision API 결과를 비교하여 더 정확한 추출 결과를 생성합니다.
"""

import pdfplumber
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import difflib

class EnhancedPDFProcessor:
    def __init__(self):
        self.error_patterns = {
            # 숫자/문자 혼동 패턴
            'digit_confusion': [
                (r'[O0]', ['0', 'O']),  # 0과 O
                (r'[1lI]', ['1', 'l', 'I']),  # 1, l, I
                (r'[5S]', ['5', 'S']),  # 5와 S
                (r'[6G]', ['6', 'G']),  # 6과 G
                (r'[8B]', ['8', 'B']),  # 8과 B
            ],
            # 회계 숫자 패턴
            'accounting_numbers': [
                (r'(\d{1,3})[,.](\d{3})', r'\1,\2'),  # 천단위 구분자
                (r'(\d+)\s+(\d+)', r'\1\2'),  # 숫자 사이 공백 제거
                (r'￦\s*(\d)', r'￦\1'),  # 원화 기호 정규화
            ],
            # 특수문자 패턴
            'special_chars': [
                (r'［', '['),
                (r'］', ']'),
                (r'（', '('),
                (r'）', ')'),
                (r'∼', '~'),
            ]
        }
        
        self.validation_rules = {
            'table_sum': self.validate_table_sum,
            'percentage': self.validate_percentage,
            'balance': self.validate_balance,
        }
        
        self.correction_history = []
        
    def extract_text_layer(self, pdf_path: Path, page_num: int) -> Dict:
        """PDF text layer 추출"""
        with pdfplumber.open(pdf_path) as pdf:
            if page_num <= len(pdf.pages):
                page = pdf.pages[page_num - 1]
                text = page.extract_text() or ""
                tables = page.extract_tables() or []
                
                return {
                    'text': text,
                    'tables': tables,
                    'method': 'text_layer'
                }
        return {'text': '', 'tables': [], 'method': 'text_layer'}
    
    def load_vision_result(self, json_path: Path) -> Dict:
        """Vision API 결과 로드"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'text': data.get('content', ''),
                    'tables': self.extract_tables_from_content(data.get('content', '')),
                    'method': 'vision_api',
                    'raw_data': data
                }
        except:
            return {'text': '', 'tables': [], 'method': 'vision_api'}
    
    def extract_tables_from_content(self, content: str) -> List:
        """Vision API 콘텐츠에서 표 추출"""
        tables = []
        lines = content.split('\n')
        current_table = []
        
        for line in lines:
            if '|' in line and not line.strip().startswith('|--'):
                # 표 행 발견
                row = [cell.strip() for cell in line.split('|') if cell.strip()]
                if row:
                    current_table.append(row)
            elif current_table:
                # 표 끝
                if len(current_table) > 1:  # 최소 2행 이상
                    tables.append(current_table)
                current_table = []
        
        if current_table and len(current_table) > 1:
            tables.append(current_table)
        
        return tables
    
    def cross_validate(self, text_data: Dict, vision_data: Dict) -> Dict:
        """Text layer와 Vision API 결과 교차 검증"""
        validated = {
            'content': '',
            'confidence_scores': {},
            'corrections': [],
            'warnings': []
        }
        
        # 텍스트 비교
        text_similarity = self.calculate_similarity(
            text_data['text'], 
            vision_data['text']
        )
        
        if text_similarity > 0.95:
            # 거의 일치 - text layer 신뢰
            validated['content'] = text_data['text']
            validated['confidence_scores']['overall'] = 0.98
            validated['method'] = 'text_layer_primary'
        elif text_similarity > 0.8:
            # 부분 일치 - 라인별 비교
            validated['content'] = self.merge_by_line(
                text_data['text'], 
                vision_data['text']
            )
            validated['confidence_scores']['overall'] = 0.85
            validated['method'] = 'hybrid'
        else:
            # 큰 차이 - Vision API 우선, text layer로 검증
            validated['content'] = vision_data['text']
            validated['confidence_scores']['overall'] = 0.7
            validated['method'] = 'vision_primary'
            validated['warnings'].append('Text layer와 Vision API 결과 차이가 큼')
        
        # 표 데이터 검증
        validated['tables'] = self.validate_tables(
            text_data['tables'], 
            vision_data['tables']
        )
        
        return validated
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """두 텍스트의 유사도 계산"""
        if not text1 or not text2:
            return 0.0
        
        # 정규화
        text1 = self.normalize_text(text1)
        text2 = self.normalize_text(text2)
        
        # difflib를 사용한 유사도 계산
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def normalize_text(self, text: str) -> str:
        """텍스트 정규화"""
        # 공백 정규화
        text = re.sub(r'\s+', ' ', text)
        # 특수문자 정규화
        for pattern, replacement in self.error_patterns['special_chars']:
            text = re.sub(pattern, replacement, text)
        return text.strip()
    
    def merge_by_line(self, text1: str, text2: str) -> str:
        """라인별로 최적의 텍스트 선택"""
        lines1 = text1.split('\n')
        lines2 = text2.split('\n')
        merged = []
        
        for i in range(max(len(lines1), len(lines2))):
            line1 = lines1[i] if i < len(lines1) else ''
            line2 = lines2[i] if i < len(lines2) else ''
            
            # 숫자가 포함된 라인은 더 신중하게 선택
            if self.contains_numbers(line1) or self.contains_numbers(line2):
                selected = self.select_best_numeric_line(line1, line2)
            else:
                # 더 긴 라인 선택 (더 완전한 정보)
                selected = line1 if len(line1) > len(line2) else line2
            
            if selected.strip():
                merged.append(selected)
        
        return '\n'.join(merged)
    
    def contains_numbers(self, text: str) -> bool:
        """텍스트에 숫자가 포함되어 있는지 확인"""
        if text is None or not isinstance(text, str):
            return False
        return bool(re.search(r'\d', text))
    
    def select_best_numeric_line(self, line1: str, line2: str) -> str:
        """숫자가 포함된 라인 중 최적 선택"""
        # 회계 패턴에 더 잘 맞는 라인 선택
        score1 = self.score_accounting_pattern(line1)
        score2 = self.score_accounting_pattern(line2)
        
        if score1 > score2:
            return line1
        elif score2 > score1:
            return line2
        else:
            # 동점일 경우 더 긴 라인 선택
            return line1 if len(line1) >= len(line2) else line2
    
    def score_accounting_pattern(self, text: str) -> int:
        """회계 패턴 점수 계산"""
        score = 0
        
        # 천단위 구분자가 올바른 경우
        if re.search(r'\d{1,3}(,\d{3})+', text):
            score += 2
        
        # 원화 기호가 있는 경우
        if '￦' in text or '원' in text:
            score += 1
        
        # 괄호 안의 숫자 (마이너스 표시)
        if re.search(r'\(\d+([,.]?\d+)*\)', text):
            score += 1
        
        # 백분율
        if re.search(r'\d+(\.\d+)?%', text):
            score += 1
        
        return score
    
    def validate_tables(self, text_tables: List, vision_tables: List) -> List:
        """표 데이터 검증 및 병합"""
        validated_tables = []
        
        # 더 많은 표를 가진 쪽을 기준으로
        max_tables = max(len(text_tables), len(vision_tables))
        
        for i in range(max_tables):
            text_table = text_tables[i] if i < len(text_tables) else []
            vision_table = vision_tables[i] if i < len(vision_tables) else []
            
            if text_table and vision_table:
                # 두 표 병합
                validated_table = self.merge_tables(text_table, vision_table)
            elif text_table:
                validated_table = text_table
            else:
                validated_table = vision_table
            
            # 표 내용 검증
            if validated_table:
                validated_table = self.validate_table_content(validated_table)
                validated_tables.append(validated_table)
        
        return validated_tables
    
    def merge_tables(self, table1: List, table2: List) -> List:
        """두 표 데이터 병합"""
        merged = []
        max_rows = max(len(table1), len(table2))
        
        for i in range(max_rows):
            row1 = table1[i] if i < len(table1) else []
            row2 = table2[i] if i < len(table2) else []
            
            merged_row = self.merge_table_row(row1, row2)
            merged.append(merged_row)
        
        return merged
    
    def merge_table_row(self, row1: List, row2: List) -> List:
        """표의 행 병합"""
        merged = []
        max_cols = max(len(row1), len(row2))
        
        for i in range(max_cols):
            cell1 = row1[i] if i < len(row1) else ''
            cell2 = row2[i] if i < len(row2) else ''
            
            # None 처리
            cell1 = '' if cell1 is None else str(cell1)
            cell2 = '' if cell2 is None else str(cell2)
            
            # 셀 내용 선택
            if self.contains_numbers(cell1) or self.contains_numbers(cell2):
                selected = self.select_best_numeric_line(cell1, cell2)
            else:
                selected = cell1 if cell1 else cell2
            
            merged.append(selected)
        
        return merged
    
    def validate_table_content(self, table: List) -> List:
        """표 내용 검증"""
        validated = []
        
        for row in table:
            validated_row = []
            for cell in row:
                # 오류 패턴 수정
                corrected_cell = self.apply_error_corrections(cell)
                validated_row.append(corrected_cell)
            validated.append(validated_row)
        
        # 합계 검증 등 추가 검증
        self.validate_table_sum(validated)
        
        return validated
    
    def apply_error_corrections(self, text: str) -> str:
        """오류 패턴 수정 적용"""
        # None이나 비문자열 처리
        if text is None:
            return ''
        if not isinstance(text, str):
            text = str(text)
            
        corrected = text
        
        # 회계 숫자 패턴 수정
        for pattern, replacement in self.error_patterns['accounting_numbers']:
            corrected = re.sub(pattern, replacement, corrected)
        
        # 특수문자 수정
        for pattern, replacement in self.error_patterns['special_chars']:
            corrected = re.sub(pattern, replacement, corrected)
        
        # 수정 이력 기록
        if corrected != text:
            self.correction_history.append({
                'original': text,
                'corrected': corrected,
                'timestamp': datetime.now().isoformat(),
                'type': 'auto_correction'
            })
        
        return corrected
    
    def validate_table_sum(self, table: List) -> bool:
        """표의 합계 검증"""
        # 구현 예정
        return True
    
    def validate_percentage(self, values: List[str]) -> bool:
        """백분율 합계 검증"""
        # 구현 예정
        return True
    
    def validate_balance(self, debit: float, credit: float) -> bool:
        """차변/대변 균형 검증"""
        # 구현 예정
        return abs(debit - credit) < 0.01
    
    def save_correction_history(self, output_path: Path):
        """수정 이력 저장"""
        history_path = output_path.parent / f"{output_path.stem}_corrections.json"
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(self.correction_history, f, ensure_ascii=False, indent=2)
    
    def process_page(self, pdf_path: Path, page_num: int, 
                     vision_json_path: Optional[Path] = None) -> Dict:
        """단일 페이지 처리"""
        # Text layer 추출
        text_data = self.extract_text_layer(pdf_path, page_num)
        
        # Vision API 결과 로드 (있는 경우)
        if vision_json_path and vision_json_path.exists():
            vision_data = self.load_vision_result(vision_json_path)
        else:
            # Vision API 결과가 없으면 text layer만 사용
            vision_data = text_data.copy()
            vision_data['method'] = 'vision_api'
        
        # 교차 검증
        validated = self.cross_validate(text_data, vision_data)
        
        # 결과 포맷팅
        result = {
            'page': page_num,
            'content': validated['content'],
            'tables': validated['tables'],
            'confidence': validated['confidence_scores'].get('overall', 0),
            'method': validated.get('method', 'unknown'),
            'corrections': len(self.correction_history),
            'warnings': validated.get('warnings', [])
        }
        
        return result

def main():
    """테스트 실행"""
    processor = EnhancedPDFProcessor()
    
    # 2024년 PDF 1페이지 테스트
    pdf_path = Path("_source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf")
    
    if pdf_path.exists():
        print("향상된 PDF 처리 테스트")
        print("=" * 50)
        
        result = processor.process_page(pdf_path, 1)
        
        print(f"페이지: {result['page']}")
        print(f"추출 방법: {result['method']}")
        print(f"신뢰도: {result['confidence']:.2%}")
        print(f"자동 수정: {result['corrections']}건")
        print(f"경고: {result['warnings']}")
        print("\n추출 내용 (처음 500자):")
        print(result['content'][:500])
        
        # 수정 이력 저장
        if processor.correction_history:
            processor.save_correction_history(Path("test_corrections.json"))
            print(f"\n수정 이력이 test_corrections.json에 저장되었습니다.")

if __name__ == "__main__":
    main()