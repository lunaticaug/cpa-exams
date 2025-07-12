"""
기능: 2024 원가회계 마크다운에서 정확한 구조 추출 및 사용자 스타일 템플릿 생성
입력: 변환된 마크다운 파일  
출력: 사용자가 원하는 스타일의 완성된 헤딩 구조 파일
"""

import re
from pathlib import Path
from collections import defaultdict


class AccurateStructureExtractor:
    def __init__(self, markdown_path):
        self.markdown_path = Path(markdown_path)
        self.content = self.markdown_path.read_text(encoding='utf-8')
        self.lines = self.content.split('\n')
        
    def extract_complete_structure(self):
        """전체 문서 구조를 정확히 추출"""
        structure = {
            "problems": defaultdict(lambda: {
                "points": 0,
                "materials": [],
                "questions": [],
                "tables": []
            })
        }
        
        current_problem = None
        current_material = None
        current_question = None
        in_textbox = False
        textbox_content = []
        table_content = []
        in_table = False
        
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            
            # 문제 감지
            if match := re.match(r'##\s*문제\s*(\d+)\s*\((\d+)점\)', line):
                current_problem = int(match.group(1))
                structure["problems"][current_problem]["points"] = int(match.group(2))
                current_material = None
                current_question = None
                
            # 자료 감지
            elif match := re.match(r'####\s*<자료\s*(\d*?)>', line):
                material_num = match.group(1) or "1"
                current_material = f"자료{material_num}"
                
                # 글상자 내용 수집 시작
                in_textbox = True
                textbox_content = []
                i += 1
                
                # 다음 표나 물음이 나올 때까지 글상자 내용 수집
                while i < len(self.lines) and not self.lines[i].startswith('|') and not re.match(r'###.*물음', self.lines[i]):
                    if self.lines[i].strip() and not self.lines[i].startswith('#'):
                        textbox_content.append(self.lines[i].strip())
                    i += 1
                
                if current_problem and textbox_content:
                    structure["problems"][current_problem]["materials"].append({
                        "name": current_material,
                        "textbox": ' '.join(textbox_content),
                        "tables": []
                    })
                i -= 1
                
            # 물음 감지
            elif match := re.match(r'###\s*\(물음\s*(\d+)\)', line):
                current_question = int(match.group(1))
                if current_problem:
                    structure["problems"][current_problem]["questions"].append({
                        "number": current_question,
                        "has_answer_format": False,
                        "tables": []
                    })
                    
            # 답안양식 감지
            elif '답안양식' in line:
                if current_problem and structure["problems"][current_problem]["questions"]:
                    structure["problems"][current_problem]["questions"][-1]["has_answer_format"] = True
                    
            # 테이블 감지
            elif line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    table_content = []
                table_content.append(line)
                
                # 다음 줄이 테이블이 아니면 테이블 종료
                if i + 1 >= len(self.lines) or not self.lines[i + 1].strip().startswith('|'):
                    in_table = False
                    if len(table_content) >= 2:  # 헤더 + 최소 1행
                        # 테이블 크기 계산
                        header = table_content[0]
                        cols = len([c for c in header.split('|') if c.strip()])
                        rows = len([r for r in table_content if r.strip() and not r.strip().startswith('| ---')])
                        
                        table_info = {
                            "rows": rows,
                            "cols": cols,
                            "content": table_content[:3]  # 샘플로 처음 3줄만
                        }
                        
                        # 현재 위치에 따라 테이블 할당
                        if current_problem:
                            if current_question and structure["problems"][current_problem]["questions"]:
                                # 물음에 속한 테이블
                                structure["problems"][current_problem]["questions"][-1]["tables"].append(table_info)
                            elif current_material and structure["problems"][current_problem]["materials"]:
                                # 자료에 속한 테이블
                                structure["problems"][current_problem]["materials"][-1]["tables"].append(table_info)
                            else:
                                # 문제 직속 테이블
                                structure["problems"][current_problem]["tables"].append(table_info)
                                
            i += 1
            
        return structure
    
    def generate_user_style_template(self, structure):
        """사용자 스타일에 맞춘 템플릿 생성"""
        lines = []
        lines.append("<!--")
        lines.append("Generated by: process-22-accurate-structure-extractor.py (v1.22)")
        lines.append("Description: 구조 템플릿 (완성본)")
        lines.append("Generated at: 2025-01-12")
        lines.append("-->")
        lines.append("")
        lines.append("# 2024년 2차 원가회계 기출문제 - 헤딩 구조")
        lines.append("")
        
        # 각 문제 처리
        for prob_num in sorted(structure["problems"].keys()):
            prob_data = structure["problems"][prob_num]
            
            lines.append(f"## 【문제 {prob_num}】 ({prob_data['points']}점)")
            lines.append("- type: text; 문제설명")
            lines.append("")
            
            # 자료들 처리
            for material in prob_data["materials"]:
                lines.append(f"### <{material['name']}>")
                lines.append("- type: 글상자")
                
                # 글상자 내용
                if material["textbox"]:
                    content_preview = material["textbox"][:150]
                    lines.append(f"- 글상자 내용: {content_preview}...")
                lines.append("")
                
                # 자료의 표들
                for idx, table in enumerate(material["tables"]):
                    material_num = re.search(r'자료(\d+)', material['name']).group(1)
                    lines.append(f"<!-- 문{prob_num}-자료{material_num}-표{idx+1} -->")
                    lines.append(f"크기: {table['rows']}×{table['cols']} 표")
                    
                    # 표 내용 미리보기
                    if table['content']:
                        lines.append("표 내용:")
                        for row in table['content'][:2]:
                            lines.append(f"  {row}")
                    lines.append("")
            
            # 물음들 소개
            if prob_data["questions"]:
                q_nums = [q["number"] for q in prob_data["questions"]]
                lines.append(f"**※ 자료를 이용하여 (물음 {min(q_nums)})∼(물음 {max(q_nums)})에 답하시오.**")
                lines.append("")
                
                # 각 물음 처리
                for question in prob_data["questions"]:
                    lines.append(f"#### (물음 {question['number']})")
                    lines.append("- 문제 내용")
                    
                    # 답안양식이 있는 경우
                    if question["has_answer_format"]:
                        lines.append("")
                        lines.append("**[답안양식]**")
                        
                        # 물음의 표들 (답안 표)
                        for idx, table in enumerate(question["tables"]):
                            lines.append(f"<!-- 문{prob_num}-물음{question['number']}-답안표{idx+1} -->")
                            lines.append(f"크기: {table['rows']}×{table['cols']} 표")
                            if table['content']:
                                lines.append("표 구조:")
                                for row in table['content'][:2]:
                                    lines.append(f"  {row}")
                    lines.append("")
                    
        return '\n'.join(lines)
    
    def save_template(self, output_path):
        """구조 추출 및 템플릿 저장"""
        print("구조 추출 중...")
        structure = self.extract_complete_structure()
        
        print("\n=== 추출된 구조 요약 ===")
        for prob_num, data in structure["problems"].items():
            print(f"문제 {prob_num} ({data['points']}점):")
            print(f"  - 자료: {len(data['materials'])}개")
            print(f"  - 물음: {len(data['questions'])}개")
            print(f"  - 직속 표: {len(data['tables'])}개")
            
        print("\n템플릿 생성 중...")
        template = self.generate_user_style_template(structure)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(template, encoding='utf-8')
        
        print(f"\n템플릿 저장 완료: {output_path}")


def main():
    # 경로 설정
    base_dir = Path(__file__).parent.parent.parent  # using-claudecode 디렉토리로 이동
    markdown_path = base_dir / "output/output_v1.23_pdf_to_markdown/2024_2차_원가회계_2-1+원가회계+문제(2024-2).md"
    
    if not markdown_path.exists():
        print(f"파일을 찾을 수 없습니다: {markdown_path}")
        return
        
    # 추출기 생성 및 실행
    extractor = AccurateStructureExtractor(markdown_path)
    
    # 템플릿 저장
    output_path = base_dir / "documentation/2024_원가회계_헤딩_구조_완성.md"
    extractor.save_template(output_path)


if __name__ == "__main__":
    main()