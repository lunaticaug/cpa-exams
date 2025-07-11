"""
기능: 변환된 마크다운에서 구조 정보 추출하여 사용자 스타일 템플릿 생성
입력: 변환된 마크다운 파일
출력: 사용자 스타일에 맞춘 상세 구조 템플릿
"""

import re
from pathlib import Path
import json


class MarkdownStructureAnalyzer:
    def __init__(self, markdown_path):
        self.markdown_path = Path(markdown_path)
        self.content = self.markdown_path.read_text(encoding='utf-8')
        self.structure = {
            "metadata": {
                "year": "2024",
                "subject": "원가회계", 
                "exam_type": "2차",
                "total_points": 100
            },
            "problems": []
        }
        
    def extract_text_boxes(self):
        """텍스트 박스(글상자) 내용 추출"""
        text_boxes = {}
        
        # 자료 섹션 찾기
        lines = self.content.split('\n')
        current_problem = None
        current_material = None
        box_content = []
        in_box = False
        
        for line in lines:
            # 문제 번호 감지
            problem_match = re.match(r'##\s*【문제\s*(\d+)】.*?\((\d+)점\)', line)
            if problem_match:
                current_problem = int(problem_match.group(1))
                if current_problem not in text_boxes:
                    text_boxes[current_problem] = {}
                    
            # 자료 섹션 감지
            material_match = re.match(r'###.*?<자료\s*(\d*?)>', line)
            if material_match:
                material_num = material_match.group(1) or "1"
                current_material = f"자료{material_num}"
                in_box = True
                box_content = []
                continue
                
            # 표 시작 감지 (글상자 끝)
            if line.strip().startswith('|') and in_box:
                if current_problem and current_material:
                    text_boxes[current_problem][current_material] = '\n'.join(box_content).strip()
                in_box = False
                box_content = []
                
            # 글상자 내용 수집
            if in_box and line.strip():
                box_content.append(line.strip())
                
        return text_boxes
    
    def analyze_tables(self):
        """마크다운 테이블 구조 분석"""
        tables = {}
        lines = self.content.split('\n')
        current_problem = None
        current_section = None
        table_counter = {}
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 문제 번호 감지
            problem_match = re.match(r'##\s*【문제\s*(\d+)】', line)
            if problem_match:
                current_problem = int(problem_match.group(1))
                table_counter[current_problem] = 0
                tables[current_problem] = []
                
            # 자료/물음 섹션 감지
            if re.match(r'###.*?<자료\s*\d*>', line):
                current_section = re.findall(r'자료\s*(\d*)', line)[0] or "1"
            elif re.match(r'###.*?\(물음\s*\d+\)', line):
                current_section = f"물음{re.findall(r'물음\s*(\d+)', line)[0]}"
                
            # 테이블 감지
            if line.strip().startswith('|') and i + 1 < len(lines) and lines[i + 1].strip().startswith('|'):
                # 테이블 시작
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i])
                    i += 1
                    
                if len(table_lines) >= 2:  # 헤더 + 구분선 최소 필요
                    # 행과 열 계산
                    header = table_lines[0]
                    cols = len([c for c in header.split('|') if c.strip()])
                    rows = len(table_lines) - 1  # 구분선 제외
                    
                    if current_problem:
                        table_counter[current_problem] += 1
                        tables[current_problem].append({
                            "section": current_section,
                            "number": table_counter[current_problem],
                            "rows": rows,
                            "cols": cols,
                            "content": table_lines
                        })
            i += 1
            
        return tables
    
    def generate_user_style_template(self):
        """사용자 스타일 템플릿 생성"""
        text_boxes = self.extract_text_boxes()
        tables = self.analyze_tables()
        
        print(f"발견된 텍스트 박스: {text_boxes}")
        print(f"발견된 테이블: {len(tables)} 문제")
        
        template_lines = []
        template_lines.append("<!--")
        template_lines.append("Generated by: process-21-markdown-structure-analyzer.py (v1.21)")
        template_lines.append("Description: 구조 템플릿 (완성본)")
        template_lines.append("Generated at: 2025-01-12")
        template_lines.append("-->")
        template_lines.append("")
        template_lines.append("# 2024년 2차 원가회계 기출문제 - 헤딩 구조")
        template_lines.append("")
        
        # 문제별 처리 - 문제 패턴 수정
        for prob_num in range(1, 6):  # 문제 1~5
            # 문제 찾기 - 패턴 수정
            prob_match = re.search(rf'##\s*문제\s*{prob_num}\s*\((\d+)점\)', self.content)
            if not prob_match:
                print(f"문제 {prob_num} 못 찾음")
                continue
                
            points = prob_match.group(1)
            template_lines.append(f"## 【문제 {prob_num}】 ({points}점)")
            template_lines.append("- type: text; 문제설명")
            template_lines.append("")
            
            # 해당 문제의 자료들
            if prob_num in text_boxes:
                for material_key, box_content in text_boxes[prob_num].items():
                    material_num = re.search(r'자료(\d*)', material_key).group(1) or "1"
                    template_lines.append(f"### <자료 {material_num}>")
                    template_lines.append("- type: 글상자")
                    template_lines.append(f"- 글상자 내용: {box_content[:100]}...")
                    template_lines.append("")
                    
                    # 해당 자료의 표들
                    if prob_num in tables:
                        material_tables = [t for t in tables[prob_num] if t['section'] == material_num]
                        for idx, table in enumerate(material_tables):
                            template_lines.append(f"<!-- 문{prob_num}-자료{material_num}-표{idx+1} -->")
                            template_lines.append(f"크기: {table['rows']}×{table['cols']} 표")
                            
                            # 표 내용 샘플 (첫 2행)
                            if table['content']:
                                template_lines.append("표 내용 샘플:")
                                for line in table['content'][:3]:
                                    template_lines.append(f"  {line}")
                            template_lines.append("")
            
            # 물음들 찾기
            questions = re.findall(rf'###.*?\(물음\s*(\d+)\)', self.content)
            if questions:
                # 중복 제거 및 정렬
                unique_questions = sorted(set(int(q) for q in questions))
                
                template_lines.append(f"**※ 자료를 이용하여 (물음 1)∼(물음 {len(unique_questions)})에 답하시오.**")
                template_lines.append("")
                
                for q_num in unique_questions:
                    template_lines.append(f"#### (물음 {q_num})")
                    
                    # 답안양식 찾기
                    if prob_num in tables:
                        answer_tables = [t for t in tables[prob_num] if t['section'] == f"물음{q_num}"]
                        if answer_tables:
                            template_lines.append("")
                            template_lines.append("**[답안양식]**")
                            for table in answer_tables:
                                template_lines.append(f"<!-- 문{prob_num}-물음{q_num}-답안표 -->")
                                template_lines.append(f"크기: {table['rows']}×{table['cols']} 표")
                    template_lines.append("")
        
        return "\n".join(template_lines)
    
    def save_template(self, output_path):
        """템플릿 저장"""
        template_content = self.generate_user_style_template()
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(template_content, encoding='utf-8')
        
        print(f"템플릿 저장 완료: {output_path}")


def main():
    # 마크다운 파일 경로
    base_dir = Path(__file__).parent.parent
    markdown_path = base_dir / "output/output_v1.23_pdf_to_markdown/2024_2차_원가회계_2-1+원가회계+문제(2024-2).md"
    
    if not markdown_path.exists():
        print(f"파일을 찾을 수 없습니다: {markdown_path}")
        return
    
    # 분석기 생성
    analyzer = MarkdownStructureAnalyzer(markdown_path)
    
    # 템플릿 생성 및 저장
    output_path = base_dir / "documentation/2024_원가회계_헤딩_구조_완성.md"
    analyzer.save_template(output_path)
    
    print("\n구조 분석 완료!")


if __name__ == "__main__":
    main()