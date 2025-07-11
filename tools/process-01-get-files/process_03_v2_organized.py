"""
Process 3 v2 : 첨부파일 다운로드 - 과목별 정리 버전
----------------------------------------------------
입력 : 02_file_urls_cache.csv
저장 : <script_dir>/download/
         {YYYYMMDD_HHMMSS}_{조건}/{연도}_{차수}_{과목}_{파일명}.*
         
특징:
- 과목별로 폴더를 나누어 정리
- 확정답안만 다운로드하는 옵션 제공
- 중복 파일 처리 개선
"""

import os
import csv
import re
import requests
from urllib.parse import urlparse, unquote
from datetime import datetime

CSV_NAME   = "02_file_urls_cache.csv"
TIMEOUT    = 15
CHUNK_SIZE = 8192

# 1차 시험 과목 매핑
FIRST_EXAM_SUBJECTS = {
    "경영학": ["경영학"],
    "경제학": ["경제원론", "경제학"],
    "상법": ["상법"],
    "세법": ["세법개론", "세법"],
    "회계학": ["회계학"],
    "영어": ["영어"],
    "답안": ["답안", "정답", "가답안", "확정답안", "확정정답", "최종정답"]
}

# 2차 시험 과목 매핑
SECOND_EXAM_SUBJECTS = {
    "세법": ["세법"],
    "재무관리": ["재무관리"],
    "회계감사": ["회계감사"],
    "원가회계": ["원가회계", "원가관리회계"],
    "재무회계": ["재무회계"]
}

def classify_subject(filename, phase):
    """파일명에서 과목 분류"""
    filename_lower = filename.lower()
    
    # 선택할 과목 매핑
    subjects_map = FIRST_EXAM_SUBJECTS if "1차" in phase else SECOND_EXAM_SUBJECTS
    
    for subject, keywords in subjects_map.items():
        for keyword in keywords:
            if keyword.lower() in filename_lower:
                return subject
    
    return "기타"

def is_final_answer(filename):
    """확정답안 여부 판별"""
    final_keywords = ["확정", "최종", "(최종)", "(확정)"]
    preliminary_keywords = ["가답안"]
    
    filename_lower = filename.lower()
    
    # 가답안이면 False
    for keyword in preliminary_keywords:
        if keyword in filename_lower:
            return False
    
    # 확정/최종 키워드가 있으면 True
    for keyword in final_keywords:
        if keyword in filename_lower:
            return True
    
    # 답안 파일이 아니면 None (일반 문제)
    if any(word in filename_lower for word in ["답안", "정답"]):
        return False  # 답안인데 확정이 아니면 가답안으로 간주
    
    return None  # 일반 문제 파일

