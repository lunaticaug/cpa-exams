"""
기능: 글상자와 일반 텍스트/표 구조물 식별
입력: 변환된 마크다운 파일
출력: 구조화된 문서 (글상자 마킹)
"""

import re
from pathlib import Path
from collections import OrderedDict


class TextBoxIdentifier:
    def __init__(self, markdown_path):
        self.markdown_path = Path(markdown_path)
        self.content = self.markdown_path.read_text(encoding='utf-8')
        self.lines = self.content.split('\n')
        
    def identify_document_elements(self):
        """문서 요소를 순차적으로 식별"""
        elements = []
        i = 0
        
        while i < len(self.lines):
            line = self.lines[i].strip()
            
            # 1. 문제 식별
            if match := re.match(r'##\s*문제\s*(\d+)\s*\((\d+)점\)', line):
                elements.append({
                    'type': 'problem',
                    'number': int(match.group(1)),
                    'points': int(match.group(2)),
                    'line': i
                })
                
            # 2. 자료 섹션 시작 (잠재적 글상자)
            elif re.match(r'####\s*<자료\s*\d*>', line):
                # 자료 다음의 텍스트 블록을 글상자로 간주
                textbox_content = []
                i += 1
                
                # 표나 다른 섹션이 나올 때까지 텍스트 수집
                while i < len(self.lines):
                    next_line = self.lines[i].strip()
                    
                    # 종료 조건
                    if (next_line.startswith('|') or      # 표 시작
                        next_line.startswith('#') or      # 새 섹션
                        next_line.startswith('**※') or    # 안내문
                        not next_line):                    # 빈 줄 2개 연속
                        break
                        
                    if next_line:  # 빈 줄이 아니면 추가
                        textbox_content.append(next_line)
                    i += 1
                
                if textbox_content:
                    elements.append({
                        'type': 'textbox',
                        'content': ' '.join(textbox_content),
                        'start_line': i - len(textbox_content),
                        'end_line': i - 1
                    })
                i -= 1
                
            # 3. 표 식별
            elif line.startswith('|'):
                table_lines = [line]
                i += 1
                
                while i < len(self.lines) and self.lines[i].strip().startswith('|'):
                    table_lines.append(self.lines[i].strip())
                    i += 1
                    
                elements.append({
                    'type': 'table',
                    'lines': table_lines,
                    'start_line': i - len(table_lines),
                    'end_line': i - 1
                })
                i -= 1
                
            # 4. 물음 식별
            elif match := re.match(r'###\s*\(물음\s*(\d+)\)', line):
                elements.append({
                    'type': 'question',
                    'number': int(match.group(1)),
                    'line': i
                })
                
            # 5. 답안양식 식별
            elif '답안양식' in line:
                elements.append({
                    'type': 'answer_format',
                    'line': i
                })
                
            # 6. 일반 텍스트
            elif line and not line.startswith('#'):
                # 독립적인 텍스트 (글상자 외부)
                elements.append({
                    'type': 'text',
                    'content': line,
                    'line': i
                })
                
            i += 1
            
        return elements
    
    def generate_structured_template(self, elements):
        """식별된 요소들로 구조화된 템플릿 생성"""
        lines = []
        lines.append("# 2024년 원가회계 - 구조 분석 (글상자 식별)")
        lines.append("")
        
        current_problem = None
        current_material = 0
        
        for elem in elements:
            if elem['type'] == 'problem':
                current_problem = elem['number']
                current_material = 0
                lines.append(f"\n## 【문제 {elem['number']}】 ({elem['points']}점)")
                
            elif elem['type'] == 'textbox':
                current_material += 1
                lines.append(f"\n### <자료 {current_material}> - 글상자")
                lines.append(f"내용: {elem['content'][:100]}...")
                lines.append(f"(줄 {elem['start_line']}-{elem['end_line']})")
                
            elif elem['type'] == 'table':
                cols = len([c for c in elem['lines'][0].split('|') if c.strip()])
                rows = len([l for l in elem['lines'] if not l.startswith('| ---')])
                lines.append(f"\n<!-- 표: {rows}×{cols} -->")
                lines.append(f"(줄 {elem['start_line']}-{elem['end_line']})")
                
            elif elem['type'] == 'question':
                lines.append(f"\n#### (물음 {elem['number']})")
                
            elif elem['type'] == 'answer_format':
                lines.append("**[답안양식]**")
                
            elif elem['type'] == 'text':
                # 중요한 텍스트만 표시
                if len(elem['content']) > 20:
                    lines.append(f"텍스트: {elem['content'][:50]}...")
                    
        return '\n'.join(lines)
    
    def analyze_patterns(self, elements):
        """패턴 분석 및 통계"""
        stats = {
            'problems': 0,
            'textboxes': 0,
            'tables': 0,
            'questions': 0
        }
        
        for elem in elements:
            if elem['type'] == 'problem':
                stats['problems'] += 1
            elif elem['type'] == 'textbox':
                stats['textboxes'] += 1
            elif elem['type'] == 'table':
                stats['tables'] += 1
            elif elem['type'] == 'question':
                stats['questions'] += 1
                
        return stats


def main():
    base_dir = Path("/Users/user/GitHub/active/cpa-exams/tools/process-02-file-converter/using-claudecode")
    markdown_path = base_dir / "output/output_v1.23_pdf_to_markdown/2024_2차_원가회계_2-1+원가회계+문제(2024-2).md"
    
    identifier = TextBoxIdentifier(markdown_path)
    
    print("문서 요소 식별 중...")
    elements = identifier.identify_document_elements()
    
    print("\n=== 식별 결과 ===")
    stats = identifier.analyze_patterns(elements)
    for key, value in stats.items():
        print(f"{key}: {value}개")
    
    # 구조화된 템플릿 생성
    template = identifier.generate_structured_template(elements)
    
    output_path = base_dir / "documentation/2024_textbox_analysis.md"
    output_path.write_text(template, encoding='utf-8')
    
    print(f"\n분석 결과 저장: {output_path}")


if __name__ == "__main__":
    main()