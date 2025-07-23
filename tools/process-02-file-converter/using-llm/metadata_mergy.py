#!/usr/bin/env python3
"""
메타데이터 JSON 조각을 과목별 통합 파일에 병합하는 도구 (Metadata Mergy!)

사용법:
1. metadata_fragment.json에 새로운 메타데이터 조각을 붙여넣기
2. 이 스크립트를 실행하여 과목 선택
3. 선택한 과목의 통합 JSON 파일에 자동 병합
"""

import json
import os
from typing import Dict, List

# ANSI 색상 코드
class Colors:
    YELLOW = '\033[93m'      # 세법
    CYAN = '\033[96m'        # 재무관리
    GREEN = '\033[92m'       # 회계감사
    MAGENTA = '\033[95m'     # 원가관리회계
    RED = '\033[91m'         # 재무회계
    GREEN_DARK = '\033[32m'  # 상법
    BLUE = '\033[94m'        # 경제학
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

# 과목 매핑
SUBJECTS = {
    '1': {
        'name': '세법',
        'file': 'metadata-gem-tax.json',
        'display': '세법 (Tax)',
        'color': Colors.YELLOW,
        'emoji': '🟡'
    },
    '2': {
        'name': '재무관리',
        'file': 'metadata-gem-finance-management.json',
        'display': '재무관리 (Finance Management)',
        'color': Colors.CYAN,
        'emoji': '🔵'
    },
    '3': {
        'name': '회계감사',
        'file': 'metadata-gem-audit.json',
        'display': '회계감사 (Audit)',
        'color': Colors.GREEN,
        'emoji': '🟢'
    },
    '4': {
        'name': '원가관리회계',
        'file': 'metadata-gem-cost-management.json',
        'display': '원가관리회계 (Cost Management)',
        'color': Colors.MAGENTA,
        'emoji': '🟣'
    },
    '5': {
        'name': '재무회계',
        'file': 'metadata-gem-accounting.json',
        'display': '재무회계 (Financial Accounting)',
        'color': Colors.RED,
        'emoji': '🔴'
    },
    '6': {
        'name': '상법',
        'file': 'metadata-gem-claw.json',
        'display': '상법 (Commercial Law)',
        'color': Colors.GREEN_DARK,
        'emoji': '🟩'
    },
    '7': {
        'name': '경제학',
        'file': 'metadata-gem-economics.json',
        'display': '경제학 (Economics)',
        'color': Colors.BLUE,
        'emoji': '🔷'
    }
}