def generate_folder_name(selected_phase, selected_subjects, final_only):
    """선택 조건에 따른 폴더명 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    parts = []
    
    if selected_phase:
        parts.append(selected_phase)
    
    if selected_subjects:
        if len(selected_subjects) == 1:
            parts.append(selected_subjects[0])
        elif len(selected_subjects) <= 2:
            parts.append("-".join(selected_subjects))
        else:
            parts.append(f"{len(selected_subjects)}과목")
    
    if final_only:
        parts.append("확정답안")
    
    condition_desc = "_".join(parts) if parts else "전체"
    return f"{timestamp}_{condition_desc}"

def download_organized(csv_path: str, base_dir: str, final_only=False, selected_subjects=None, selected_phase=None):
    """
    과목별로 정리하여 다운로드
    
    Args:
        csv_path: CSV 파일 경로
        base_dir: 다운로드 기본 디렉토리
        final_only: True면 확정답안만 다운로드
        selected_subjects: 선택된 과목 리스트 (None이면 전체)
        selected_phase: 선택된 차수 ("1차", "2차", None이면 전체)
    """
    # 폴더명 생성
    folder_name = generate_folder_name(selected_phase, selected_subjects, final_only)
    download_dir = os.path.join(base_dir, "download", folder_name)
    os.makedirs(download_dir, exist_ok=True)
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    stats = {"downloaded": 0, "skipped": 0, "failed": 0, "filtered": 0}
    
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("exists", "").lower() != "true":
                continue
            
            year  = row["year"] or "unknown"
            phase = row["phase"] or "unknown"
            url   = row["url"]
            
            # 차수 필터링
            if selected_phase and phase != selected_phase:
                continue
            
            # 파일 다운로드 시도
            try:
                resp = session.get(url, stream=True, timeout=TIMEOUT)
                resp.raise_for_status()
            except Exception as err:
                print(f"⚠️ [FAIL] {url} ▶ {err}")
                stats["failed"] += 1
                continue
            
            # 원본 파일명 추출
            cd = resp.headers.get("Content-Disposition", "")
            if "filename=" in cd:
                fname = cd.split("filename=")[-1].strip('"; ')
            else:
                fname = os.path.basename(urlparse(url).path)
            fname = unquote(fname)
            
            # 확정답안 필터링
            if final_only:
                is_final = is_final_answer(fname)
                if is_final is False:  # 가답안이면 스킵
                    print(f"🔍 [FILTER] 가답안 스킵: {fname}")
                    stats["filtered"] += 1
                    continue
            
            # 과목 분류
            subject = classify_subject(fname, phase)
            
            # 과목 필터링
            if selected_subjects and subject not in selected_subjects:
                stats["filtered"] += 1
                continue
            
            # 파일명 구성: 연도_차수_과목_원본파일명
            new_fname = f"{year}_{phase}_{subject}_{fname}"
            save_path = os.path.join(download_dir, new_fname)
            
            # 이미 존재하는지 확인
            if os.path.exists(save_path):
                print(f"😓 [SKIP] 이미 존재: {new_fname}")
                stats["skipped"] += 1
                continue
            
            # 저장
            try:
                with open(save_path, "wb") as out:
                    for chunk in resp.iter_content(CHUNK_SIZE):
                        if chunk:
                            out.write(chunk)
                print(f"✅ [OK] {new_fname}")
                stats["downloaded"] += 1
            except Exception as err:
                print(f"⚠️ [FAIL] 저장 오류 {new_fname} ▶ {err}")
                stats["failed"] += 1
    
    # 통계 출력
    print("\n" + "="*50)
    print("📊 다운로드 완료 통계:")
    print(f"  ✅ 다운로드: {stats['downloaded']}개")
    print(f"  😓 스킵: {stats['skipped']}개")
    print(f"  🔍 필터링: {stats['filtered']}개")
    print(f"  ⚠️ 실패: {stats['failed']}개")
    print("="*50)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, CSV_NAME)
    
    if not os.path.isfile(csv_path):
        print(f"⚠️ '{CSV_NAME}'가 없습니다. 먼저 Process 2를 실행하세요.")
        return
    
    # 사용자에게 옵션 선택 받기
    print("\n📂 CPA 시험 파일 다운로드 (과목별 정리 버전)")
    print("="*50)
    print("1. 모든 파일 다운로드")
    print("2. 1차 확정답안만 다운로드")
    print("3. 특정 과목만 다운로드")
    print("="*50)
    
    choice = input("선택하세요 (1, 2, 3, 기본값=1): ").strip()
    
    final_only = False
    selected_subjects = None
    selected_phase = None
    
    if choice == "2":
        final_only = True
        selected_phase = "1차"  # 확정답안은 1차만 해당
        print("\n✨ 1차 시험 확정답안만 다운로드합니다.")
    
    elif choice == "3":
        # 차수 선택
        print("\n📚 차수를 선택하세요:")
        print("1. 1차 시험")
        print("2. 2차 시험")
        print("3. 전체 (1차+2차)")
        phase_choice = input("선택 (1, 2, 3, 기본값=3): ").strip()
        
        if phase_choice == "1":
            selected_phase = "1차"
            subjects = FIRST_EXAM_SUBJECTS
        elif phase_choice == "2":
            selected_phase = "2차"
            subjects = SECOND_EXAM_SUBJECTS
        else:
            subjects = {**FIRST_EXAM_SUBJECTS, **SECOND_EXAM_SUBJECTS}
        
        # 과목 선택
        print("\n📖 다운로드할 과목을 선택하세요:")
        subject_list = list(subjects.keys())
        for i, subject in enumerate(subject_list, 1):
            print(f"{i}. {subject}")
        print(f"{len(subject_list)+1}. 전체 과목")
        
        subject_input = input("\n과목 번호를 입력하세요 (쉼표로 구분, 예: 1,3,5): ").strip()
        
        if subject_input == str(len(subject_list)+1) or not subject_input:
            selected_subjects = None  # 전체
        else:
            try:
                indices = [int(x.strip()) - 1 for x in subject_input.split(",")]
                selected_subjects = [subject_list[i] for i in indices if 0 <= i < len(subject_list)]
                
                if selected_subjects:
                    print(f"\n✅ 선택된 과목: {', '.join(selected_subjects)}")
                else:
                    print("\n⚠️ 잘못된 선택입니다. 전체 과목을 다운로드합니다.")
            except:
                print("\n⚠️ 잘못된 입력입니다. 전체 과목을 다운로드합니다.")
        
        # 확정답안 필터링 여부 (1차 시험만 해당)
        if selected_phase == "1차" or not selected_phase:
            answer_choice = input("\n확정답안만 다운로드하시겠습니까? (1차 시험만 해당, y/N): ").strip().lower()
            if answer_choice == 'y':
                final_only = True
                if not selected_phase:  # 전체 선택인 경우
                    selected_phase = "1차"  # 1차로 제한
                    print("ℹ️ 확정답안은 1차 시험만 제공되므로 1차 파일만 다운로드합니다.")
    
    # 선택 사항 요약
    print("\n" + "="*50)
    print("📋 다운로드 설정:")
    if selected_phase:
        print(f"  - 차수: {selected_phase}")
    if selected_subjects:
        print(f"  - 과목: {', '.join(selected_subjects)}")
    if final_only:
        print("  - 확정답안만 다운로드")
    print("="*50)
    
    download_organized(csv_path, script_dir, final_only, selected_subjects, selected_phase)

if __name__ == "__main__":
    main()