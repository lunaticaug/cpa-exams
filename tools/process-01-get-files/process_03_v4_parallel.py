"""
Process 3 v4 : 첨부파일 다운로드 - 병렬 처리 버전
------------------------------------------------
입력 : 02_file_urls_cache.csv
저장 : <script_dir>/download_{설정명}/
         {year}_{phase}_{subject}_{파일명}.*
         
특징:
- 병렬 다운로드로 속도 대폭 개선
- 동시 다운로드 워커 수 조절 가능
- 진행 상황 실시간 표시
- 재시도 로직 포함
- 기존 v3의 모든 기능 포함
"""

import os
import csv
import requests
from urllib.parse import urlparse, unquote
from collections import defaultdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

CSV_NAME   = "02_file_urls_cache.csv"
TIMEOUT    = 15
CHUNK_SIZE = 8192
MAX_RETRIES = 3   # 최대 재시도 횟수

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

# 전역 통계를 위한 lock
stats_lock = threading.Lock()

class DownloadStats:
    """다운로드 통계 관리"""
    def __init__(self):
        self.downloaded = 0
        self.skipped = 0
        self.failed = 0
        self.filtered = 0
        self.total = 0
        self.start_time = time.time()
        
    def increment(self, stat_type):
        with stats_lock:
            setattr(self, stat_type, getattr(self, stat_type) + 1)
    
    def get_progress(self):
        with stats_lock:
            completed = self.downloaded + self.skipped + self.failed + self.filtered
            return completed, self.total
    
    def get_speed(self):
        """평균 다운로드 속도 계산"""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return self.downloaded / elapsed
        return 0

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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    parts = []
    
    if selected_years:
        if len(selected_years) == 1:
            parts.append(selected_years[0])
        elif len(selected_years) <= 3:
            parts.append("-".join(selected_years))
        else:
            parts.append(f"{selected_years[0]}-{selected_years[-1]}")
    
    if selected_phase:
        parts.append(selected_phase)
    
    if selected_subjects:
        if len(selected_subjects) == 1:
            parts.append(selected_subjects[0])
        elif len(selected_subjects) <= 2:
            parts.append("-".join(selected_subjects))
        else:
            parts.append(f"{len(selected_subjects)}과목")
    
    condition_desc = "_".join(parts) if parts else "전체"
    return f"{timestamp}_{condition_desc}"

def download_file(session, row, download_dir, selected_years, selected_phase, 
                 selected_subjects, final_only, organize_by_ext, stats, file_extensions):
    """단일 파일 다운로드 (워커 스레드에서 실행)"""
    try:
        year = row["year"] or "unknown"
        phase = row["phase"] or "unknown"
        url = row["url"]
        
        # 필터링 체크
        if selected_years and year not in selected_years:
            stats.increment('filtered')
            return
        
        if selected_phase and phase != selected_phase:
            stats.increment('filtered')
            return
        
        # 다운로드 시도 (재시도 포함)
        for retry in range(MAX_RETRIES):
            try:
                resp = session.get(url, stream=True, timeout=TIMEOUT)
                resp.raise_for_status()
                break
            except Exception as e:
                if retry == MAX_RETRIES - 1:
                    print(f"⚠️ [FAIL] {url} ▶ {e}")
                    stats.increment('failed')
                    return
                time.sleep(1)  # 재시도 전 대기
        
        # 파일명 추출
        cd = resp.headers.get("Content-Disposition", "")
        if "filename=" in cd:
            fname = cd.split("filename=")[-1].strip('"; ')
        else:
            fname = os.path.basename(urlparse(url).path)
        fname = unquote(fname)
        
        # 확정답안 필터링
        if final_only and phase == "1차":
            is_final = is_final_answer(fname)
            if is_final is False:
                stats.increment('filtered')
                return
        
        # 과목 분류
        subject = classify_subject(fname, phase)
        
        # 과목 필터링
        if selected_subjects and subject not in selected_subjects:
            stats.increment('filtered')
            return
        
        # 확장자 추출
        ext = os.path.splitext(fname)[1].lower()
        if ext:
            with stats_lock:
                file_extensions[ext] += 1
        
        # 파일명 구성
        new_fname = f"{year}_{phase}_{subject}_{fname}"
        
        # 저장 경로 결정
        if organize_by_ext and ext:
            ext_dir = os.path.join(download_dir, ext[1:])
            os.makedirs(ext_dir, exist_ok=True)
            save_path = os.path.join(ext_dir, new_fname)
        else:
            save_path = os.path.join(download_dir, new_fname)
        
        # 이미 존재하는지 확인
        if os.path.exists(save_path):
            print(f"😓 [SKIP] 이미 존재: {new_fname}")
            stats.increment('skipped')
            return
        
        # 파일 저장
        with open(save_path, "wb") as out:
            for chunk in resp.iter_content(CHUNK_SIZE):
                if chunk:
                    out.write(chunk)
        
        print(f"✅ [OK] {new_fname}")
        stats.increment('downloaded')
        
    except Exception as e:
        print(f"⚠️ [ERROR] 예기치 않은 오류: {e}")
        stats.increment('failed')

