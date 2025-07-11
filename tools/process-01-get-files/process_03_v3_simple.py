"""
Process 3 v3 : 첨부파일 다운로드 - 단순화된 구조
------------------------------------------------
입력 : 02_file_urls_cache.csv
저장 : <script_dir>/download_{설정명}/
         {year}_{phase}_{subject}_{파일명}.*
         
특징:
- 단순화된 폴더 구조 (선택 조건을 폴더명에 반영)
- 연도별 선택 가능
- 과목별, 차수별 필터링
- 확장자별 정리 옵션
"""

import os
import csv
import re
import requests
from urllib.parse import urlparse, unquote
from collections import defaultdict
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

def get_available_years(csv_path):
    """CSV에서 사용 가능한 연도 목록 추출"""
    years = set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("exists", "").lower() == "true":
                year = row.get("year", "")
                if year and year != "unknown":
                    years.add(year)
    return sorted(years, reverse=True)

def classify_subject(filename, phase):
    """파일명에서 과목 분류"""
    filename_lower = filename.lower()
    
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
    
    for keyword in preliminary_keywords:
        if keyword in filename_lower:
            return False
    
    for keyword in final_keywords:
        if keyword in filename_lower:
            return True
    
    if any(word in filename_lower for word in ["답안", "정답"]):
        return False
    
    return None

def generate_folder_name(selected_years, selected_phase, selected_subjects):
    """선택 조건에 따른 폴더명 생성"""
    # 현재 날짜시간
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    parts = []
    
    # 연도
    if selected_years:
        if len(selected_years) == 1:
            parts.append(selected_years[0])
        elif len(selected_years) <= 3:
            parts.append("-".join(selected_years))
        else:
            parts.append(f"{selected_years[0]}-{selected_years[-1]}")
    
    # 차수
    if selected_phase:
        parts.append(selected_phase)
    
    # 과목
    if selected_subjects:
        if len(selected_subjects) == 1:
            parts.append(selected_subjects[0])
        elif len(selected_subjects) <= 2:
            parts.append("-".join(selected_subjects))
        else:
            parts.append(f"{len(selected_subjects)}과목")
    
    condition_desc = "_".join(parts) if parts else "전체"
    return f"{timestamp}_{condition_desc}"

