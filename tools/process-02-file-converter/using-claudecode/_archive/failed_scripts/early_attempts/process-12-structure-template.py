"""
기능: PDF 구조 템플릿 생성 및 매칭
입력: 문서 구조 템플릿
출력: 구조화된 추출 가이드
"""

import json
from pathlib import Path

def create_2024_structure_template():
    """2024년 원가회계 구조 템플릿 생성"""
    
    template = {
        "document": "2024년 2차 원가회계",
        "total_pages": 15,
        "structure": [
            {
                "page": 1,
                "page_header": "원가회계 2/16 1교시",
                "elements": [
                    {
                        "type": "problem",
                        "number": 1,
                        "points": 24,
                        "content": "【문제 1】(24점)",
                        "children": [
                            {
                                "type": "instruction",
                                "content": "※ <자료 1>을 이용하여 (물음 1)∼(물음 3)에 답하시오.",
                                "references": ["자료 1"]
                            },
                            {
                                "type": "context",
                                "content": "㈜한국은 두 개의 보조부문(수선부문, 식당부문)과 세 개의 제조부문(X부문, Y부문, Z부문)으로 구성되어 있다."
                            },
                            {
                                "type": "data",
                                "id": "자료 1",
                                "content": "<자료 1>",
                                "has_tables": True,
                                "table_count": 2,
                                "table_descriptions": [
                                    "사용부문별 예산/실제 용역의 양",
                                    "보조부문원가 정보"
                                ]
                            },
                            {
                                "type": "sub_question",
                                "number": 1,
                                "content": "(물음 1) 상호배분법을 적용하여 보조부문의 원가를 배분할 때, 각 제조부문에 배분되는 금액을 계산하시오.",
                                "answer_format": {
                                    "type": "table",
                                    "columns": ["부문", "금액"],
                                    "rows": ["X", "Y", "Z"]
                                }
                            },
                            {
                                "type": "sub_question",
                                "number": 2,
                                "content": "(물음 2) ㈜한국은 두 개의 보조부문(수선부문, 식당부문)을 폐쇄하고 외주업체를 통해 해당 용역을 공급받을지 여부를 검토하고 있다. 해당 의사결정에서 고려해야 하는 질적 판단기준을 3가지 서술하시오.",
                                "constraints": "3줄 이내로 답하시오."
                            },
                            {
                                "type": "sub_question",
                                "number": 3,
                                "content": "(물음 3) 보조부문 원가를 이중배분율(dual-rate)을 적용하여 제조부문에 배분할 때 발생할 수 있는 문제점을 2가지 서술하시오.",
                                "constraints": "2줄 이내로 답하시오."
                            }
                        ]
                    }
                ]
            },
            {
                "page": 2,
                "page_header": "원가회계 1교시 3/16",
                "elements": [
                    {
                        "type": "continuation",
                        "parent": "문제 1",
                        "children": [
                            {
                                "type": "context",
                                "content": "㈜한국은 실제개별원가계산을 적용하며, 개별법으로 재고자산을 평가한다."
                            },
                            {
                                "type": "data",
                                "id": "자료 2",
                                "content": "<자료 2>",
                                "has_tables": True,
                                "table_count": 2,
                                "table_descriptions": [
                                    "작업별 기계가동시간과 직접노무시간",
                                    "작업별 직접재료원가와 직접노무원가"
                                ]
                            },
                            {
                                "type": "instruction",
                                "content": "※ <자료 2>를 이용하여 (물음 4)∼(물음 6)에 답하시오.",
                                "references": ["자료 2"]
                            },
                            {
                                "type": "sub_question",
                                "number": 4,
                                "content": "(물음 4) 20x1년의 각 제조부문별 제조간접원가 배부율을 계산하시오.",
                                "answer_format": {
                                    "type": "table",
                                    "columns": ["부문", "배부율"],
                                    "rows": ["X", "Y", "Z"]
                                }
                            },
                            {
                                "type": "sub_question",
                                "number": 5,
                                "content": "(물음 5) 20x1년 말의 재공품, 제품, 매출원가 계정의 잔액을 각각 계산하시오.",
                                "answer_format": {
                                    "type": "list",
                                    "items": ["재공품", "제품", "매출원가"]
                                }
                            },
                            {
                                "type": "sub_question",
                                "number": 6,
                                "content": "(물음 6) 외부 전문가는 ㈜한국의 경영자에게 정상원가계산(평준화원가계산: normal costing)의 도입을 권유하고 있다.",
                                "constraints": "2줄 이내로 답하시오."
                            }
                        ]
                    }
                ]
            },
            {
                "page": 3,
                "page_header": "원가회계 4/16 1교시",
                "elements": [
                    {
                        "type": "continuation",
                        "parent": "문제 1",
                        "children": [
                            {
                                "type": "context",
                                "content": "※ ㈜한국이 당기(20x1년)에 정상개별원가계산을 적용했다고 가정하시오."
                            },
                            {
                                "type": "data",
                                "id": "자료 3",
                                "content": "<자료 3>",
                                "has_tables": True,
                                "table_descriptions": ["예산 제조간접원가 정보"]
                            },
                            {
                                "type": "instruction",
                                "content": "※ <자료 2>와 <자료 3>을 이용하여 (물음 7)∼(물음 9)에 답하시오.",
                                "references": ["자료 2", "자료 3"]
                            },
                            {
                                "type": "sub_question",
                                "number": 7,
                                "content": "(물음 7) 제조간접원가 배부차이 조정 전의 20x1년 말 재공품, 제품 및 매출원가 계정의 잔액을 각각 계산하시오."
                            },
                            {
                                "type": "sub_question",
                                "number": 8,
                                "content": "(물음 8) 20x1년 말 제조간접원가 배부차이 금액을 계산하고, 그 배부차이가 과대배부 또는 과소배부인지 밝히시오."
                            },
                            {
                                "type": "sub_question",
                                "number": 9,
                                "content": "(물음 9) ㈜한국은 제조간접원가 배부차이를 재공품, 제품 및 매출원가 기말잔액의 비율에 따라 조정한다."
                            }
                        ]
                    }
                ]
            },
            {
                "page": 4,
                "page_header": "원가회계 1교시 5/16",
                "elements": [
                    {
                        "type": "problem",
                        "number": 2,
                        "points": 28,
                        "content": "【문제 2】(28점)",
                        "children": [
                            {
                                "type": "context",
                                "content": "㈜한국은 실제원가를 이용하여 가중평균법에 입각한 종합원가계산을 적용하고 있다."
                            },
                            {
                                "type": "data",
                                "id": "자료",
                                "content": "<자료>",
                                "has_tables": True
                            },
                            {
                                "type": "instruction",
                                "content": "※ <자료>를 이용하여 (물음 1)∼(물음 6)에 답하시오."
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    return template

def save_template():
    """템플릿을 JSON 파일로 저장"""
    template = create_2024_structure_template()
    
    output_file = "structure-template-2024.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    
    print(f"구조 템플릿 저장 완료: {output_file}")
    
    # 간단한 요약 출력
    print("\n=== 구조 템플릿 요약 ===")
    print(f"문서: {template['document']}")
    print(f"총 페이지: {template['total_pages']}")
    
    for page_info in template['structure']:
        print(f"\n페이지 {page_info['page']}: {page_info['page_header']}")
        for element in page_info['elements']:
            if element['type'] == 'problem':
                print(f"  - {element['content']}")
                sub_count = sum(1 for child in element['children'] if child['type'] == 'sub_question')
                print(f"    하위 문제: {sub_count}개")
            elif element['type'] == 'continuation':
                print(f"  - {element['parent']} 계속")

def create_extraction_guide(template):
    """템플릿을 기반으로 추출 가이드 생성"""
    guide = {
        "extraction_steps": [
            {
                "step": 1,
                "description": "페이지별 텍스트 블록 추출",
                "method": "extract_words()로 위치 정보 포함 추출"
            },
            {
                "step": 2,
                "description": "구조 요소 매칭",
                "patterns": {
                    "problem": r"【문제\s*(\d+)】\s*\((\d+)점\)",
                    "sub_question": r"\(물음\s*(\d+)\)",
                    "data": r"<자료\s*(\d+)?>"
                }
            },
            {
                "step": 3,
                "description": "계층 구조 구성",
                "rules": [
                    "문제 하위에 물음 배치",
                    "자료는 참조하는 물음 앞에 배치",
                    "답안양식은 해당 물음 직후 배치"
                ]
            },
            {
                "step": 4,
                "description": "표 매핑",
                "rules": [
                    "답안양식 키워드 다음 표는 답안 템플릿",
                    "자료 내의 표는 데이터 테이블"
                ]
            }
        ]
    }
    
    return guide

if __name__ == "__main__":
    save_template()
    
    # 추출 가이드도 생성
    template = create_2024_structure_template()
    guide = create_extraction_guide(template)
    
    with open("extraction-guide.json", "w", encoding="utf-8") as f:
        json.dump(guide, f, ensure_ascii=False, indent=2)
    
    print("\n추출 가이드 저장 완료: extraction-guide.json")