def load_json_file(filepath: str) -> Dict:
    """JSON 파일 로드"""
    if not os.path.exists(filepath):
        return {"metadata_log": []}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(filepath: str, data: Dict):
    """JSON 파일 저장"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def validate_metadata(metadata: List[Dict]) -> tuple[bool, str]:
    """메타데이터 유효성 검증 (필수 항목만 검증)"""
    if not metadata:
        return False, "메타데이터가 비어있습니다."
    
    required_fields = ['question_id', 'tags']
    
    for idx, item in enumerate(metadata):
        for field in required_fields:
            if field not in item:
                return False, f"항목 {idx+1}에 필수 필드 '{field}'가 없습니다."
        
        if not isinstance(item['tags'], list):
            return False, f"항목 {idx+1}의 tags가 리스트가 아닙니다."
    
    # difficulty는 검증하지 않음 (있어도 되고 없어도 되고, 어떤 값이든 OK)
    
    return True, "유효성 검증 통과"

def detect_subject_from_ids(metadata: List[Dict]) -> str:
    """question_id 패턴으로 과목 자동 탐지"""
    if not metadata:
        return None
    
    # 첫 번째 question_id로 판단
    first_id = metadata[0].get('question_id', '').lower()
    
    # 패턴 매칭
    subject_patterns = {
        'tax': '1',
        'finance-management': '2',
        'finance-mgmt': '2',
        'audit': '3',
        'cost-management': '4',
        'cost-mgmt': '4',
        'accounting': '5',
        'claw': '6',
        'commercial-law': '6',
        'economics': '7',
        'econ': '7'
    }
    
    for pattern, subject_num in subject_patterns.items():
        if pattern in first_id:
            return subject_num
    
    return None

def merge_metadata(fragment_file: str, subject_choice: str):
    """메타데이터 병합 메인 함수"""
    # 조각 파일 로드
    fragment_data = load_json_file(fragment_file)
    
    if not fragment_data.get('metadata_log'):
        print("❌ metadata_fragment.json에 병합할 데이터가 없습니다.")
        return
    
    # 유효성 검증
    is_valid, message = validate_metadata(fragment_data['metadata_log'])
    if not is_valid:
        print(f"❌ 유효성 검증 실패: {message}")
        return
    
    # 대상 파일 경로
    subject_info = SUBJECTS[subject_choice]
    target_file = subject_info['file']
    
    # 기존 데이터 로드
    target_data = load_json_file(target_file)
    
    # 병합 전 통계
    before_count = len(target_data['metadata_log'])
    
    # 중복 제거를 위한 기존 ID 수집
    existing_ids = {item['question_id'] for item in target_data['metadata_log']}
    
    # 새 항목 추가 (중복 제외)
    added_count = 0
    duplicate_ids = []
    
    for item in fragment_data['metadata_log']:
        if item['question_id'] not in existing_ids:
            target_data['metadata_log'].append(item)
            added_count += 1
        else:
            duplicate_ids.append(item['question_id'])
    
    # 저장
    save_json_file(target_file, target_data)
    
    # 결과 출력
    color = subject_info['color']
    print(f"\n{Colors.BOLD}✅ 병합 완료!{Colors.RESET}")
    print(f"📊 과목: {color}{Colors.BOLD}{subject_info['display']}{Colors.RESET}")
    print(f"📄 파일: {target_file}")
    print(f"🔢 기존 항목: {before_count}개")
    print(f"➕ 새로 추가: {Colors.BOLD}{color}{added_count}개{Colors.RESET}")
    print(f"🔄 중복 제외: {len(duplicate_ids)}개")
    if duplicate_ids:
        print(f"   중복 ID: {', '.join(duplicate_ids[:5])}{' ...' if len(duplicate_ids) > 5 else ''}")
    print(f"📝 총 항목: {Colors.BOLD}{len(target_data['metadata_log'])}개{Colors.RESET}")
    
    # fragment 파일 초기화
    save_json_file(fragment_file, {"metadata_log": []})
    print(f"\n🧹 metadata_fragment.json 파일이 초기화되었습니다.")

def main():
    """메인 실행 함수"""
    print("=== CPA 시험 메타데이터 병합 도구 (Metadata Mergy!) ===\n")
    
    fragment_file = "metadata_fragment.json"
    
    # fragment 파일 확인
    if not os.path.exists(fragment_file):
        print(f"❌ {fragment_file} 파일이 없습니다.")
        return
    
    # 조각 파일 로드하여 과목 자동 탐지 시도
    fragment_data = load_json_file(fragment_file)
    detected_subject = None
    
    if fragment_data.get('metadata_log'):
        detected_subject = detect_subject_from_ids(fragment_data['metadata_log'])
        
        if detected_subject:
            subject_info = SUBJECTS[detected_subject]
            color = subject_info['color']
            
            # 자동 탐지된 과목을 크고 굵게 표시
            print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
            print(f"🔍 {Colors.BOLD}{color}과목 자동 탐지: {subject_info['display']}{Colors.RESET}")
            print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
            
            print("\n다른 과목을 선택하려면 번호를 입력하세요:")
            for key, subject in SUBJECTS.items():
                if key == detected_subject:
                    # 탐지된 과목은 하이라이트
                    print(f"  {subject['emoji']} {Colors.BOLD}{key}. {subject['display']}{Colors.RESET} ✓")
                else:
                    print(f"  {subject['emoji']} {key}. {subject['display']}")
            
            confirm = input("\n확인: Enter (자동 탐지 승인) 또는 과목 번호 (1-7): ").strip()
            
            # 숫자를 입력한 경우
            if confirm in SUBJECTS:
                detected_subject = confirm
            # 빈 입력(Enter)이 아닌 다른 입력
            elif confirm != '':
                print("❌ 잘못된 입력입니다.")
                return
    
    # 자동 탐지 실패하거나 사용자가 거부한 경우 수동 선택
    if not detected_subject:
        print("\n병합할 과목을 선택하세요:")
        for key, subject in SUBJECTS.items():
            print(f"  {subject['emoji']} {key}. {subject['display']}")
        
        choice = input("\n선택 (1-7): ").strip()
        
        if choice not in SUBJECTS:
            print("❌ 잘못된 선택입니다.")
            return
        
        detected_subject = choice
    
    # 병합 실행
    merge_metadata(fragment_file, detected_subject)

if __name__ == "__main__":
    main()