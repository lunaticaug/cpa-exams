"""
기능: DOCX 변환 경로 테스트 및 라이브러리 확인
입력: HWP/DOCX 파일
출력: 변환 가능성 분석
"""

import subprocess
from pathlib import Path
import json

def check_pandoc():
    """Pandoc 설치 확인"""
    try:
        result = subprocess.run(['pandoc', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            return True, version
    except:
        pass
    return False, None

def check_python_docx():
    """python-docx 라이브러리 확인"""
    try:
        import docx
        return True, docx.__version__
    except:
        return False, None

def check_mammoth():
    """mammoth 라이브러리 확인 (DOCX to HTML/Markdown)"""
    try:
        import mammoth
        return True, mammoth.__version__
    except:
        return False, None

def test_docx_conversion():
    """DOCX 변환 테스트"""
    print("=== DOCX 변환 경로 분석 ===\n")
    
    # 도구 확인
    tools = {
        "Pandoc": check_pandoc(),
        "python-docx": check_python_docx(),
        "mammoth": check_mammoth()
    }
    
    print("【도구 확인】")
    for tool, (available, version) in tools.items():
        status = f"✓ {version}" if available else "✗ 미설치"
        print(f"- {tool}: {status}")
    
    # 변환 경로 제안
    print("\n【변환 경로 제안】")
    
    print("\n1. HWP → DOCX 변환")
    print("   - 온라인 도구 (CloudConvert, Zamzar)")
    print("   - 한컴오피스 내보내기")
    print("   - LibreOffice (부분 지원)")
    
    print("\n2. DOCX → Markdown 변환")
    if tools["Pandoc"][0]:
        print("   ✓ Pandoc 사용 가능 (추천)")
        print("     명령어: pandoc input.docx -o output.md --extract-media=media")
    
    if tools["mammoth"][0]:
        print("   ✓ Mammoth 사용 가능")
        print("     - 표와 이미지 처리 우수")
    
    print("\n3. 표 처리 개선 방안")
    print("   - DOCX에서 표 구조 유지")
    print("   - Pandoc의 표 옵션 활용")
    print("   - 복잡한 표는 HTML 테이블로 보존")
    
    # 테스트 결과 저장
    result = {
        "tools": {k: {"available": v[0], "version": v[1]} for k, v in tools.items()},
        "recommended_path": "HWP → DOCX (manual) → Pandoc → Markdown",
        "table_strategy": "Use Pandoc with pipe_tables extension"
    }
    
    with open("output-07-docx-test.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    return tools

def install_missing_tools():
    """누락된 도구 설치 명령어 제공"""
    print("\n【설치 명령어】")
    print("- Pandoc: brew install pandoc (macOS)")
    print("- python-docx: pip install python-docx")
    print("- mammoth: pip install mammoth")

if __name__ == "__main__":
    tools = test_docx_conversion()
    
    # 누락된 도구가 있으면 설치 안내
    missing = [name for name, (available, _) in tools.items() if not available]
    if missing:
        print(f"\n누락된 도구: {', '.join(missing)}")
        install_missing_tools()