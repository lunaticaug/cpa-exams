"""
개선된 통합 PDF 처리 시스템
신뢰도 계산 개선 및 Vision API 경로 문제 해결
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pdfplumber
import re
import difflib

from enhanced_pdf_processor import EnhancedPDFProcessor
from correction_learning_system import CorrectionLearningSystem

class ImprovedIntegratedProcessor:
    def __init__(self):
        self.enhanced_processor = EnhancedPDFProcessor()
        self.learning_system = CorrectionLearningSystem()
        self.processing_stats = {
            'total_pages': 0,
            'confidence_scores': [],  # 실제 신뢰도 점수 저장
            'methods_used': {'text_layer_primary': 0, 'hybrid': 0, 'vision_primary': 0},
            'auto_corrections': 0
        }
    
    def find_vision_files(self, year: str, page_num: int) -> Optional[Path]:
        """다양한 경로에서 Vision API 결과 파일 찾기"""
        # 가능한 경로들
        possible_paths = [
            Path(f"__temp/{year}/vision_output"),
            Path(f"__temp/workspace/vision_output"),
            Path(f"workspace/vision_output"),
            Path("__temp"),  # 2024년은 직접 __temp에 있을 수 있음
        ]
        
        # 가능한 파일명 패턴들
        patterns = [
            f"page_{page_num:03d}_*.json",
            f"page_{page_num:02d}_*.json",
            f"page_{page_num}_*.json",
            f"*page_{page_num:03d}*.json",
            f"*_{year}_*page_{page_num}*.json"
        ]
        
        for base_path in possible_paths:
            if base_path.exists():
                for pattern in patterns:
                    files = list(base_path.glob(pattern))
                    if files:
                        # 가장 최신 파일 선택
                        return sorted(files, key=lambda x: x.stat().st_mtime)[-1]
        
        return None
    
    def calculate_dynamic_confidence(self, text_data: str, vision_data: str, 
                                   method: str, table_accuracy: float = 0) -> float:
        """동적 신뢰도 계산"""
        base_confidence = {
            'text_layer_primary': 0.9,
            'hybrid': 0.75,
            'vision_primary': 0.6
        }
        
        confidence = base_confidence.get(method, 0.5)
        
        # 텍스트 품질 평가
        if text_data:
            # 숫자 포함 여부
            if re.search(r'\d+', text_data):
                confidence += 0.05
            
            # 한글 텍스트 포함 여부
            if re.search(r'[가-힣]+', text_data):
                confidence += 0.05
            
            # 특수문자 일관성
            if text_data.count('￦') > 0 or text_data.count(',') > 3:
                confidence += 0.03
        
        # 표 정확도 반영
        if table_accuracy > 0:
            confidence = confidence * 0.7 + table_accuracy * 0.3
        
        # 최대값 제한
        return min(confidence, 0.98)
    
    def enhanced_text_normalize(self, text: str) -> str:
        """향상된 텍스트 정규화"""
        if not text:
            return ""
        
        # PDF 추출 시 발생하는 아티팩트 제거
        text = re.sub(r'\s*\n\s*', '\n', text)  # 불필요한 공백 제거
        text = re.sub(r'[ \t]+', ' ', text)     # 연속 공백을 하나로
        text = re.sub(r'\n{3,}', '\n\n', text)  # 과도한 줄바꿈 제거
        
        # 한글 특수문자 정규화
        replacements = {
            '（': '(', '）': ')',
            '［': '[', '］': ']',
            '｜': '|', '－': '-',
            '～': '~', '：': ':',
            '，': ',', '．': '.'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # 숫자 주변 공백 정규화
        text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # 숫자 사이 공백 제거
        text = re.sub(r'￦\s+(\d)', r'￦\1', text)    # 원화 기호 후 공백 제거
        
        return text.strip()
    
    def process_pdf_with_improvements(self, pdf_path: Path, 
                                    output_path: Path,
                                    year: str) -> Dict:
        """개선된 PDF 처리"""
        print(f"\n처리 중: {pdf_path.name}")
        print("=" * 60)
        
        results = {
            'file': pdf_path.name,
            'year': year,
            'timestamp': datetime.now().isoformat(),
            'pages': [],
            'detailed_stats': {}
        }
        
        content_parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = min(len(pdf.pages), 15)
            
            for page_num in range(1, total_pages + 1):
                print(f"\r페이지 {page_num}/{total_pages} 처리 중...", end='')
                
                # Vision 파일 찾기 (개선된 방식)
                vision_file = self.find_vision_files(year, page_num)
                
                if vision_file:
                    print(f"\n  Vision 파일 발견: {vision_file.name}")
                
                # 기존 처리기 수정 - Vision 파일이 없을 때의 처리 개선
                text_data = self.enhanced_processor.extract_text_layer(pdf_path, page_num)
                
                if vision_file and vision_file.exists():
                    vision_data = self.enhanced_processor.load_vision_result(vision_file)
                    
                    # 텍스트 정규화 적용
                    text_data['text'] = self.enhanced_text_normalize(text_data['text'])
                    vision_data['text'] = self.enhanced_text_normalize(vision_data['text'])
                    
                    # 교차 검증
                    validated = self.enhanced_processor.cross_validate(text_data, vision_data)
                    
                    # 동적 신뢰도 계산
                    table_accuracy = self.calculate_table_accuracy(
                        text_data.get('tables', []),
                        vision_data.get('tables', [])
                    )
                    
                    confidence = self.calculate_dynamic_confidence(
                        text_data['text'],
                        vision_data['text'],
                        validated.get('method', 'unknown'),
                        table_accuracy
                    )
                else:
                    # Vision API 없음 - Text Layer만 사용
                    validated = {
                        'content': text_data['text'],
                        'tables': text_data['tables'],
                        'method': 'text_only',
                        'confidence_scores': {'overall': 0.85},
                        'warnings': ['Vision API 결과 없음']
                    }
                    confidence = 0.85
                
                # 학습된 수정사항 적용
                if validated['content']:
                    corrected_content, applied = self.learning_system.apply_learned_corrections(
                        validated['content']
                    )
                    
                    # 표 구조 개선
                    corrected_content = self.improve_table_structure(corrected_content)
                    
                    validated['content'] = corrected_content
                    self.processing_stats['auto_corrections'] += len(applied)
                
                # 통계 업데이트
                self.processing_stats['total_pages'] += 1
                self.processing_stats['confidence_scores'].append(confidence)
                if 'method' in validated:
                    method = validated['method']
                    if method in self.processing_stats['methods_used']:
                        self.processing_stats['methods_used'][method] += 1
                
                # 결과 저장
                results['pages'].append({
                    'page': page_num,
                    'confidence': confidence,
                    'method': validated.get('method', 'unknown'),
                    'has_vision': vision_file is not None,
                    'warnings': validated.get('warnings', [])
                })
                
                # 콘텐츠 추가
                content_parts.append(f"[페이지 {page_num}]")
                content_parts.append(validated['content'])
                
                # 신뢰도 정보 추가
                if confidence < 0.85:
                    content_parts.append(f"\n[confidence: {confidence:.2%}]")
                    if validated.get('warnings'):
                        content_parts.append(f"[warnings: {', '.join(validated['warnings'])}]")
                
                content_parts.append("\n---\n")
        
        print()  # 줄바꿈
        
        # 최종 콘텐츠 생성
        final_content = '\n'.join(content_parts)
        
        # 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        # 상세 통계 생성
        results['detailed_stats'] = self.generate_detailed_stats()
        
        # 보고서 저장
        report_path = output_path.parent / f"{output_path.stem}_detailed_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return results
    
    def calculate_table_accuracy(self, text_tables: List, vision_tables: List) -> float:
        """표 정확도 계산"""
        if not text_tables and not vision_tables:
            return 0.0
        
        if not text_tables or not vision_tables:
            return 0.5
        
        total_cells = 0
        matching_cells = 0
        
        for t_table, v_table in zip(text_tables[:5], vision_tables[:5]):  # 처음 5개 표만
            for t_row, v_row in zip(t_table[:10], v_table[:10]):  # 각 표의 처음 10행만
                for t_cell, v_cell in zip(t_row, v_row):
                    total_cells += 1
                    
                    # 정규화 후 비교
                    t_cell = str(t_cell).strip() if t_cell else ''
                    v_cell = str(v_cell).strip() if v_cell else ''
                    
                    if t_cell == v_cell or (t_cell and v_cell and 
                                          difflib.SequenceMatcher(None, t_cell, v_cell).ratio() > 0.9):
                        matching_cells += 1
        
        return matching_cells / total_cells if total_cells > 0 else 0.0
    
    def improve_table_structure(self, content: str) -> str:
        """표 구조 개선 (기존 메서드 재사용)"""
        # 기존 integrated_pdf_processor의 메서드 사용
        lines = content.split('\n')
        improved_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 표 헤더 패턴 감지
            if any(keyword in line for keyword in ['사용부문', '제공부문', '구분', '[연간']):
                # 표 시작
                table_lines = [line]
                i += 1
                
                # 표 내용 수집
                while i < len(lines) and lines[i].strip():
                    if any(end in lines[i] for end in ['</자료>', '※', '(물음']):
                        break
                    table_lines.append(lines[i])
                    i += 1
                
                # 표 처리
                if len(table_lines) > 1:
                    processed_table = self.process_table_lines(table_lines)
                    improved_lines.extend(processed_table)
                else:
                    improved_lines.append(line)
            else:
                improved_lines.append(line)
                i += 1
        
        return '\n'.join(improved_lines)
    
    def process_table_lines(self, lines: List[str]) -> List[str]:
        """표 라인 처리"""
        processed = []
        
        # 표 제목 유지
        if '[' in lines[0] and ']' in lines[0]:
            processed.append(lines[0])
            processed.append('')
            lines = lines[1:]
        
        # 각 라인을 표 형식으로 변환
        for line in lines:
            if not line.strip():
                continue
            
            # 이미 표 형식이면 유지
            if '|' in line:
                processed.append(line)
            else:
                # 공백으로 구분된 값들을 표로 변환
                items = re.split(r'\s{2,}|\t', line.strip())
                items = [item for item in items if item]
                
                if items:
                    processed.append('| ' + ' | '.join(items) + ' |')
        
        if processed and not processed[0].startswith('['):
            processed.insert(0, '')
        processed.append('')
        
        return processed
    
    def generate_detailed_stats(self) -> Dict:
        """상세 통계 생성"""
        if not self.processing_stats['confidence_scores']:
            return {}
        
        scores = self.processing_stats['confidence_scores']
        
        return {
            'total_pages': self.processing_stats['total_pages'],
            'average_confidence': sum(scores) / len(scores),
            'min_confidence': min(scores),
            'max_confidence': max(scores),
            'confidence_distribution': {
                'high (>90%)': sum(1 for s in scores if s > 0.9),
                'medium (70-90%)': sum(1 for s in scores if 0.7 <= s <= 0.9),
                'low (<70%)': sum(1 for s in scores if s < 0.7)
            },
            'methods_used': self.processing_stats['methods_used'],
            'auto_corrections': self.processing_stats['auto_corrections']
        }
    
    def batch_process_improved(self, file_list: List[Tuple[str, str]], output_dir: Path):
        """개선된 배치 처리"""
        output_dir.mkdir(exist_ok=True)
        
        print("\n" + "=" * 60)
        print("개선된 통합 PDF 처리 시스템")
        print("=" * 60)
        
        all_results = []
        
        for pdf_file, year in file_list:
            pdf_path = Path(pdf_file)
            if not pdf_path.exists():
                print(f"\n파일 없음: {pdf_path}")
                continue
            
            # 통계 초기화
            self.processing_stats = {
                'total_pages': 0,
                'confidence_scores': [],
                'methods_used': {'text_layer_primary': 0, 'hybrid': 0, 'vision_primary': 0},
                'auto_corrections': 0
            }
            
            # 출력 파일명
            output_file = output_dir / f"{pdf_path.stem}_improved.md"
            
            # 처리
            result = self.process_pdf_with_improvements(
                pdf_path, output_file, year
            )
            all_results.append(result)
            
            # 요약 출력
            if 'detailed_stats' in result and result['detailed_stats']:
                stats = result['detailed_stats']
                print(f"\n완료: {pdf_path.name}")
                print(f"  - 평균 신뢰도: {stats.get('average_confidence', 0):.2%}")
                print(f"  - 최소/최대: {stats.get('min_confidence', 0):.2%} / {stats.get('max_confidence', 0):.2%}")
                print(f"  - 자동 수정: {stats.get('auto_corrections', 0)}건")
                print(f"  - 처리 방법: {stats.get('methods_used', {})}")
        
        # 전체 보고서 생성
        self.generate_improved_batch_report(all_results, output_dir)
    
    def generate_improved_batch_report(self, results: List[Dict], output_dir: Path):
        """개선된 배치 처리 보고서"""
        report_path = output_dir / "improved_batch_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 개선된 통합 PDF 처리 보고서\n\n")
            f.write(f"처리 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 처리 결과 상세\n\n")
            f.write("| 파일명 | 페이지 | 평균 신뢰도 | 최소-최대 | Vision 사용 | 상태 |\n")
            f.write("|--------|--------|------------|----------|------------|------|\n")
            
            for result in results:
                if 'detailed_stats' in result and result['detailed_stats']:
                    stats = result['detailed_stats']
                    avg_conf = stats.get('average_confidence', 0)
                    min_conf = stats.get('min_confidence', 0)
                    max_conf = stats.get('max_confidence', 0)
                    
                    # Vision 사용 페이지 수 계산
                    vision_pages = sum(1 for p in result['pages'] if p.get('has_vision', False))
                    total_pages = len(result['pages'])
                    
                    status = "✅" if avg_conf > 0.85 else "⚠️" if avg_conf > 0.7 else "❌"
                    
                    f.write(f"| {result['file'][:30]}... | "
                           f"{total_pages} | "
                           f"{avg_conf:.1%} | "
                           f"{min_conf:.1%}-{max_conf:.1%} | "
                           f"{vision_pages}/{total_pages} | "
                           f"{status} |\n")
            
            f.write("\n## 신뢰도 분포\n\n")
            
            total_high = sum(r['detailed_stats']['confidence_distribution']['high (>90%)'] 
                           for r in results if 'detailed_stats' in r)
            total_medium = sum(r['detailed_stats']['confidence_distribution']['medium (70-90%)'] 
                             for r in results if 'detailed_stats' in r)
            total_low = sum(r['detailed_stats']['confidence_distribution']['low (<70%)'] 
                          for r in results if 'detailed_stats' in r)
            total_all = total_high + total_medium + total_low
            
            if total_all > 0:
                f.write(f"- 높음 (90% 이상): {total_high}페이지 ({total_high/total_all:.1%})\n")
                f.write(f"- 중간 (70-90%): {total_medium}페이지 ({total_medium/total_all:.1%})\n")
                f.write(f"- 낮음 (70% 미만): {total_low}페이지 ({total_low/total_all:.1%})\n")
            
            f.write("\n## 권장사항\n\n")
            
            # Vision API 없는 파일 확인
            no_vision_files = []
            for r in results:
                vision_count = sum(1 for p in r['pages'] if p.get('has_vision', False))
                if vision_count == 0:
                    no_vision_files.append(r['file'])
            
            if no_vision_files:
                f.write("### Vision API 결과가 없는 파일\n")
                for file in no_vision_files:
                    f.write(f"- {file}\n")
                f.write("\n위 파일들은 Vision API 추출을 실행하면 신뢰도가 향상될 수 있습니다.\n")
            
            f.write("\n### 개선 결과\n")
            f.write("- 동적 신뢰도 계산으로 더 정확한 품질 평가\n")
            f.write("- Vision API 파일 경로 문제 해결\n")
            f.write("- 텍스트 정규화 개선으로 비교 정확도 향상\n")
        
        print(f"\n\n개선된 보고서 생성: {report_path}")

def main():
    """메인 실행"""
    processor = ImprovedIntegratedProcessor()
    
    # 처리할 파일 목록
    files_to_process = [
        ("_source/2022_2차_원가회계_(2022)2-1.+원가회계.pdf", "2022"),
        ("_source/2023_2차_원가회계_2-1+원가회계+문제(2023-2).pdf", "2023"),
        ("_source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf", "2024"),
        ("_source/2025_2차_원가회계_2-1+원가관리회계+문제(2025-2).pdf", "2025"),
    ]
    
    # 출력 디렉토리
    output_dir = Path("improved_output")
    
    # 배치 처리 실행
    processor.batch_process_improved(files_to_process, output_dir)

if __name__ == "__main__":
    main()