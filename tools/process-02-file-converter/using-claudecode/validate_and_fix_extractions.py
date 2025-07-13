"""
Vision API 결과 검증 및 수정 도구
PDF Text Layer와 Vision API 결과를 비교하여 오류를 찾고 수정합니다.
"""

import json
from pathlib import Path
from datetime import datetime
import pdfplumber
import re
from typing import Dict, List, Tuple
from enhanced_pdf_processor import EnhancedPDFProcessor

class ExtractionValidator:
    def __init__(self):
        self.processor = EnhancedPDFProcessor()
        self.validation_results = []
        self.corrections_made = []
        
    def find_numeric_discrepancies(self, text1: str, text2: str) -> List[Dict]:
        """두 텍스트 간 숫자 불일치 찾기"""
        discrepancies = []
        
        # 숫자 패턴 추출
        pattern = r'[\d,]+(?:\.\d+)?'
        numbers1 = re.findall(pattern, text1)
        numbers2 = re.findall(pattern, text2)
        
        # 위치별 비교
        lines1 = text1.split('\n')
        lines2 = text2.split('\n')
        
        for i, (line1, line2) in enumerate(zip(lines1, lines2)):
            nums1 = re.findall(pattern, line1)
            nums2 = re.findall(pattern, line2)
            
            if nums1 != nums2:
                discrepancies.append({
                    'line': i + 1,
                    'text_layer': line1.strip(),
                    'vision_api': line2.strip(),
                    'numbers_text': nums1,
                    'numbers_vision': nums2
                })
        
        return discrepancies
    
    def analyze_table_accuracy(self, text_tables: List, vision_tables: List) -> Dict:
        """표 데이터 정확도 분석"""
        analysis = {
            'total_cells': 0,
            'matching_cells': 0,
            'numeric_errors': [],
            'missing_data': []
        }
        
        for t_idx, (text_table, vision_table) in enumerate(zip(text_tables, vision_tables)):
            for r_idx, (text_row, vision_row) in enumerate(zip(text_table, vision_table)):
                for c_idx, (text_cell, vision_cell) in enumerate(zip(text_row, vision_row)):
                    analysis['total_cells'] += 1
                    
                    # 정규화
                    text_cell = str(text_cell).strip() if text_cell else ''
                    vision_cell = str(vision_cell).strip() if vision_cell else ''
                    
                    if text_cell == vision_cell:
                        analysis['matching_cells'] += 1
                    else:
                        # 숫자 오류 분석
                        if re.search(r'\d', text_cell) or re.search(r'\d', vision_cell):
                            analysis['numeric_errors'].append({
                                'table': t_idx,
                                'row': r_idx,
                                'col': c_idx,
                                'text_value': text_cell,
                                'vision_value': vision_cell
                            })
        
        if analysis['total_cells'] > 0:
            analysis['accuracy'] = analysis['matching_cells'] / analysis['total_cells']
        else:
            analysis['accuracy'] = 0
            
        return analysis
    
    def validate_file(self, pdf_path: Path, year: str) -> Dict:
        """단일 파일 검증"""
        print(f"\n검증 중: {pdf_path.name}")
        
        results = {
            'file': pdf_path.name,
            'year': year,
            'pages': []
        }
        
        # Vision output 경로 찾기
        vision_dir = Path(f"__temp/{year}/vision_output")
        if not vision_dir.exists():
            print(f"  Vision 결과 없음: {vision_dir}")
            return results
        
        # 각 페이지 검증
        vision_files = sorted(vision_dir.glob("page_*.json"))
        
        for vision_file in vision_files[:3]:  # 처음 3페이지만 테스트
            # 페이지 번호 추출
            page_match = re.search(r'page_(\d+)', vision_file.name)
            if not page_match:
                continue
                
            page_num = int(page_match.group(1))
            print(f"  페이지 {page_num} 검증 중...")
            
            # 처리
            result = self.processor.process_page(pdf_path, page_num, vision_file)
            
            # 상세 분석
            text_data = self.processor.extract_text_layer(pdf_path, page_num)
            vision_data = self.processor.load_vision_result(vision_file)
            
            # 불일치 찾기
            if text_data['text'] and vision_data['text']:
                discrepancies = self.find_numeric_discrepancies(
                    text_data['text'], 
                    vision_data['text']
                )
                
                # 표 정확도
                table_analysis = self.analyze_table_accuracy(
                    text_data['tables'],
                    vision_data['tables']
                )
                
                page_result = {
                    'page': page_num,
                    'confidence': result['confidence'],
                    'method': result['method'],
                    'discrepancies': len(discrepancies),
                    'table_accuracy': table_analysis['accuracy'],
                    'numeric_errors': len(table_analysis['numeric_errors']),
                    'sample_errors': discrepancies[:3]  # 처음 3개만
                }
                
                results['pages'].append(page_result)
                
                # 오류가 많으면 경고
                if len(discrepancies) > 5:
                    print(f"    ⚠️  {len(discrepancies)}개 불일치 발견")
                    for d in discrepancies[:3]:
                        print(f"      Line {d['line']}: {d['numbers_text']} vs {d['numbers_vision']}")
        
        return results
    
    def create_enhanced_extraction(self, pdf_path: Path, year: str, output_path: Path):
        """향상된 추출 결과 생성"""
        print(f"\n향상된 추출 생성: {pdf_path.name}")
        
        enhanced_content = []
        enhanced_content.append(f"# {Path(pdf_path).stem} - 향상된 추출\n")
        enhanced_content.append(f"생성일시: {datetime.now().isoformat()}\n")
        enhanced_content.append("추출 방법: Text Layer + Vision API 교차 검증\n\n")
        
        # Vision output 경로
        vision_dir = Path(f"__temp/{year}/vision_output")
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in range(1, min(len(pdf.pages) + 1, 16)):  # 최대 15페이지
                enhanced_content.append(f"## 페이지 {page_num}\n")
                
                # Vision 파일 찾기
                vision_file = vision_dir / f"page_{page_num:03d}_추출_1.json"
                if not vision_file.exists():
                    # 다른 패턴 시도
                    vision_files = list(vision_dir.glob(f"page_{page_num:03d}_*.json"))
                    if vision_files:
                        vision_file = vision_files[0]
                    else:
                        vision_file = None
                
                # 처리
                result = self.processor.process_page(pdf_path, page_num, vision_file)
                
                # 내용 추가
                content = result['content']
                if content:
                    enhanced_content.append(content)
                    enhanced_content.append("\n")
                    
                    # 메타데이터 추가
                    enhanced_content.append(f"\n[검증 정보]\n")
                    enhanced_content.append(f"- 추출 방법: {result['method']}\n")
                    enhanced_content.append(f"- 신뢰도: {result['confidence']:.2%}\n")
                    if result['corrections'] > 0:
                        enhanced_content.append(f"- 자동 수정: {result['corrections']}건\n")
                    if result['warnings']:
                        enhanced_content.append(f"- 경고: {', '.join(result['warnings'])}\n")
                
                enhanced_content.append("\n---\n\n")
        
        # 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(enhanced_content))
        
        print(f"  저장됨: {output_path}")
        
        # 수정 이력 저장
        if self.processor.correction_history:
            correction_path = output_path.parent / f"{output_path.stem}_corrections.json"
            self.processor.save_correction_history(correction_path)
            print(f"  수정 이력: {correction_path}")

