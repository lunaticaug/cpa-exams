"""
Vision API 다중 추출 및 검증 시스템
동일 페이지를 여러 번 추출하여 정확도 향상
"""

import json
import base64
from pathlib import Path
from typing import List, Dict, Optional
import os
from datetime import datetime
import time

class VisionMultipleExtractor:
    def __init__(self):
        self.extraction_prompts = [
            # 프롬프트 1: 정확성 중심
            """이미지에서 모든 텍스트를 정확하게 추출해주세요. 특히:
1. 숫자는 매우 정확하게 (천단위 구분자 포함)
2. 한글 용어는 정확하게 (직접노무원가, 제조간접원가 등)
3. 표는 마크다운 형식으로
4. 특수문자와 기호도 정확하게""",
            
            # 프롬프트 2: 표 구조 중심
            """이미지의 표를 중심으로 데이터를 추출해주세요:
1. 표의 구조를 정확히 파악
2. 각 셀의 데이터를 빠짐없이
3. 숫자 데이터는 특히 신중하게
4. 표 외부의 텍스트도 포함""",
            
            # 프롬프트 3: 검증 중심
            """이미지를 매우 신중하게 읽고 추출해주세요:
1. 숫자가 이상하게 보이면 다시 확인
2. '직접'이 '직입'으로 보이지 않도록 주의
3. 단위(단위, %, 원)를 정확히
4. 문맥상 이상한 부분은 재확인"""
        ]
    
    def extract_with_vision_api(self, image_path: Path, prompt: str) -> Dict:
        """Vision API로 이미지 추출 (실제 구현 시 API 호출)"""
        # 실제 구현에서는 여기서 Vision API를 호출합니다
        # 데모를 위해 시뮬레이션
        print(f"  Vision API 호출 시뮬레이션: {prompt[:50]}...")
        
        # 실제 구현 예시:
        # with open(image_path, 'rb') as f:
        #     image_data = base64.b64encode(f.read()).decode()
        # 
        # response = vision_api.analyze(
        #     image=image_data,
        #     prompt=prompt
        # )
        # return response
        
        # 데모: 기존 결과 반환
        return {
            'content': "시뮬레이션된 추출 결과",
            'confidence': 0.85
        }
    
    def multiple_extract(self, image_path: Path, num_extractions: int = 3) -> List[Dict]:
        """동일 이미지를 여러 번 추출"""
        results = []
        
        print(f"\n이미지 다중 추출 시작: {image_path.name}")
        
        for i in range(min(num_extractions, len(self.extraction_prompts))):
            print(f"\n추출 {i+1}/{num_extractions}")
            
            # 각각 다른 프롬프트로 추출
            prompt = self.extraction_prompts[i]
            result = self.extract_with_vision_api(image_path, prompt)
            
            results.append({
                'extraction_num': i + 1,
                'prompt_type': ['accuracy', 'structure', 'validation'][i],
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
            # API 제한을 위한 대기
            if i < num_extractions - 1:
                time.sleep(1)
        
        return results
    
    def compare_extractions(self, extractions: List[Dict]) -> Dict:
        """여러 추출 결과 비교 분석"""
        comparison = {
            'total_extractions': len(extractions),
            'variations': [],
            'consensus': {}
        }
        
        # 실제 구현에서는 더 복잡한 비교 로직
        # - 숫자 비교
        # - 텍스트 유사도
        # - 표 구조 일치도
        
        return comparison
    
    def save_multiple_results(self, page_num: int, results: List[Dict], 
                            output_dir: Path):
        """다중 추출 결과 저장"""
        output_dir.mkdir(exist_ok=True)
        
        for i, result in enumerate(results):
            filename = f"page_{page_num:03d}_추출_{i+1}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"  저장: {filename}")

class EnhancedMultiValidation:
    """PDF Text Layer + 다중 Vision API 결과를 통합한 검증"""
    
    def __init__(self):
        self.validation_rules = {
            # 회계 용어 검증
            'accounting_terms': [
                '직접재료원가', '직접노무원가', '제조간접원가',
                '기초재공품', '기말재공품', '당기투입원가'
            ],
            # 의심스러운 패턴
            'suspicious_patterns': {
                '직입': '직접',
                '제공품': '재공품',
                '평작업': '재작업'
            }
        }
    
    def validate_with_multiple_sources(self, pdf_text: str, 
                                     vision_results: List[Dict]) -> Dict:
        """다중 소스 검증"""
        
        # 1. 모든 소스에서 숫자 추출
        all_numbers = self.extract_all_numbers(pdf_text, vision_results)
        
        # 2. 투표 방식으로 신뢰할 숫자 결정
        validated_numbers = self.vote_on_numbers(all_numbers)
        
        # 3. 텍스트 검증
        validated_text = self.validate_text_content(pdf_text, vision_results)
        
        # 4. 신뢰도 계산
        confidence = self.calculate_multi_source_confidence(
            validated_numbers, validated_text
        )
        
        return {
            'validated_numbers': validated_numbers,
            'validated_text': validated_text,
            'confidence': confidence,
            'sources_count': 1 + len(vision_results)
        }
    
    def extract_all_numbers(self, pdf_text: str, 
                          vision_results: List[Dict]) -> Dict:
        """모든 소스에서 숫자 추출"""
        import re
        
        number_sources = {}
        
        # PDF에서 추출
        pdf_numbers = re.findall(r'[\d,]+(?:\.\d+)?', pdf_text)
        for num in pdf_numbers:
            clean_num = num.replace(',', '')
            if clean_num not in number_sources:
                number_sources[clean_num] = []
            number_sources[clean_num].append('pdf')
        
        # Vision 결과들에서 추출
        for i, vision in enumerate(vision_results):
            content = vision.get('result', {}).get('content', '')
            vision_numbers = re.findall(r'[\d,]+(?:\.\d+)?', content)
            
            for num in vision_numbers:
                clean_num = num.replace(',', '')
                if clean_num not in number_sources:
                    number_sources[clean_num] = []
                number_sources[clean_num].append(f'vision_{i+1}')
        
        return number_sources
    
    def vote_on_numbers(self, number_sources: Dict) -> List[Dict]:
        """투표 방식으로 신뢰할 숫자 결정"""
        validated = []
        
        for number, sources in number_sources.items():
            confidence = len(sources) / 4  # PDF + 3 Vision
            
            if confidence >= 0.5:  # 과반수 이상
                validated.append({
                    'value': number,
                    'confidence': confidence,
                    'sources': sources,
                    'consensus': len(sources) >= 3
                })
        
        return sorted(validated, key=lambda x: x['confidence'], reverse=True)
    
    def validate_text_content(self, pdf_text: str, 
                            vision_results: List[Dict]) -> str:
        """텍스트 내용 검증"""
        # 간단한 구현 - 실제로는 더 복잡한 로직 필요
        
        # 의심스러운 패턴 수정
        validated = pdf_text
        for wrong, correct in self.validation_rules['suspicious_patterns'].items():
            validated = validated.replace(wrong, correct)
        
        return validated
    
    def calculate_multi_source_confidence(self, numbers: List[Dict], 
                                        text: str) -> float:
        """다중 소스 기반 신뢰도 계산"""
        if not numbers:
            return 0.5
        
        # 숫자들의 평균 신뢰도
        num_confidence = sum(n['confidence'] for n in numbers) / len(numbers)
        
        # 회계 용어 존재 여부
        term_score = sum(1 for term in self.validation_rules['accounting_terms'] 
                        if term in text) / len(self.validation_rules['accounting_terms'])
        
        # 가중 평균
        return num_confidence * 0.7 + term_score * 0.3

def demonstrate_complete_system():
    """완전한 다중 검증 시스템 시연"""
    print("="*60)
    print("Vision API 다중 추출 및 검증 시스템")
    print("="*60)
    
    # 1단계: Vision API 다중 추출
    extractor = VisionMultipleExtractor()
    image_path = Path("workspace/vision_input/page_001.png")
    
    if image_path.exists():
        # 3번 추출
        vision_results = extractor.multiple_extract(image_path, 3)
        
        # 결과 저장
        output_dir = Path("multi_vision_output")
        extractor.save_multiple_results(1, vision_results, output_dir)
    else:
        print("이미지 파일이 없어 시뮬레이션 모드로 진행")
        vision_results = [
            {'result': {'content': '시뮬레이션 결과 1'}},
            {'result': {'content': '시뮬레이션 결과 2'}},
            {'result': {'content': '시뮬레이션 결과 3'}}
        ]
    
    # 2단계: 다중 소스 검증
    validator = EnhancedMultiValidation()
    
    # PDF 텍스트 (예시)
    pdf_text = """원가관리회계
    직입노무원가 143,420
    기말재공품 8,463단위"""
    
    validation_result = validator.validate_with_multiple_sources(
        pdf_text, vision_results
    )
    
    print("\n" + "="*60)
    print("최종 검증 결과")
    print("="*60)
    print(f"사용된 소스: {validation_result['sources_count']}개 (PDF + Vision x3)")
    print(f"전체 신뢰도: {validation_result['confidence']:.2%}")
    
    print("\n[합의된 숫자들]")
    for num in validation_result['validated_numbers'][:5]:
        consensus = "✓" if num['consensus'] else "?"
        print(f"  {consensus} {num['value']} - 신뢰도: {num['confidence']:.2%}")
    
    print("\n[텍스트 검증 결과]")
    if '직입' in pdf_text and '직접' in validation_result['validated_text']:
        print("  ✓ '직입노무원가' → '직접노무원가' 수정됨")
    
    print("\n이러한 방식으로 여러 소스를 교차 검증하면")
    print("OCR 오류를 크게 줄일 수 있습니다!")

if __name__ == "__main__":
    demonstrate_complete_system()