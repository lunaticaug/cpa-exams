"""
수정사항 학습 시스템
사용자가 수정한 내용을 학습하여 향후 변환에 자동 적용합니다.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import difflib
from collections import defaultdict

class CorrectionLearningSystem:
    def __init__(self, corrections_db_path: str = "learned_corrections.json"):
        self.corrections_db_path = Path(corrections_db_path)
        self.corrections = self.load_corrections()
        self.patterns = self.extract_patterns()
        
    def load_corrections(self) -> Dict:
        """기존 수정사항 로드"""
        if self.corrections_db_path.exists():
            with open(self.corrections_db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'manual_corrections': [],
            'auto_patterns': [],
            'table_fixes': [],
            'context_rules': []
        }
    
    def save_corrections(self):
        """수정사항 저장"""
        with open(self.corrections_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.corrections, f, ensure_ascii=False, indent=2)
    
    def learn_from_diff(self, original_file: Path, corrected_file: Path):
        """원본과 수정본의 차이를 학습"""
        print(f"\n학습 중: {original_file.name} vs {corrected_file.name}")
        
        with open(original_file, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()
        
        with open(corrected_file, 'r', encoding='utf-8') as f:
            corrected_lines = f.readlines()
        
        # 차이점 분석
        differ = difflib.unified_diff(
            original_lines, 
            corrected_lines,
            fromfile=str(original_file),
            tofile=str(corrected_file),
            lineterm=''
        )
        
        corrections_found = []
        context_before = []
        
        for line in differ:
            if line.startswith('---') or line.startswith('+++'):
                continue
            elif line.startswith('@@'):
                # 새로운 변경 구간
                context_before = []
            elif line.startswith('-'):
                # 삭제된 라인 (원본)
                original_text = line[1:].strip()
                context_before.append(original_text)
            elif line.startswith('+'):
                # 추가된 라인 (수정본)
                corrected_text = line[1:].strip()
                
                if context_before:
                    original_text = context_before[-1]
                    
                    # 수정 패턴 분석
                    correction = self.analyze_correction(
                        original_text, 
                        corrected_text
                    )
                    
                    if correction:
                        corrections_found.append(correction)
                        print(f"  발견: {correction['type']} - {correction['description']}")
        
        # 학습한 수정사항 저장
        for correction in corrections_found:
            self.add_correction(correction)
        
        self.save_corrections()
        print(f"  총 {len(corrections_found)}개 패턴 학습 완료")
        
        return corrections_found
    
    def analyze_correction(self, original: str, corrected: str) -> Optional[Dict]:
        """수정 패턴 분석"""
        # 표 구조 수정
        if '|' in corrected and '|' not in original:
            return {
                'type': 'table_structure',
                'pattern': 'missing_pipe',
                'original': original,
                'corrected': corrected,
                'description': '표 구분자 추가',
                'context': self.extract_table_context(original, corrected)
            }
        
        # 숫자 형식 수정
        numbers_orig = re.findall(r'[\d,]+(?:\.\d+)?', original)
        numbers_corr = re.findall(r'[\d,]+(?:\.\d+)?', corrected)
        
        if numbers_orig != numbers_corr:
            return {
                'type': 'number_format',
                'pattern': 'number_correction',
                'original': original,
                'corrected': corrected,
                'description': f'숫자 수정: {numbers_orig} → {numbers_corr}',
                'number_changes': list(zip(numbers_orig, numbers_corr))
            }
        
        # 문자 혼동 수정
        char_mistakes = [
            ('O', '0'), ('0', 'O'),
            ('l', '1'), ('1', 'l'),
            ('I', '1'), ('1', 'I'),
        ]
        
        for orig_char, corr_char in char_mistakes:
            if orig_char in original and corr_char in corrected:
                orig_with_replacement = original.replace(orig_char, corr_char)
                if orig_with_replacement == corrected:
                    return {
                        'type': 'character_confusion',
                        'pattern': f'{orig_char}_to_{corr_char}',
                        'original': original,
                        'corrected': corrected,
                        'description': f'문자 혼동 수정: {orig_char} → {corr_char}'
                    }
        
        # 공백/정렬 수정
        if original.strip() == corrected.strip():
            return {
                'type': 'whitespace',
                'pattern': 'alignment',
                'original': original,
                'corrected': corrected,
                'description': '공백/정렬 수정'
            }
        
        # 기타 수정
        if original != corrected:
            return {
                'type': 'other',
                'pattern': 'general',
                'original': original,
                'corrected': corrected,
                'description': '일반 수정'
            }
        
        return None
    
    def extract_table_context(self, original: str, corrected: str) -> Dict:
        """표 관련 컨텍스트 추출"""
        # 표 헤더인지 확인
        is_header = any(keyword in original for keyword in 
                       ['구분', '부문', '항목', '단위', '계정'])
        
        # 숫자 데이터인지 확인
        has_numbers = bool(re.search(r'\d', original))
        
        # 열 개수 추정
        pipe_count = corrected.count('|')
        
        return {
            'is_header': is_header,
            'has_numbers': has_numbers,
            'column_count': pipe_count - 1 if pipe_count > 0 else 0
        }
    
    def add_correction(self, correction: Dict):
        """수정사항 추가"""
        correction['timestamp'] = datetime.now().isoformat()
        correction['frequency'] = 1
        
        # 중복 확인 및 빈도 업데이트
        for existing in self.corrections['manual_corrections']:
            if (existing['original'] == correction['original'] and 
                existing['corrected'] == correction['corrected']):
                existing['frequency'] += 1
                return
        
        self.corrections['manual_corrections'].append(correction)
        
        # 패턴 추출 및 저장
        if correction['type'] in ['table_structure', 'number_format']:
            self.extract_and_save_pattern(correction)
    
    def extract_and_save_pattern(self, correction: Dict):
        """수정사항에서 패턴 추출"""
        if correction['type'] == 'table_structure':
            # 표 구조 패턴
            pattern = {
                'type': 'table_reconstruction',
                'indicators': ['missing_pipe', 'broken_table'],
                'rules': [
                    {
                        'condition': 'consecutive_numbers_or_text',
                        'action': 'add_pipe_separators',
                        'example': correction
                    }
                ]
            }
            self.corrections['auto_patterns'].append(pattern)
        
        elif correction['type'] == 'number_format':
            # 숫자 형식 패턴
            for orig, corr in correction.get('number_changes', []):
                pattern = {
                    'type': 'number_correction',
                    'original_pattern': self.create_number_pattern(orig),
                    'correction_pattern': self.create_number_pattern(corr),
                    'example': {'original': orig, 'corrected': corr}
                }
                self.corrections['auto_patterns'].append(pattern)
    
    def create_number_pattern(self, number_str: str) -> str:
        """숫자 문자열에서 패턴 생성"""
        # 천단위 구분자 패턴
        if ',' in number_str:
            return r'\d{1,3}(,\d{3})+'
        # 소수점 패턴
        elif '.' in number_str:
            return r'\d+\.\d+'
        # 일반 숫자
        else:
            return r'\d+'
    
    def apply_learned_corrections(self, text: str) -> Tuple[str, List[Dict]]:
        """학습된 수정사항 적용"""
        corrected_text = text
        applied_corrections = []
        
        # 라인별 처리
        lines = corrected_text.split('\n')
        corrected_lines = []
        
        for line in lines:
            corrected_line = line
            
            # 1. 문자 혼동 수정
            for correction in self.corrections['manual_corrections']:
                if correction['type'] == 'character_confusion':
                    pattern = correction['pattern']
                    if '_to_' in pattern:
                        orig_char, corr_char = pattern.split('_to_')
                        if orig_char in corrected_line:
                            corrected_line = corrected_line.replace(orig_char, corr_char)
                            applied_corrections.append({
                                'type': 'character_confusion',
                                'original': line,
                                'corrected': corrected_line,
                                'rule': pattern
                            })
            
            # 2. 표 구조 복원
            if self.needs_table_reconstruction(corrected_line):
                reconstructed = self.reconstruct_table_line(corrected_line)
                if reconstructed != corrected_line:
                    applied_corrections.append({
                        'type': 'table_reconstruction',
                        'original': corrected_line,
                        'corrected': reconstructed,
                        'rule': 'auto_table_fix'
                    })
                    corrected_line = reconstructed
            
            corrected_lines.append(corrected_line)
        
        corrected_text = '\n'.join(corrected_lines)
        
        return corrected_text, applied_corrections
    
    def needs_table_reconstruction(self, line: str) -> bool:
        """표 재구성이 필요한지 판단"""
        # 표 관련 키워드
        table_keywords = ['구분', '부문', '제공부문', '사용부문', '단위']
        has_keyword = any(keyword in line for keyword in table_keywords)
        
        # 연속된 숫자나 텍스트
        has_multiple_values = len(re.findall(r'\S+', line)) > 3
        
        # 파이프가 없음
        no_pipes = '|' not in line
        
        return has_keyword or (has_multiple_values and no_pipes)
    
    def reconstruct_table_line(self, line: str) -> str:
        """표 라인 재구성"""
        # 공백으로 구분된 값들 추출
        values = re.split(r'\s{2,}', line.strip())
        
        if len(values) > 1:
            # 표 형식으로 재구성
            return '| ' + ' | '.join(values) + ' |'
        
        return line
    
    def extract_patterns(self) -> Dict:
        """저장된 수정사항에서 패턴 추출"""
        patterns = defaultdict(list)
        
        for correction in self.corrections['manual_corrections']:
            patterns[correction['type']].append({
                'pattern': correction.get('pattern'),
                'frequency': correction.get('frequency', 1)
            })
        
        return dict(patterns)
    
    def generate_report(self) -> str:
        """학습 결과 보고서 생성"""
        report = ["# 수정사항 학습 보고서\n"]
        report.append(f"생성일시: {datetime.now().isoformat()}\n")
        
        # 수정 유형별 통계
        type_stats = defaultdict(int)
        for correction in self.corrections['manual_corrections']:
            type_stats[correction['type']] += correction.get('frequency', 1)
        
        report.append("## 수정 유형별 통계\n")
        for correction_type, count in sorted(type_stats.items(), 
                                           key=lambda x: x[1], reverse=True):
            report.append(f"- {correction_type}: {count}건\n")
        
        # 주요 패턴
        report.append("\n## 주요 수정 패턴\n")
        for i, correction in enumerate(self.corrections['manual_corrections'][:10], 1):
            report.append(f"\n### {i}. {correction['description']}\n")
            report.append(f"- 유형: {correction['type']}\n")
            report.append(f"- 빈도: {correction.get('frequency', 1)}회\n")
            if 'original' in correction and 'corrected' in correction:
                report.append(f"- 원본: `{correction['original'][:50]}...`\n")
                report.append(f"- 수정: `{correction['corrected'][:50]}...`\n")
        
        # 자동 적용 가능 패턴
        report.append("\n## 자동 적용 가능 패턴\n")
        auto_applicable = sum(1 for c in self.corrections['manual_corrections'] 
                            if c['type'] in ['character_confusion', 'number_format'])
        report.append(f"총 {auto_applicable}개 패턴이 자동 적용 가능합니다.\n")
        
        return ''.join(report)

def main():
    """테스트 및 사용 예시"""
    learner = CorrectionLearningSystem()
    
    # 예시: 원본과 수정본 비교 학습
    original_file = Path("sample/cost-accounting-2024.md")
    corrected_file = Path("sample/cost-accounting-2024_corrected.md")  # 사용자가 수정한 버전
    
    if original_file.exists() and corrected_file.exists():
        corrections = learner.learn_from_diff(original_file, corrected_file)
        
        # 학습 결과 보고서
        report = learner.generate_report()
        with open("correction_learning_report.md", 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("\n학습 완료! correction_learning_report.md를 확인하세요.")
    else:
        print("학습할 파일이 없습니다.")
        print("\n사용법:")
        print("1. 원본 파일과 사용자가 수정한 파일을 준비")
        print("2. learner.learn_from_diff(원본_경로, 수정본_경로) 실행")
        print("3. 학습된 패턴은 자동으로 저장되어 향후 변환에 적용됨")

if __name__ == "__main__":
    main()