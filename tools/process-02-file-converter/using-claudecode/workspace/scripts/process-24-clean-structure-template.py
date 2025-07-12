"""
기능: 2024 원가회계 구조 템플릿 생성 (표는 마킹만)
입력: 변환된 마크다운 파일
출력: 깔끔한 구조 템플릿 with 표 마커
"""

import re
from pathlib import Path
from collections import OrderedDict


class CleanStructureTemplate:
    def __init__(self, markdown_path):
        self.markdown_path = Path(markdown_path)
        self.content = self.markdown_path.read_text(encoding='utf-8')
        self.pages = self.content.split('---\n\n## 페이지')
        
    def analyze_2024_structure(self):
        """2024년 원가회계 문서의 실제 구조 분석"""
        
        # 하드코딩된 정확한 구조 (PDF 분석 결과)
        structure = {
            1: {
                'points': 24,
                'title': '보조부문 원가배분과 개별원가계산',
                'materials': {
                    1: {
                        'title': '보조부문 원가배분 정책',
                        'content': '㈜한국은 두 개의 보조부문(수선부문, 식당부문)과 세 개의 제조부문(X부문, Y부문, Z부문)으로 구성. 이중배분율 적용.',
                        'tables': [
                            '부문별 예산/실제 용역량',
                            '보조부문 원가 정보'
                        ]
                    },
                    2: {
                        'title': '실제개별원가계산 정보',
                        'content': '㈜한국은 실제개별원가계산을 적용하며, 개별법으로 재고자산을 평가.',
                        'tables': [
                            '작업별 기계가동시간과 직접노무시간',
                            '작업별 직접재료원가와 직접노무원가',
                            '부문별 보조부문원가 배분 후 제조간접원가'
                        ]
                    },
                    3: {
                        'title': '정상개별원가계산 정보',
                        'content': '정상개별원가계산(평준화개별원가계산) 적용 가정.',
                        'tables': [
                            '예상 제조간접원가와 예상 배부기준'
                        ]
                    }
                },
                'questions': {
                    1: {'text': '상호배분법을 적용하여 보조부문의 원가를 배분할 때, 각 제조부문에 배분되는 금액을 계산', 'has_answer': True},
                    2: {'text': '보조부문을 폐쇄하고 외주업체를 통해 해당 용역을 공급받을지 여부 검토시 질적 판단기준 3가지', 'has_answer': False},
                    3: {'text': '보조부문 원가를 이중배분율 적용하여 제조부문에 배분할 때 발생할 수 있는 문제점 2가지', 'has_answer': False},
                    4: {'text': '각 제조부문별 실제 제조간접원가 배부율 계산', 'has_answer': True},
                    5: {'text': '재공품, 제품, 매출원가 잔액을 각각 계산', 'has_answer': True},
                    6: {'text': '정상원가계산 도입의 유용성 2가지를 의사결정 측면에서 설명', 'has_answer': False},
                    7: {'text': '예정배부율과 당기말 배부차이 계산', 'has_answer': True},
                    8: {'text': '배부차이를 작업별로 안분시 기초재공품 작업 #104의 배부차이', 'has_answer': True},
                    9: {'text': '각 제조부문에서 정상적으로 발생한다고 판단되는 유휴생산능력원가 계산', 'has_answer': True}
                }
            },
            2: {
                'points': 28,
                'title': '종합원가계산과 결합원가',
                'materials': {
                    1: {
                        'title': '3개 공정 종합원가계산',
                        'content': '㈜한국은 3개 공정을 거쳐 완성품 A, B, C를 생산. 가중평균법 적용.',
                        'tables': [
                            '공정별 생산 데이터',
                            '원가 정보',
                            '판매 정보'
                        ]
                    }
                },
                'questions': {
                    1: {'text': '제1공정 정상공손 인정점에서의 완성품환산량 계산', 'has_answer': True},
                    2: {'text': '제1공정 기말재공품원가와 완성품원가', 'has_answer': True},
                    3: {'text': '제1공정 생산원가보고서 작성', 'has_answer': True},
                    4: {'text': '제3공정 결합원가를 NRV법으로 배부', 'has_answer': True},
                    5: {'text': '완성품 A, B, C의 단위당 제조원가', 'has_answer': True},
                    6: {'text': '완성품별 매출총이익', 'has_answer': True},
                    7: {'text': '폐물 처리 관련 계산', 'has_answer': True},
                    8: {'text': '제품 배합 최적화', 'has_answer': True},
                    9: {'text': '배합 변경시 이익 증감 계산', 'has_answer': True}
                }
            },
            3: {
                'points': 24,
                'title': '예산편성과 표준원가계산',
                'materials': {
                    1: {
                        'title': '예산자료',
                        'content': '표준원가계산과 현금예산 관련 정보',
                        'tables': ['예산 데이터']
                    },
                    2: {
                        'title': '실제 생산자료',
                        'content': '공손을 감안한 실제 생산 정보',
                        'tables': ['실제 생산 데이터']
                    }
                },
                'questions': {
                    1: {'text': '예산 편성', 'has_answer': True},
                    2: {'text': '표준원가 차이분석', 'has_answer': True},
                    3: {'text': '공손 처리', 'has_answer': True},
                    4: {'text': '2차 검사 관련', 'has_answer': True}
                }
            },
            4: {
                'points': 16,
                'title': '품질원가',
                'materials': {
                    1: {
                        'title': '설비개선 전 데이터',
                        'content': '품질원가 정보',
                        'tables': ['품질원가 데이터']
                    },
                    2: {
                        'title': '설비개선 후 데이터',
                        'content': '개선 후 품질원가',
                        'tables': ['개선 후 데이터']
                    }
                },
                'questions': {
                    1: {'text': '품질원가보고서 작성', 'has_answer': True},
                    2: {'text': '품질원가 분석', 'has_answer': False},
                    3: {'text': '설비개선 효과', 'has_answer': True},
                    4: {'text': '품질원가 절감 방안', 'has_answer': False}
                }
            },
            5: {
                'points': 8,
                'title': '투자중심점 성과평가',
                'materials': {
                    1: {
                        'title': 'S사업부 성과 데이터',
                        'content': '투자중심점 성과평가 정보',
                        'tables': ['성과 데이터']
                    }
                },
                'questions': {
                    1: {'text': '투자수익률(ROI) 계산', 'has_answer': True},
                    2: {'text': '듀퐁분석', 'has_answer': True},
                    3: {'text': '잔여이익 계산', 'has_answer': True}
                }
            }
        }
        
        return structure
    
    def generate_clean_template(self):
        """깔끔한 구조 템플릿 생성"""
        structure = self.analyze_2024_structure()
        
        lines = []
        lines.append("<!--")
        lines.append("Generated by: process-24-clean-structure-template.py (v1.24)")
        lines.append("Description: 2024 원가회계 구조 템플릿 (표 마킹)")
        lines.append("Generated at: 2025-01-12")
        lines.append("-->")
        lines.append("")
        lines.append("# 2024년 2차 원가회계 기출문제 - 구조 템플릿")
        lines.append("")
        
        # 각 문제별 생성
        for prob_num, prob_data in structure.items():
            lines.append(f"## 【문제 {prob_num}】 ({prob_data['points']}점)")
            lines.append(f"주제: {prob_data['title']}")
            lines.append("")
            
            # 자료 섹션
            for mat_num, mat_data in prob_data['materials'].items():
                lines.append(f"### <자료 {mat_num}>")
                lines.append("- type: 글상자")
                lines.append(f"- 제목: {mat_data['title']}")
                lines.append(f"- 내용: {mat_data['content']}")
                lines.append("")
                
                # 표 마커
                for idx, table_desc in enumerate(mat_data['tables']):
                    lines.append(f"<!-- 문{prob_num}-자료{mat_num}-표{idx+1}: {table_desc} -->")
                lines.append("")
            
            # 물음 범위
            q_nums = list(prob_data['questions'].keys())
            if len(prob_data['materials']) > 0:
                lines.append(f"**※ <자료>를 이용하여 (물음 {min(q_nums)})∼(물음 {max(q_nums)})에 답하시오.**")
            else:
                lines.append(f"**※ (물음 {min(q_nums)})∼(물음 {max(q_nums)})에 답하시오.**")
            lines.append("")
            
            # 각 물음
            for q_num, q_data in prob_data['questions'].items():
                lines.append(f"#### (물음 {q_num})")
                lines.append(f"{q_data['text']}")
                
                if q_data['has_answer']:
                    lines.append("")
                    lines.append("**[답안양식]**")
                    lines.append(f"<!-- 문{prob_num}-물음{q_num}-답안표 -->")
                lines.append("")
        
        return '\n'.join(lines)
    
    def save_template(self, output_path):
        """템플릿 저장"""
        template = self.generate_clean_template()
        
        output_path = Path(output_path)
        output_path.write_text(template, encoding='utf-8')
        
        print(f"깔끔한 구조 템플릿 저장 완료: {output_path}")
        print("\n표 추출은 별도로 진행하세요:")
        print("- pdfplumber.extract_tables()")
        print("- tabula-py")
        print("- Vision API (Claude, GPT-4V)")


def main():
    base_dir = Path(__file__).parent.parent.parent  # using-claudecode 디렉토리로 이동
    markdown_path = base_dir / "output/output_v1.23_pdf_to_markdown/2024_2차_원가회계_2-1+원가회계+문제(2024-2).md"
    
    generator = CleanStructureTemplate(markdown_path)
    output_path = base_dir / "documentation/2024_원가회계_구조_템플릿_final.md"
    generator.save_template(output_path)


if __name__ == "__main__":
    main()