def show_progress(stats):
    """진행 상황 표시 (별도 스레드에서 실행)"""
    while True:
        completed, total = stats.get_progress()
        if total > 0:
            progress = completed / total * 100
            speed = stats.get_speed()
            print(f"\r⏳ 진행률: {progress:.1f}% ({completed}/{total}) | "
                  f"속도: {speed:.1f} 파일/초", end='', flush=True)
        
        if completed >= total and total > 0:
            break
        
        time.sleep(0.5)

def download_parallel(csv_path: str, base_dir: str, selected_years=None, selected_phase=None, 
                     selected_subjects=None, final_only=False, organize_by_ext=False, max_workers=10):
    """병렬 다운로드 실행"""
    # 폴더 생성
    folder_name = generate_folder_name(selected_years, selected_phase, selected_subjects)
    download_dir = os.path.join(base_dir, "download", folder_name)
    os.makedirs(download_dir, exist_ok=True)
    
    # 세션 생성
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    
    # 통계 및 데이터 준비
    stats = DownloadStats()
    file_extensions = defaultdict(int)
    
    # CSV 읽기
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("exists", "").lower() == "true":
                rows.append(row)
    
    stats.total = len(rows)
    
    print(f"\n🚀 병렬 다운로드 시작 (워커: {max_workers}개)")
    print(f"📁 대상 파일: {stats.total}개")
    print("="*50)
    
    # 진행 상황 표시 스레드 시작
    progress_thread = threading.Thread(target=show_progress, args=(stats,))
    progress_thread.daemon = True
    progress_thread.start()
    
    # 병렬 다운로드 실행
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for row in rows:
            future = executor.submit(
                download_file, session, row, download_dir, selected_years, 
                selected_phase, selected_subjects, final_only, organize_by_ext,
                stats, file_extensions
            )
            futures.append(future)
        
        # 모든 작업 완료 대기
        for future in as_completed(futures):
            pass
    
    # 진행 표시 종료 대기
    progress_thread.join()
    
    # 최종 통계 출력
    print("\n\n" + "="*50)
    print("📊 다운로드 완료 통계:")
    print(f"  ✅ 다운로드: {stats.downloaded}개")
    print(f"  😓 스킵: {stats.skipped}개")
    print(f"  🔍 필터링: {stats.filtered}개")
    print(f"  ⚠️ 실패: {stats.failed}개")
    
    elapsed = time.time() - stats.start_time
    print(f"\n⏱️ 소요 시간: {elapsed:.1f}초")
    print(f"🚀 평균 속도: {stats.get_speed():.1f} 파일/초")
    
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
    
    print("\n📂 CPA 시험 파일 다운로드 (병렬 처리 버전)")
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
    
    # 워커 수 설정
    max_workers = 10
    print(f"\n⚙️ 동시 다운로드 수 (1-20, 기본값={max_workers}): ", end='')
    worker_input = input().strip()
    if worker_input and worker_input.isdigit():
        max_workers = max(1, min(20, int(worker_input)))
    
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
    print(f"  - 동시 다운로드 수: {max_workers}")
    print("="*50)
    
    input("\n계속하려면 Enter를 누르세요...")
    
    download_parallel(csv_path, script_dir, selected_years, selected_phase, 
                     selected_subjects, final_only, organize_by_ext, max_workers)

if __name__ == "__main__":
    main()