def download_simple(csv_path: str, base_dir: str, selected_years=None, selected_phase=None, 
                   selected_subjects=None, final_only=False, organize_by_ext=False):
    """
    단순화된 구조로 다운로드
    """
    # 폴더명 생성
    folder_name = generate_folder_name(selected_years, selected_phase, selected_subjects)
    download_dir = os.path.join(base_dir, "download", folder_name)
    os.makedirs(download_dir, exist_ok=True)
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    stats = {"downloaded": 0, "skipped": 0, "failed": 0, "filtered": 0}
    file_extensions = defaultdict(int)
    
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("exists", "").lower() != "true":
                continue
            
            year  = row["year"] or "unknown"
            phase = row["phase"] or "unknown"
            url   = row["url"]
            
            # 연도 필터링
            if selected_years and year not in selected_years:
                continue
            
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
            
            # 확정답안 필터링 (1차만)
            if final_only and phase == "1차":
                is_final = is_final_answer(fname)
                if is_final is False:
                    stats["filtered"] += 1
                    continue
            
            # 과목 분류
            subject = classify_subject(fname, phase)
            
            # 과목 필터링
            if selected_subjects and subject not in selected_subjects:
                stats["filtered"] += 1
                continue
            
            # 확장자 추출
            ext = os.path.splitext(fname)[1].lower()
            if ext:
                file_extensions[ext] += 1
            
            # 파일명 구성: 연도_차수_과목_원본파일명
            new_fname = f"{year}_{phase}_{subject}_{fname}"
            
            # 확장자별 정리 옵션
            if organize_by_ext and ext:
                ext_dir = os.path.join(download_dir, ext[1:])  # .제거
                os.makedirs(ext_dir, exist_ok=True)
                save_path = os.path.join(ext_dir, new_fname)
            else:
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
    
    if file_extensions:
        print("\n📁 파일 형식별 통계:")
        for ext, count in sorted(file_extensions.items()):
            print(f"  {ext}: {count}개")
    
    print(f"\n💾 저장 위치: {download_dir}")
    print("="*50)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, CSV_NAME)
    
    if not os.path.isfile(csv_path):
        print(f"⚠️ '{CSV_NAME}'가 없습니다. 먼저 Process 2를 실행하세요.")
        return
    
    # 사용 가능한 연도 확인
    available_years = get_available_years(csv_path)
    
    print("\n📂 CPA 시험 파일 다운로드 (단순화 버전)")
    print("="*50)
    print("1. 모든 파일 다운로드")
    print("2. 선택 다운로드")
    print("="*50)
    
    main_choice = input("선택하세요 (1 또는 2, 기본값=1): ").strip()
    
    selected_years = None
    selected_phase = None
    selected_subjects = None
    final_only = False
    organize_by_ext = False
    
    if main_choice == "2":
        # 연도 선택
        print(f"\n📅 연도 선택 (사용 가능: {available_years[0]}~{available_years[-1]})")
        print("1. 전체 연도")
        print("2. 특정 연도 선택")
        print("3. 최근 5년")
        print("4. 최근 10년")
        
        year_choice = input("선택 (1~4, 기본값=1): ").strip()
        
        if year_choice == "2":
            year_input = input("연도를 입력하세요 (쉼표로 구분, 예: 2023,2024): ").strip()
            if year_input:
                selected_years = [y.strip() for y in year_input.split(",") if y.strip() in available_years]
                if selected_years:
                    print(f"✅ 선택된 연도: {', '.join(sorted(selected_years, reverse=True))}")
                else:
                    print("⚠️ 유효한 연도가 없습니다. 전체 연도로 진행합니다.")
        elif year_choice == "3":
            selected_years = available_years[:5]
            print(f"✅ 최근 5년: {', '.join(selected_years)}")
        elif year_choice == "4":
            selected_years = available_years[:10]
            print(f"✅ 최근 10년: {', '.join(selected_years)}")
        
        # 차수 선택
        print("\n📚 차수를 선택하세요:")
        print("1. 전체 (1차+2차)")
        print("2. 1차 시험만")
        print("3. 2차 시험만")
        phase_choice = input("선택 (1~3, 기본값=1): ").strip()
        
        if phase_choice == "2":
            selected_phase = "1차"
        elif phase_choice == "3":
            selected_phase = "2차"
        
        # 과목 선택
        print("\n📖 과목 선택:")
        print("1. 전체 과목")
        print("2. 특정 과목 선택")
        
        subject_choice = input("선택 (1 또는 2, 기본값=1): ").strip()
        
        if subject_choice == "2":
            if selected_phase == "1차":
                subjects = FIRST_EXAM_SUBJECTS
            elif selected_phase == "2차":
                subjects = SECOND_EXAM_SUBJECTS
            else:
                subjects = {**FIRST_EXAM_SUBJECTS, **SECOND_EXAM_SUBJECTS}
            
            subject_list = list(subjects.keys())
            print("\n다운로드할 과목:")
            for i, subject in enumerate(subject_list, 1):
                print(f"{i}. {subject}")
            
            subject_input = input("\n과목 번호를 입력하세요 (쉼표로 구분): ").strip()
            if subject_input:
                try:
                    indices = [int(x.strip()) - 1 for x in subject_input.split(",")]
                    selected_subjects = [subject_list[i] for i in indices if 0 <= i < len(subject_list)]
                    if selected_subjects:
                        print(f"✅ 선택된 과목: {', '.join(selected_subjects)}")
                except:
                    print("⚠️ 잘못된 입력입니다. 전체 과목으로 진행합니다.")
        
        # 확정답안 필터링 (1차만)
        if selected_phase == "1차" or not selected_phase:
            answer_choice = input("\n확정답안만 다운로드하시겠습니까? (1차 시험만 해당, y/N): ").strip().lower()
            if answer_choice == 'y':
                final_only = True
                if not selected_phase:
                    selected_phase = "1차"
                    print("ℹ️ 확정답안은 1차 시험만 제공되므로 1차 파일만 다운로드합니다.")
        
        # 확장자별 정리
        ext_choice = input("\n확장자별로 폴더를 나누시겠습니까? (y/N): ").strip().lower()
        if ext_choice == 'y':
            organize_by_ext = True
    
    # 설정 요약
    print("\n" + "="*50)
    print("📋 다운로드 설정:")
    if selected_years:
        print(f"  - 연도: {', '.join(sorted(selected_years, reverse=True))}")
    if selected_phase:
        print(f"  - 차수: {selected_phase}")
    if selected_subjects:
        print(f"  - 과목: {', '.join(selected_subjects)}")
    if final_only:
        print("  - 확정답안만 다운로드")
    if organize_by_ext:
        print("  - 확장자별 폴더 정리")
    print("="*50)
    
    input("\n계속하려면 Enter를 누르세요...")
    
    download_simple(csv_path, script_dir, selected_years, selected_phase, 
                   selected_subjects, final_only, organize_by_ext)

if __name__ == "__main__":
    main()