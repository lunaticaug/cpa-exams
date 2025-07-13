"""
다중 검증 시스템
PDF Text Layer + Vision API 다중 실행으로 정확도 향상
"""

import json
import pdfplumber
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple
from collections import Counter
import difflib

class MultiValidationSystem:
    def __init__(self):
        self.confidence_threshold = 0.8
        self.known_corrections = {
            # 자주 발생하는 OCR 오류 패턴
            '직입노무원가': '직접노무원가',
            '직입재료원가': '직접재료원가',
            '공손 이루어': '공손에',
            '평작업이라는': '재작업에',
            '코스트': '대한'
        }
    
    def extract_from_pdf_text_layer(self, pdf_path: Path, page_num: int) -> Dict:
        """PDF Text Layer에서 텍스트와 숫자 추출"""
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num - 1]
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            
            # 숫자 추출 (천단위 구분자 포함)
            numbers = re.findall(r'[\d,]+(?:\.\d+)?', text)
            numbers = [n.replace(',', '') for n in numbers]
            
            # 핵심 용어 추출
            key_terms = re.findall(r'[가-힣]+원가|[가-힣]+부문|\d+단위|￦[\d,]+', text)
            
            return {
                'text': text,
                'numbers': numbers,
                'key_terms': key_terms,
                'tables': tables,
                'source': 'pdf_text_layer'
            }
    
    def load_vision_results(self, vision_files: List[Path]) -> List[Dict]:
        """여러 Vision API 결과 로드"""
        results = []
        
        for vision_file in vision_files:
            try:
                with open(vision_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    content = data.get('content', '')
                    
                    # 숫자 추출
                    numbers = re.findall(r'[\d,]+(?:\.\d+)?', content)
                    numbers = [n.replace(',', '') for n in numbers]
                    
                    # 핵심 용어 추출
                    key_terms = re.findall(r'[가-힣]+원가|[가-힣]+부문|\d+단위|￦[\d,]+', content)
                    
                    results.append({
                        'text': content,
                        'numbers': numbers,
                        'key_terms': key_terms,
                        'source': vision_file.name,
                        'raw_data': data
                    })
            except Exception as e:
                print(f"Vision 파일 로드 오류 {vision_file}: {e}")
        
        return results
    
    def validate_numbers(self, pdf_numbers: List[str], vision_results: List[Dict]) -> Dict:
        """숫자 검증 - 가장 빈번하게 나타나는 값 선택"""
        validation = {}
        
        # 모든 소스에서 숫자 수집
        all_number_sets = [set(pdf_numbers)]
        for vision in vision_results:
            all_number_sets.append(set(vision['numbers']))
        
        # 각 위치별로 가장 많이 나타나는 숫자 선택
        validated_numbers = []
        
        # 모든 고유 숫자 찾기
        all_unique_numbers = set()
        for num_set in all_number_sets:
            all_unique_numbers.update(num_set)
        
        for number in all_unique_numbers:
            # 각 숫자가 몇 개의 소스에서 나타나는지 계산
            count = sum(1 for num_set in all_number_sets if number in num_set)
            confidence = count / len(all_number_sets)
            
            if confidence >= 0.5:  # 과반수 이상에서 나타나면 신뢰
                validated_numbers.append({
                    'value': number,
                    'confidence': confidence,
                    'sources': count
                })
        
        return {
            'validated_numbers': validated_numbers,
            'total_sources': len(all_number_sets)
        }
    
    def validate_text_segments(self, pdf_text: str, vision_texts: List[str]) -> str:
        """텍스트 세그먼트 검증 - 라인별로 최적 선택"""
        # 모든 텍스트를 라인으로 분할
        pdf_lines = pdf_text.split('\n')
        vision_lines_sets = [text.split('\n') for text in vision_texts]
        
        validated_lines = []
        
        # 각 라인 위치별로 검증
        max_lines = max(len(pdf_lines), max(len(lines) for lines in vision_lines_sets))
        
        for i in range(max_lines):
            candidates = []
            
            # PDF 라인
            if i < len(pdf_lines):
                candidates.append(pdf_lines[i])
            
            # Vision 라인들
            for vision_lines in vision_lines_sets:
                if i < len(vision_lines):
                    candidates.append(vision_lines[i])
            
            # 가장 적절한 라인 선택
            best_line = self.select_best_line(candidates)
            validated_lines.append(best_line)
        
        return '\n'.join(validated_lines)
    
    def select_best_line(self, candidates: List[str]) -> str:
        """여러 후보 중 최적 라인 선택"""
        if not candidates:
            return ""
        
        # 알려진 오류 수정
        corrected_candidates = []
        for candidate in candidates:
            corrected = candidate
            for error, correction in self.known_corrections.items():
                corrected = corrected.replace(error, correction)
            corrected_candidates.append(corrected)
        
        # 가장 많이 나타나는 버전 선택
        counter = Counter(corrected_candidates)
        most_common = counter.most_common(1)[0][0]
        
        return most_common
    
    def detect_anomalies(self, validated_data: Dict) -> List[Dict]:
        """이상치 감지"""
        anomalies = []
        
        # 1. 비정상적으로 큰 숫자 감지
        numbers = validated_data.get('numbers', [])
        for num_data in numbers:
            try:
                value = float(num_data['value'])
                # 8,463 같은 이상한 숫자 감지
                if value > 10000 and value % 100 not in [0, 50]:
                    anomalies.append({
                        'type': 'suspicious_number',
                        'value': num_data['value'],
                        'confidence': num_data['confidence'],
                        'suggestion': '일반적이지 않은 숫자입니다. 확인이 필요합니다.'
                    })
            except:
                pass
        
        # 2. 의미불명 텍스트 감지
        text = validated_data.get('text', '')
        suspicious_patterns = [
            r'평작업이라는.*코스트',
            r'공손\s+이루어',
            r'직입[가-힣]+원가'
        ]
        
        for pattern in suspicious_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                anomalies.append({
                    'type': 'suspicious_text',
                    'value': match,
                    'suggestion': '문맥상 맞지 않는 텍스트입니다.'
                })
        
        return anomalies
    
    def multi_validate_page(self, pdf_path: Path, page_num: int, 
                          vision_files: List[Path]) -> Dict:
        """페이지 다중 검증"""
        print(f"\n페이지 {page_num} 다중 검증 시작...")
        
        # 1. PDF Text Layer 추출
        pdf_data = self.extract_from_pdf_text_layer(pdf_path, page_num)
        print(f"  PDF Text Layer: {len(pdf_data['numbers'])}개 숫자 추출")
        
        # 2. Vision API 결과들 로드
        vision_results = self.load_vision_results(vision_files)
        print(f"  Vision API: {len(vision_results)}개 버전 로드")
        
        # 3. 숫자 검증
        number_validation = self.validate_numbers(pdf_data['numbers'], vision_results)
        
        # 4. 텍스트 검증
        vision_texts = [v['text'] for v in vision_results]
        validated_text = self.validate_text_segments(pdf_data['text'], vision_texts)
        
        # 5. 최종 결과 조합
        result = {
            'page': page_num,
            'validated_text': validated_text,
            'validated_numbers': number_validation['validated_numbers'],
            'sources_used': number_validation['total_sources'],
            'confidence': self.calculate_overall_confidence(number_validation)
        }
        
        # 6. 이상치 감지
        anomalies = self.detect_anomalies({
            'text': validated_text,
            'numbers': number_validation['validated_numbers']
        })
        
        if anomalies:
            result['anomalies'] = anomalies
            print(f"  ⚠️  {len(anomalies)}개 이상치 감지")
        
        return result
    
    def calculate_overall_confidence(self, validation_data: Dict) -> float:
        """전체 신뢰도 계산"""
        if not validation_data['validated_numbers']:
            return 0.5
        
        confidences = [n['confidence'] for n in validation_data['validated_numbers']]
        return sum(confidences) / len(confidences)
    
    def generate_corrected_content(self, validation_result: Dict) -> str:
        """검증된 결과로 수정된 콘텐츠 생성"""
        content = validation_result['validated_text']
        
        # 이상치가 있으면 주석 추가
        if 'anomalies' in validation_result:
            content += "\n\n[검증 시 발견된 이상치]\n"
            for anomaly in validation_result['anomalies']:
                content += f"- {anomaly['type']}: {anomaly['value']}\n"
                content += f"  {anomaly['suggestion']}\n"
        
        return content

def demonstrate_multi_validation():
    """다중 검증 시연"""
    validator = MultiValidationSystem()
    
    # 2025년 1페이지 검증
    pdf_path = Path("_source/2025_2차_원가회계_2-1+원가관리회계+문제(2025-2).pdf")
    
    # Vision API 결과 파일들 (여러 버전이 있다고 가정)
    vision_files = [
        Path("__temp/2025/vision_output/page_001_추출_1.json"),
        # 추가 Vision 실행 결과가 있다면 여기에 추가
    ]
    
    if pdf_path.exists() and vision_files[0].exists():
        result = validator.multi_validate_page(pdf_path, 1, vision_files)
        
        print("\n" + "="*60)
        print("다중 검증 결과")
        print("="*60)
        
        print(f"\n전체 신뢰도: {result['confidence']:.2%}")
        print(f"사용된 소스: {result['sources_used']}개")
        
        # 검증된 숫자들
        print("\n[검증된 주요 숫자]")
        for num_data in result['validated_numbers'][:10]:
            print(f"  {num_data['value']} (신뢰도: {num_data['confidence']:.2%})")
        
        # 이상치
        if 'anomalies' in result:
            print("\n[감지된 이상치]")
            for anomaly in result['anomalies']:
                print(f"  - {anomaly['type']}: {anomaly['value']}")
                print(f"    → {anomaly['suggestion']}")
        
        # 수정된 콘텐츠 생성
        corrected = validator.generate_corrected_content(result)
        
        # 파일로 저장
        output_path = Path("multi_validated_output.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(corrected)
        
        print(f"\n수정된 결과가 {output_path}에 저장되었습니다.")
    else:
        print("필요한 파일이 없습니다.")

if __name__ == "__main__":
    demonstrate_multi_validation()