def main():
    """메인 실행 함수"""
    validator = ExtractionValidator()
    
    # 검증할 파일들
    files_to_validate = [
        ("_source/2022_2차_원가회계_(2022)2-1.+원가회계.pdf", "2022"),
        ("_source/2023_2차_원가회계_2-1+원가회계+문제(2023-2).pdf", "2023"),
        ("_source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf", "2024"),
        ("_source/2025_2차_원가회계_2-1+원가관리회계+문제(2025-2).pdf", "2025"),
    ]
    
    print("=" * 60)
    print("Vision API 추출 결과 검증 및 향상")
    print("=" * 60)
    
    all_results = []
    
    # 1단계: 검증
    print("\n[1단계] 기존 추출 결과 검증")
    for pdf_file, year in files_to_validate:
        pdf_path = Path(pdf_file)
        if pdf_path.exists():
            result = validator.validate_file(pdf_path, year)
            all_results.append(result)
    
    # 2단계: 검증 보고서
    print("\n[2단계] 검증 보고서")
    print("-" * 60)
    
    for result in all_results:
        if result['pages']:
            print(f"\n{result['file']}:")
            total_discrepancies = sum(p['discrepancies'] for p in result['pages'])
            avg_confidence = sum(p['confidence'] for p in result['pages']) / len(result['pages'])
            avg_table_accuracy = sum(p['table_accuracy'] for p in result['pages']) / len(result['pages'])
            
            print(f"  평균 신뢰도: {avg_confidence:.2%}")
            print(f"  평균 표 정확도: {avg_table_accuracy:.2%}")
            print(f"  총 불일치: {total_discrepancies}개")
    
    # 3단계: 향상된 추출 생성
    print("\n[3단계] 향상된 추출 결과 생성")
    print("-" * 60)
    
    output_dir = Path("enhanced_output")
    output_dir.mkdir(exist_ok=True)
    
    for pdf_file, year in files_to_validate:
        pdf_path = Path(pdf_file)
        if pdf_path.exists():
            output_path = output_dir / f"{pdf_path.stem}_enhanced.md"
            validator.create_enhanced_extraction(pdf_path, year, output_path)
    
    # 검증 보고서 저장
    report_path = output_dir / "validation_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': all_results,
            'total_corrections': len(validator.processor.correction_history)
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n검증 보고서 저장: {report_path}")
    print("\n완료!")

if __name__ == "__main__":
    main()