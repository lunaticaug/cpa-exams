"""
기능: HWP 파일 변환 전략 및 테스트
입력: HWP 파일
출력: 변환 가능성 분석 및 최적 방법 제안
"""

import subprocess
import platform
from pathlib import Path
import json

class HWPConversionStrategy:
    def __init__(self):
        self.strategies = []
        self.os_type = platform.system()
        
    def check_method_1_libreoffice(self):
        """LibreOffice를 통한 변환 가능성 확인"""
        try:
            # LibreOffice 설치 확인
            result = subprocess.run(['soffice', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return {
                    "method": "LibreOffice",
                    "available": True,
                    "command": "soffice --headless --convert-to pdf",
                    "pros": ["무료", "명령줄 지원", "대량 변환 가능"],
                    "cons": ["HWP 지원이 완벽하지 않을 수 있음"],
                    "priority": 2
                }
        except:
            pass
        return {
            "method": "LibreOffice",
            "available": False,
            "install": "brew install --cask libreoffice (macOS)",
            "priority": 2
        }
    
    def check_method_2_hancom_office(self):
        """한컴오피스 설치 확인"""
        hancom_paths = [
            "/Applications/Hancom Office.app",
            "/Applications/HancomOffice.app",
            "/Applications/한컴오피스.app"
        ]
        
        for path in hancom_paths:
            if Path(path).exists():
                return {
                    "method": "Hancom Office",
                    "available": True,
                    "path": path,
                    "pros": ["HWP 네이티브 지원", "가장 정확한 변환"],
                    "cons": ["자동화 어려움", "수동 작업 필요"],
                    "priority": 1
                }
        
        return {
            "method": "Hancom Office",
            "available": False,
            "note": "한컴오피스가 설치되어 있다면 가장 정확한 변환 가능",
            "priority": 1
        }
    
    def check_method_3_online_api(self):
        """온라인 변환 API 사용 가능성"""
        return {
            "method": "Online API",
            "available": "conditional",
            "options": [
                "CloudConvert API",
                "ConvertAPI",
                "Zamzar API"
            ],
            "pros": ["자동화 가능", "다양한 포맷 지원"],
            "cons": ["API 키 필요", "파일 크기 제한", "보안 고려사항"],
            "priority": 3
        }
    
    def check_method_4_vision_api(self):
        """이미지 변환 후 Vision API 사용"""
        return {
            "method": "Vision API (Claude/GPT)",
            "available": True,
            "process": [
                "1. HWP → PDF 변환 (다른 방법 사용)",
                "2. PDF → 이미지 변환",
                "3. Vision API로 텍스트 추출 및 구조 분석"
            ],
            "pros": ["복잡한 레이아웃 정확히 인식", "표와 수식 처리 우수"],
            "cons": ["API 비용 발생", "처리 시간 소요"],
            "priority": 4
        }
    
    def recommend_hybrid_approach(self):
        """하이브리드 접근법 제안"""
        return {
            "recommended_approach": "Hybrid Strategy",
            "steps": [
                {
                    "step": 1,
                    "action": "PDF 파일 우선 처리",
                    "method": "pdfplumber + 표 영역은 Vision API",
                    "reason": "이미 PDF 버전이 있는 파일들은 직접 처리"
                },
                {
                    "step": 2,
                    "action": "HWP 전용 파일 식별",
                    "method": "2016년 이전 파일들 (HWP만 존재)",
                    "files": ["2003-2015년 파일들"]
                },
                {
                    "step": 3,
                    "action": "소량 수동 변환",
                    "method": "한컴오피스 또는 온라인 도구로 PDF 변환",
                    "reason": "13개 파일만 처리하면 됨"
                },
                {
                    "step": 4,
                    "action": "통합 Markdown 변환",
                    "method": "기존 PDF 변환 스크립트 활용",
                    "output": "연도별 정리된 Markdown 파일"
                }
            ]
        }
    
    def analyze_files(self):
        """소스 파일 분석"""
        source_dir = Path("source")
        
        hwp_files = list(source_dir.glob("*.hwp"))
        pdf_files = list(source_dir.glob("*.pdf"))
        
        # 연도별로 파일 존재 여부 확인
        years_analysis = {}
        
        for hwp in hwp_files:
            year = hwp.name.split('_')[0]
            if year not in years_analysis:
                years_analysis[year] = {"hwp": False, "pdf": False}
            years_analysis[year]["hwp"] = True
        
        for pdf in pdf_files:
            year = pdf.name.split('_')[0]
            if year not in years_analysis:
                years_analysis[year] = {"hwp": False, "pdf": False}
            years_analysis[year]["pdf"] = True
        
        # HWP만 있는 연도 찾기
        hwp_only_years = [year for year, info in years_analysis.items() 
                         if info["hwp"] and not info["pdf"]]
        
        return {
            "total_hwp": len(hwp_files),
            "total_pdf": len(pdf_files),
            "years_with_both": len([y for y, info in years_analysis.items() 
                                   if info["hwp"] and info["pdf"]]),
            "hwp_only_years": sorted(hwp_only_years),
            "hwp_only_count": len(hwp_only_years)
        }

def main():
    strategy = HWPConversionStrategy()
    
    print("=== HWP 파일 변환 전략 분석 ===\n")
    
    # 파일 분석
    file_analysis = strategy.analyze_files()
    print("【파일 현황】")
    print(f"- 전체 HWP 파일: {file_analysis['total_hwp']}개")
    print(f"- 전체 PDF 파일: {file_analysis['total_pdf']}개")
    print(f"- PDF 버전이 없는 HWP 파일: {file_analysis['hwp_only_count']}개")
    print(f"- 해당 연도: {', '.join(file_analysis['hwp_only_years'])}")
    
    print("\n【변환 방법 분석】")
    
    # 각 방법 확인
    methods = [
        strategy.check_method_1_libreoffice(),
        strategy.check_method_2_hancom_office(),
        strategy.check_method_3_online_api(),
        strategy.check_method_4_vision_api()
    ]
    
    for method in methods:
        print(f"\n{method['method']}:")
        print(f"  사용 가능: {method.get('available', 'Unknown')}")
        if 'pros' in method:
            print(f"  장점: {', '.join(method['pros'])}")
        if 'cons' in method:
            print(f"  단점: {', '.join(method['cons'])}")
    
    # 추천 전략
    print("\n【추천 전략】")
    hybrid = strategy.recommend_hybrid_approach()
    print(f"\n{hybrid['recommended_approach']}:")
    for step in hybrid['steps']:
        print(f"\nStep {step['step']}: {step['action']}")
        print(f"  방법: {step['method']}")
        if 'reason' in step:
            print(f"  이유: {step['reason']}")
    
    # 결과 저장
    result = {
        "file_analysis": file_analysis,
        "methods": methods,
        "recommendation": hybrid
    }
    
    with open("output-04-hwp-strategy.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n\n분석 완료! output-04-hwp-strategy.json에 저장되었습니다.")

if __name__ == "__main__":
    main()