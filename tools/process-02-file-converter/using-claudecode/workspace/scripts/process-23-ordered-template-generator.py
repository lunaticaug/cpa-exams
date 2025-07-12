"""
기능: 정확한 순서로 구조화된 템플릿 생성
입력: 변환된 마크다운 파일
출력: 올바른 순서의 헤딩 구조 템플릿
"""

import re
from pathlib import Path
from collections import OrderedDict


class OrderedTemplateGenerator:
    def __init__(self, markdown_path):
        self.markdown_path = Path(markdown_path)
        self.content = self.markdown_path.read_text(encoding='utf-8')
        
    def parse_document_structure(self):
        """문서를 순차적으로 파싱하여 올바른 구조 생성"""
        lines = self.content.split('\n')
        
        structure = OrderedDict()
        current_problem = None
        current_section = None
        current_material = None
        material_counter = {}
        question_set = {}  # 문제별 물음 저장 (중복 제거)
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 문제 감지
            if match := re.match(r'##\s*문제\s*(\d+)\s*\((\d+)점\)', line):
                current_problem = int(match.group(1))
                points = int(match.group(2))
                structure[current_problem] = {
                    'points': points,
                    'materials': OrderedDict(),
                    'questions': OrderedDict(),
                    'tables': []
                }
                material_counter[current_problem] = 0
                question_set[current_problem] = set()
                current_section = 'problem'
                
            # 자료 감지
            elif re.match(r'####\s*<자료', line):
                if current_problem:
                    material_counter[current_problem] += 1
                    current_material = material_counter[current_problem]
                    current_section = f'material_{current_material}'
                    
                    # 자료 내용 수집
                    material_content = []
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('|') and not re.match(r'###', lines[i]):
                        if lines[i].strip():
                            material_content.append(lines[i].strip())
                        i += 1
                    i -= 1
                    
                    structure[current_problem]['materials'][current_material] = {
                        'content': ' '.join(material_content),
                        'tables': []
                    }
                    
            # 물음 감지
            elif match := re.match(r'###\s*\(물음\s*(\d+)\)', line):
                if current_problem:
                    q_num = int(match.group(1))
                    current_section = f'question_{q_num}'
                    
                    # 중복 체크
                    if q_num not in question_set[current_problem]:
                        question_set[current_problem].add(q_num)
                        structure[current_problem]['questions'][q_num] = {
                            'content': '',
                            'answer_format': False,
                            'tables': []
                        }
                        
            # 답안양식 감지
            elif '답안양식' in line and current_problem:
                # 가장 최근 물음에 답안양식 표시
                if structure[current_problem]['questions']:
                    last_q = max(structure[current_problem]['questions'].keys())
                    structure[current_problem]['questions'][last_q]['answer_format'] = True
                    
            # 테이블 감지
            elif line.startswith('|'):
                table_lines = [line]
                i += 1
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                i -= 1
                
                if len(table_lines) >= 2:
                    # 테이블 크기 계산
                    header = table_lines[0]
                    cols = len([c for c in header.split('|') if c.strip()])
                    rows = len([r for r in table_lines if r and not r.startswith('| ---')])
                    
                    table_info = {
                        'rows': rows,
                        'cols': cols,
                        'sample': table_lines[:2]
                    }
                    
                    # 현재 섹션에 따라 테이블 할당
                    if current_problem:
                        if 'question_' in str(current_section):
                            q_num = int(current_section.split('_')[1])
                            if q_num in structure[current_problem]['questions']:
                                structure[current_problem]['questions'][q_num]['tables'].append(table_info)
                        elif 'material_' in str(current_section):
                            m_num = int(current_section.split('_')[1])
                            if m_num in structure[current_problem]['materials']:
                                structure[current_problem]['materials'][m_num]['tables'].append(table_info)
                        else:
                            structure[current_problem]['tables'].append(table_info)
                            
            i += 1
            
        return structure
    
    def generate_template(self, structure):
        """올바른 순서로 템플릿 생성"""
        lines = []
        lines.append("<!--")
        lines.append("Generated by: process-23-ordered-template-generator.py (v1.23)")
        lines.append("Description: 구조 템플릿 (정렬된 버전)")
        lines.append("Generated at: 2025-01-12")
        lines.append("-->")
        lines.append("")
        lines.append("# 2024년 2차 원가회계 기출문제 - 헤딩 구조")
        lines.append("")
        
        # 각 문제 처리
        for prob_num, prob_data in structure.items():
            lines.append(f"## 【문제 {prob_num}】 ({prob_data['points']}점)")
            lines.append("- type: text; 문제설명")
            lines.append("")
            
            # 자료 출력
            for mat_num, mat_data in prob_data['materials'].items():
                lines.append(f"### <자료 {mat_num}>")
                lines.append("- type: 글상자")
                if mat_data['content']:
                    content_preview = mat_data['content'][:150]
                    if len(mat_data['content']) > 150:
                        content_preview += "..."
                    lines.append(f"- 글상자 내용: {content_preview}")
                lines.append("")
                
                # 자료의 표들
                for idx, table in enumerate(mat_data['tables']):
                    lines.append(f"<!-- 문{prob_num}-자료{mat_num}-표{idx+1} -->")
                    lines.append(f"크기: {table['rows']}×{table['cols']} 표")
                    if idx == 0 and table['sample']:  # 첫 번째 표만 샘플 표시
                        lines.append("표 구조:")
                        for row in table['sample']:
                            lines.append(f"  {row}")
                    lines.append("")
            
            # 물음 범위 표시
            if prob_data['questions']:
                q_nums = sorted(prob_data['questions'].keys())
                if q_nums:
                    lines.append(f"**※ <자료>를 이용하여 (물음 {min(q_nums)})∼(물음 {max(q_nums)})에 답하시오.**")
                    lines.append("")
                
                # 각 물음 출력 (순서대로)
                for q_num in q_nums:
                    q_data = prob_data['questions'][q_num]
                    lines.append(f"#### (물음 {q_num})")
                    
                    # 답안양식이 있는 경우
                    if q_data['answer_format']:
                        lines.append("")
                        lines.append("**[답안양식]**")
                        
                        # 답안 표들
                        for idx, table in enumerate(q_data['tables']):
                            lines.append(f"<!-- 문{prob_num}-물음{q_num}-답안표{idx+1} -->")
                            lines.append(f"크기: {table['rows']}×{table['cols']} 표")
                            if idx == 0 and table['sample']:
                                lines.append("표 구조:")
                                for row in table['sample']:
                                    lines.append(f"  {row}")
                    lines.append("")
                    
        return '\n'.join(lines)
    
    def save_template(self, output_path):
        """템플릿 생성 및 저장"""
        print("문서 구조 파싱 중...")
        structure = self.parse_document_structure()
        
        print("\n=== 파싱 결과 ===")
        for prob_num, data in structure.items():
            print(f"문제 {prob_num} ({data['points']}점):")
            print(f"  - 자료: {list(data['materials'].keys())}")
            print(f"  - 물음: {sorted(data['questions'].keys())}")
            
        print("\n템플릿 생성 중...")
        template = self.generate_template(structure)
        
        output_path = Path(output_path)
        output_path.write_text(template, encoding='utf-8')
        
        print(f"\n템플릿 저장 완료: {output_path}")


def main():
    # 경로 설정
    base_dir = Path("/Users/user/GitHub/active/cpa-exams/tools/process-02-file-converter/using-claudecode")
    markdown_path = base_dir / "output/output_v1.23_pdf_to_markdown/2024_2차_원가회계_2-1+원가회계+문제(2024-2).md"
    
    if not markdown_path.exists():
        print(f"파일을 찾을 수 없습니다: {markdown_path}")
        return
        
    # 생성기 실행
    generator = OrderedTemplateGenerator(markdown_path)
    
    # 템플릿 저장
    output_path = base_dir / "documentation/2024_원가회계_헤딩_구조_완성_v2.md"
    generator.save_template(output_path)


if __name__ == "__main__":
    main()