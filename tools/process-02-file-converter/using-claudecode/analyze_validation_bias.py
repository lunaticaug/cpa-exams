"""
검증 시스템의 선입견 분석
왜 PDF(846)와 Vision(8,463)이 있는데도 올바른 값을 선택하지 못했는가?
"""

import re
from typing import List, Dict, Tuple

class ValidationBiasAnalyzer:
    def __init__(self):
        self.bias_patterns = []
    
    def analyze_number_validation_bias(self):
        """숫자 검증 시 발생하는 선입견 분석"""
        
        # 케이스 1: PDF와 Vision의 숫자 비교
        pdf_number = "846"
        vision_number = "8,463"
        
        print("="*60)
        print("검증 시스템의 선입견 분석")
        print("="*60)
        
        print(f"\nPDF Text Layer: {pdf_number}")
        print(f"Vision API: {vision_number}")
        
        # 문제 1: 더 큰 숫자를 선호하는 경향
        print("\n[선입견 1: 더 상세한 정보 선호]")
        print("- Vision API가 콤마까지 포함한 '8,463'을 제공")
        print("- PDF는 단순한 '846'")
        print("→ 시스템이 더 '정교해 보이는' Vision 결과를 신뢰")
        
        # 문제 2: Vision API에 대한 과도한 신뢰
        print("\n[선입견 2: Vision API 과신]")
        print("- 'Vision API가 더 최신 기술이니 정확할 것'이라는 가정")
        print("- PDF Text Layer를 '구식'으로 간주")
        print("→ 실제로는 PDF가 더 정확할 수 있음")
        
        # 문제 3: 숫자 형식에 대한 편견
        print("\n[선입견 3: 형식적 완성도 편향]")
        print("- '8,463' (천단위 구분자 포함) vs '846' (단순)")
        print("- 형식이 '완전해 보이는' 것을 선호")
        print("→ 단순한 형태가 오히려 정확할 수 있음")
        
        return self.correct_validation_approach()
    
    def correct_validation_approach(self):
        """올바른 검증 접근법"""
        print("\n" + "="*60)
        print("올바른 검증 접근법")
        print("="*60)
        
        approaches = {
            "1. 문맥 기반 검증": [
                "기초재공품: 3,600단위",
                "당기착수: 5,000단위", 
                "당기완성: 3,000단위",
                "기말재공품: ???",
                "",
                "물량 균형: 3,600 + 5,000 = 8,600",
                "감손 20%: 8,600 × 0.2 = 1,720",
                "예상 기말재공품: 8,600 - 3,000 - 1,720 = 3,880",
                "",
                "→ 846은 너무 작고, 8,463도 너무 큼",
                "→ 실제로는 다른 값일 가능성"
            ],
            
            "2. 크기 비율 검증": [
                "PDF: 846 (매우 작음)",
                "Vision: 8,463 (매우 큼)",
                "비율: 약 10배 차이",
                "",
                "→ 한쪽이 자릿수를 잘못 인식했을 가능성",
                "→ 846 → 8,460 또는 3,846 등 확인 필요"
            ],
            
            "3. OCR 오류 패턴 분석": [
                "Vision이 작은 숫자를 큰 숫자로 인식하는 경향",
                "콤마 삽입 오류 가능성",
                "PDF가 숫자를 누락하는 경향",
                "",
                "→ 양쪽 모두 의심하고 재확인 필요"
            ],
            
            "4. 중립적 투표 시스템": [
                "PDF도 Vision도 무조건 신뢰하지 않음",
                "숫자의 합리성을 먼저 검증",
                "문맥상 타당한 범위 내에서 선택",
                "",
                "→ 선입견 없이 데이터 기반 판단"
            ]
        }
        
        for title, points in approaches.items():
            print(f"\n{title}")
            for point in points:
                if point:
                    print(f"  {point}")
        
        return approaches
    
    def demonstrate_unbiased_validation(self):
        """선입견 없는 검증 시연"""
        print("\n" + "="*60)
        print("선입견 없는 검증 시연")
        print("="*60)
        
        # 실제 데이터
        context = {
            "기초재공품": 3600,
            "당기착수": 5000,
            "당기완성": 3000,
            "감손율": 0.2
        }
        
        # 후보 값들
        candidates = {
            "PDF": 846,
            "Vision": 8463,
            "PDF×10": 8460,
            "계산값": 3880  # 물량 균형으로 계산
        }
        
        print("\n[단계 1: 물량 균형 검증]")
        total_input = context["기초재공품"] + context["당기착수"]
        loss = total_input * context["감손율"]
        expected = total_input - context["당기완성"] - loss
        
        print(f"총 투입: {total_input}")
        print(f"감손: {loss}")
        print(f"당기완성: {context['당기완성']}")
        print(f"예상 기말재공품: {expected}")
        
        print("\n[단계 2: 후보 값 평가]")
        for name, value in candidates.items():
            diff = abs(value - expected)
            ratio = value / expected if expected > 0 else 0
            print(f"{name}: {value} (차이: {diff}, 비율: {ratio:.2f})")
        
        print("\n[단계 3: 최종 판단]")
        print("→ 계산값(3,880)이 가장 합리적")
        print("→ PDF(846)는 너무 작음 - 자릿수 누락 의심")
        print("→ Vision(8,463)은 너무 큼 - 잘못된 인식")
        print("→ 실제 값은 3,880 근처일 가능성 높음")

def main():
    analyzer = ValidationBiasAnalyzer()
    
    # 선입견 분석
    analyzer.analyze_number_validation_bias()
    
    # 올바른 검증 시연
    analyzer.demonstrate_unbiased_validation()
    
    print("\n" + "="*60)
    print("결론")
    print("="*60)
    print("\n검증 시스템이 실패한 이유:")
    print("1. Vision API 결과를 과도하게 신뢰")
    print("2. 형식적 완성도(콤마 포함)에 현혹")
    print("3. 문맥과 물량 균형을 고려하지 않음")
    print("4. PDF의 단순한 값을 무시")
    print("\n→ 기술적 우월성이 아닌 데이터의 합리성으로 판단해야 함!")

if __name__ == "__main__":
    main()