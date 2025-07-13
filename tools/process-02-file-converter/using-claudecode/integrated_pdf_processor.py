"""
통합 PDF 처리 시스템
Vision API + Text Layer 교차 검증 + 수정사항 학습을 통합한 완전한 시스템
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pdfplumber
import re

from enhanced_pdf_processor import EnhancedPDFProcessor
from correction_learning_system import CorrectionLearningSystem

class IntegratedPDFProcessor:
    def __init__(self):
        self.enhanced_processor = EnhancedPDFProcessor()
        self.learning_system = CorrectionLearningSystem()
        self.processing_stats = {
            'total_pages': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'auto_corrections': 0
        }
    
    def process_pdf_with_learning(self, pdf_path: Path, 
                                 output_path: Path,
                                 vision_dir: Optional[Path] = None) -> Dict:
        """학습 기능이 포함된 PDF 처리"""
        print(f"\n처리 중: {pdf_path.name}")
        print("=" * 60)
        
        results = {
            'file': pdf_path.name,
            'timestamp': datetime.now().isoformat(),
            'pages': [],
            'summary': {}
        }
        
        content_parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            
            for page_num in range(1, min(total_pages + 1, 16)):  # 최대 15페이지
                print(f"\r페이지 {page_num}/{min(total_pages, 15)} 처리 중...", end='')
                
                # Vision 파일 찾기
                vision_file = None
                if vision_dir and vision_dir.exists():
                    vision_files = list(vision_dir.glob(f"page_{page_num:03d}_*.json"))
                    if not vision_files:
                        vision_files = list(vision_dir.glob(f"page_*{page_num}_*.json"))
                    if vision_files:
                        vision_file = vision_files[0]
                
                # 페이지 처리
                page_result = self.enhanced_processor.process_page(
                    pdf_path, page_num, vision_file
                )
                
                # 학습된 수정사항 적용
                if page_result['content']:
                    corrected_content, applied = self.learning_system.apply_learned_corrections(
                        page_result['content']
                    )
                    
                    # 표 구조 개선
                    corrected_content = self.improve_table_structure(corrected_content)
                    
                    page_result['content'] = corrected_content
                    page_result['learned_corrections'] = len(applied)
                    self.processing_stats['auto_corrections'] += len(applied)
                
                # 통계 업데이트
                self.update_stats(page_result['confidence'])
                
                # 결과 저장
                results['pages'].append({
                    'page': page_num,
                    'confidence': page_result['confidence'],
                    'method': page_result['method'],
                    'corrections': page_result.get('corrections', 0) + 
                                  page_result.get('learned_corrections', 0)
                })
                
                # 콘텐츠 추가
                content_parts.append(f"[페이지 {page_num}]")
                content_parts.append(page_result['content'])
                
                # 메타데이터 추가 (신뢰도가 낮은 경우만)
                if page_result['confidence'] < 0.85:
                    content_parts.append(f"\n[extraction_confidence: {page_result['confidence']:.2%}]")
                
                content_parts.append("\n---\n")
        
        print()  # 줄바꿈
        
        # 최종 콘텐츠 생성
        final_content = '\n'.join(content_parts)
        
        # 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        # 요약 생성
        results['summary'] = self.generate_summary()
        
        # 처리 보고서 저장
        report_path = output_path.parent / f"{output_path.stem}_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return results
    
    def improve_table_structure(self, content: str) -> str:
        """표 구조 개선"""
        lines = content.split('\n')
        improved_lines = []
        in_table = False
        table_buffer = []
        
        for i, line in enumerate(lines):
            # 표 시작 감지
            if self.is_table_start(line, lines[i:i+3]):
                in_table = True
                table_buffer = [line]
            elif in_table:
                table_buffer.append(line)
                
                # 표 끝 감지
                if self.is_table_end(line, lines[i:i+2]):
                    # 표 처리
                    improved_table = self.process_table_buffer(table_buffer)
                    improved_lines.extend(improved_table)
                    in_table = False
                    table_buffer = []
            else:
                improved_lines.append(line)
        
        # 남은 표 처리
        if table_buffer:
            improved_table = self.process_table_buffer(table_buffer)
            improved_lines.extend(improved_table)
        
        return '\n'.join(improved_lines)
    
    def is_table_start(self, line: str, next_lines: List[str]) -> bool:
        """표 시작 여부 판단"""
        # 표 헤더 키워드
        header_keywords = [
            '사용부문', '제공부문', '구분', '부문', '항목',
            '연간 예산', '연간 실제', '[연간', '단위:'
        ]
        
        # 현재 라인이나 다음 라인에 표 헤더 키워드가 있는지
        all_lines = [line] + next_lines[:2]
        return any(keyword in line for line in all_lines for keyword in header_keywords)
    
    def is_table_end(self, line: str, next_lines: List[str]) -> bool:
        """표 끝 여부 판단"""
        # 빈 줄 다음에 표가 아닌 텍스트
        if not line.strip() and next_lines:
            next_line = next_lines[0] if next_lines else ''
            return not self.looks_like_table_row(next_line)
        
        # 표 끝 표시
        return line.strip() in ['', '</자료>', '※', '(물음']
    
    def looks_like_table_row(self, line: str) -> bool:
        """표 행처럼 보이는지 판단"""
        # 숫자가 여러 개 있음
        numbers = re.findall(r'\d+', line)
        if len(numbers) >= 2:
            return True
        
        # 파이프 구분자가 있음
        if '|' in line:
            return True
        
        # 탭이나 많은 공백으로 구분
        if '\t' in line or '  ' in line:
            return True
        
        return False
    
    def process_table_buffer(self, table_lines: List[str]) -> List[str]:
        """표 버퍼 처리"""
        if not table_lines:
            return []
        
        # 표 구조 분석
        processed = []
        
        # 표 제목이 있으면 유지
        if '[' in table_lines[0] and ']' in table_lines[0]:
            processed.append(table_lines[0])
            table_lines = table_lines[1:]
        
        # 열 개수 추정
        col_counts = []
        for line in table_lines:
            if line.strip():
                # 공백으로 구분된 항목 수
                items = re.split(r'\s{2,}|\t', line.strip())
                col_counts.append(len([item for item in items if item]))
        
        if col_counts:
            max_cols = max(col_counts)
            
            # 표 형식으로 변환
            processed.append('')  # 빈 줄
            
            for line in table_lines:
                if not line.strip():
                    continue
                
                # 라인을 항목으로 분할
                items = re.split(r'\s{2,}|\t', line.strip())
                items = [item for item in items if item]
                
                # 부족한 열 채우기
                while len(items) < max_cols:
                    items.append('')
                
                # 표 형식으로 변환
                if items:
                    processed.append('| ' + ' | '.join(items[:max_cols]) + ' |')
            
            processed.append('')  # 빈 줄
        else:
            # 표 구조를 파악할 수 없으면 원본 유지
            processed.extend(table_lines)
        
        return processed
    
    def update_stats(self, confidence: float):
        """통계 업데이트"""
        self.processing_stats['total_pages'] += 1
        
        if confidence >= 0.9:
            self.processing_stats['high_confidence'] += 1
        elif confidence >= 0.7:
            self.processing_stats['medium_confidence'] += 1
        else:
            self.processing_stats['low_confidence'] += 1
    
    def generate_summary(self) -> Dict:
        """처리 요약 생성"""
        total = self.processing_stats['total_pages']
        if total == 0:
            return {}
        
        return {
            'total_pages': total,
            'high_confidence_ratio': self.processing_stats['high_confidence'] / total,
            'medium_confidence_ratio': self.processing_stats['medium_confidence'] / total,
            'low_confidence_ratio': self.processing_stats['low_confidence'] / total,
            'auto_corrections_applied': self.processing_stats['auto_corrections'],
            'average_confidence': (
                self.processing_stats['high_confidence'] * 0.95 +
                self.processing_stats['medium_confidence'] * 0.8 +
                self.processing_stats['low_confidence'] * 0.5
            ) / total
        }
    
    def batch_process(self, file_list: List[Tuple[str, str]], output_dir: Path):
        """배치 처리"""
        output_dir.mkdir(exist_ok=True)
        
        print("\n" + "=" * 60)
        print("통합 PDF 처리 시스템 - 배치 처리")
        print("=" * 60)
        
        all_results = []
        
        for pdf_file, year in file_list:
            pdf_path = Path(pdf_file)
            if not pdf_path.exists():
                print(f"\n파일 없음: {pdf_path}")
                continue
            
            # Vision 디렉토리
            vision_dir = Path(f"__temp/{year}/vision_output")
            
            # 출력 파일명
            output_file = output_dir / f"{pdf_path.stem}_integrated.md"
            
            # 처리
            result = self.process_pdf_with_learning(
                pdf_path, output_file, vision_dir
            )
            all_results.append(result)
            
            # 요약 출력
            if 'summary' in result and result['summary']:
                summary = result['summary']
                print(f"\n완료: {pdf_path.name}")
                print(f"  - 평균 신뢰도: {summary.get('average_confidence', 0):.2%}")
                print(f"  - 자동 수정: {summary.get('auto_corrections_applied', 0)}건")
                print(f"  - 저장: {output_file}")
        
        # 전체 보고서 생성
        self.generate_batch_report(all_results, output_dir)
    
    def generate_batch_report(self, results: List[Dict], output_dir: Path):
        """배치 처리 보고서 생성"""
        report_path = output_dir / "batch_processing_report.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 통합 PDF 처리 보고서\n\n")
            f.write(f"처리 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 처리 결과 요약\n\n")
            f.write("| 파일명 | 페이지 수 | 평균 신뢰도 | 자동 수정 | 상태 |\n")
            f.write("|--------|-----------|------------|-----------|------|\n")
            
            for result in results:
                if 'summary' in result and result['summary']:
                    summary = result['summary']
                    status = "✅" if summary.get('average_confidence', 0) > 0.8 else "⚠️"
                    f.write(f"| {result['file']} | "
                           f"{summary.get('total_pages', 0)} | "
                           f"{summary.get('average_confidence', 0):.2%} | "
                           f"{summary.get('auto_corrections_applied', 0)} | "
                           f"{status} |\n")
            
            f.write("\n## 개선 제안\n\n")
            
            # 낮은 신뢰도 파일 목록
            low_confidence_files = [
                r for r in results 
                if r.get('summary', {}).get('average_confidence', 1) < 0.8
            ]
            
            if low_confidence_files:
                f.write("### 추가 검토가 필요한 파일\n\n")
                for file_result in low_confidence_files:
                    f.write(f"- {file_result['file']}: "
                           f"신뢰도 {file_result['summary']['average_confidence']:.2%}\n")
            
            f.write("\n### 권장사항\n\n")
            f.write("1. 신뢰도가 낮은 페이지는 수동 검토 필요\n")
            f.write("2. 표 구조가 복잡한 경우 Vision API 재실행 고려\n")
            f.write("3. 수정사항을 correction_learning_system에 학습시켜 정확도 향상\n")
        
        print(f"\n\n배치 처리 보고서 생성: {report_path}")

def main():
    """메인 실행"""
    processor = IntegratedPDFProcessor()
    
    # 처리할 파일 목록
    files_to_process = [
        ("_source/2022_2차_원가회계_(2022)2-1.+원가회계.pdf", "2022"),
        ("_source/2023_2차_원가회계_2-1+원가회계+문제(2023-2).pdf", "2023"),
        ("_source/2024_2차_원가회계_2-1+원가회계+문제(2024-2).pdf", "2024"),
        ("_source/2025_2차_원가회계_2-1+원가관리회계+문제(2025-2).pdf", "2025"),
    ]
    
    # 출력 디렉토리
    output_dir = Path("integrated_output")
    
    # 배치 처리 실행
    processor.batch_process(files_to_process, output_dir)

if __name__ == "__main__":
    main()