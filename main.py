import sys
import argparse
import os
from typing import List, Dict

from config import Config
from github_client import GitHubClient
from llm_analyzer import LLMAnalyzer
from report_generator import ReportGenerator
from security_check import SecurityChecker

class CodeReviewAssistant:
    def __init__(self):
        self.github_client = GitHubClient()
        self.llm_analyzer = LLMAnalyzer()
        self.report_generator = ReportGenerator()
        self.security_checker = SecurityChecker()
    
    def analyze_repository(self, repo: str, max_files: int = None) -> Dict:
        """GitHub 레포지토리 분석"""
        print(f"GitHub 레포지토리 분석 시작: {repo}")
        
        # 레포지토리 정보 확인
        repo_info = self.github_client.get_repo_info(repo)
        if not repo_info:
            print("레포지토리를 찾을 수 없습니다.")
            return {}
        
        print(f"레포지토리: {repo_info.get('full_name')}")
        print(f"설명: {repo_info.get('description', 'N/A')}")
        print(f"스타: {repo_info.get('stargazers_count', 0)}")
        
        # 파일 목록 가져오기
        print("\n파일 목록 수집 중...")
        all_files = self.github_client.get_all_files(repo)
        
        if not all_files:
            print("분석할 파일을 찾을 수 없습니다.")
            return {}
        
        # 파일 크기로 필터링 및 정렬
        valid_files = [f for f in all_files if f['size'] <= Config.MAX_FILE_SIZE]
        valid_files.sort(key=lambda x: x['size'])  # 작은 파일부터
        
        # 파일 수 제한
        if max_files:
            valid_files = valid_files[:max_files]
        else:
            valid_files = valid_files[:Config.MAX_FILES_PER_ANALYSIS]
        
        print(f"분석 대상: {len(valid_files)}개 파일")
        
        # 파일 내용 다운로드
        files_with_content = []
        for file_info in valid_files:
            print(f"다운로드: {file_info['path']}")
            content = self.github_client.get_file_content(repo, file_info['path'])
            
            if content:
                files_with_content.append({
                    'path': file_info['path'],
                    'content': content,
                    'size': file_info['size']
                })
        
        # LLM 분석 실행
        if files_with_content:
            return self.llm_analyzer.analyze_multiple_files(files_with_content)
        else:
            print("다운로드된 파일이 없습니다.")
            return {}
    
    def analyze_pull_request(self, repo: str, pr_number: int) -> Dict:
        """Pull Request 분석"""
        print(f"Pull Request 분석 시작: {repo}/#{pr_number}")
        
        # PR 정보 가져오기
        pr_info = self.github_client.get_pull_request(repo, pr_number)
        if not pr_info:
            print("Pull Request를 찾을 수 없습니다.")
            return {}
        
        print(f"제목: {pr_info.get('title')}")
        print(f"👤 작성자: {pr_info.get('user', {}).get('login')}")
        print(f"상태: {pr_info.get('state')}")
        
        # PR에서 변경된 파일들 가져오기
        pr_files = self.github_client.get_pr_files(repo, pr_number)
        if not pr_files:
            print("변경된 파일을 찾을 수 없습니다.")
            return {}
        
        print(f"변경된 파일: {len(pr_files)}개")
        
        # 분석할 파일 준비
        files_with_content = []
        for file_info in pr_files:
            # 삭제된 파일은 제외
            if file_info.get('status') == 'removed':
                continue
            
            # 지원하는 확장자만 분석
            filename = file_info.get('filename', '')
            if not any(filename.endswith(ext) for ext in Config.SUPPORTED_EXTENSIONS):
                continue
            
            print(f"분석: {filename}")
            content = self.github_client.get_file_content(repo, filename)
            
            if content:
                files_with_content.append({
                    'path': filename,
                    'content': content,
                    'changes': file_info.get('changes', 0),
                    'additions': file_info.get('additions', 0),
                    'deletions': file_info.get('deletions', 0)
                })
        
        # LLM 분석 실행
        if files_with_content:
            return self.llm_analyzer.analyze_multiple_files(files_with_content)
        else:
            print("분석할 파일이 없습니다.")
            return {}
    
    def analyze_local_project(self, project_path: str, skip_security_check: bool = False) -> Dict:
        """로컬 프로젝트 분석"""
        print(f"로컬 프로젝트 분석 시작: {project_path}")
        
        if not os.path.exists(project_path):
            print("경로를 찾을 수 없습니다.")
            return {}
        
        # 보안 검사 (로컬 프로젝트만)
        if not skip_security_check:
            print("\n🔒 보안 검사 실행 중...")
            security_issues = self.security_checker.check_directory(project_path)
            
            if security_issues:
                print("보안 문제 발견!")
                for issue in security_issues:
                    print(f"   {issue['file']}:{issue['line']}")
                    print(f"      {issue['content']}")
                
                user_choice = input("\n계속 진행하시겠습니까? (y/N): ").lower()
                if user_choice != 'y':
                    print("분석을 중단합니다.")
                    return {}
                print()
            else:
                print("보안 검사 통과!")
        
        # 로컬 파일 수집
        files_with_content = []
        
        for root, dirs, files in os.walk(project_path):
            # 제외할 디렉토리
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', 'venv', '.vscode'}]
            
            for file in files:
                # 지원하는 확장자만
                if not any(file.endswith(ext) for ext in Config.SUPPORTED_EXTENSIONS):
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path)
                
                # 파일 크기 체크
                if os.path.getsize(file_path) > Config.MAX_FILE_SIZE:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    files_with_content.append({
                        'path': relative_path,
                        'content': content,
                        'size': os.path.getsize(file_path)
                    })
                    
                    print(f"발견: {relative_path}")
                    
                    # 파일 수 제한
                    if len(files_with_content) >= Config.MAX_FILES_PER_ANALYSIS:
                        break
                        
                except Exception as e:
                    print(f"파일 읽기 실패 ({relative_path}): {e}")
            
            if len(files_with_content) >= Config.MAX_FILES_PER_ANALYSIS:
                break
        
        print(f"분석 대상: {len(files_with_content)}개 파일")
        
        # LLM 분석 실행
        if files_with_content:
            return self.llm_analyzer.analyze_multiple_files(files_with_content)
        else:
            print("분석할 파일이 없습니다.")
            return {}
    
    def run_tests(self) -> bool:
        """연결 테스트 실행"""
        print("🔧 시스템 연결 테스트 시작...")
        
        # 설정 검증
        if not Config.validate():
            return False
        
        # GitHub 연결 테스트
        github_ok = self.github_client.test_connection()
        
        # Ollama 연결 테스트
        ollama_ok = self.llm_analyzer.test_connection()
        
        if github_ok and ollama_ok:
            print("모든 연결이 정상입니다!")
            return True
        else:
            print("일부 연결에 문제가 있습니다.")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="AI 코드 리뷰 어시스턴트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py --repo microsoft/vscode
  python main.py --pr facebook/react/12345
  python main.py --local ./my-project
  python main.py --test
        """
    )
    
    parser.add_argument('--repo', help='GitHub 레포지토리 (user/repo)')
    parser.add_argument('--pr', help='Pull Request (user/repo/number)')
    parser.add_argument('--local', help='로컬 프로젝트 경로')
    parser.add_argument('--test', action='store_true', help='연결 테스트 실행')
    parser.add_argument('--security-check', action='store_true', help='보안 검사만 실행')
    parser.add_argument('--skip-security', action='store_true', help='보안 검사 건너뛰기')
    parser.add_argument('--max-files', type=int, help='최대 분석 파일 수')
    parser.add_argument('--output', choices=['console', 'html', 'json', 'all'], 
                       default='all', help='출력 형식')
    
    args = parser.parse_args()
    
    # 인자가 없으면 도움말 출력
    if not any([args.repo, args.pr, args.local, args.test, args.security_check]):
        parser.print_help()
        return
    
    # 어시스턴트 초기화
    assistant = CodeReviewAssistant()
    
    # 보안 검사만 실행
    if args.security_check:
        if args.local:
            issues = assistant.security_checker.check_directory(args.local)
            if issues:
                print("보안 문제 발견!")
                for issue in issues:
                    print(f"   {issue['file']}:{issue['line']}")
                    print(f"      {issue['content']}")
                sys.exit(1)
            else:
                print("보안 검사 통과!")
                sys.exit(0)
        else:
            print("--local 경로를 지정해주세요.")
            sys.exit(1)
    
    # 테스트 모드
    if args.test:
        success = assistant.run_tests()
        sys.exit(0 if success else 1)
    
    # 분석 실행
    analysis_result = {}
    repo_name = ""
    
    try:
        if args.repo:
            analysis_result = assistant.analyze_repository(args.repo, args.max_files)
            repo_name = args.repo
        elif args.pr:
            # PR 형식 파싱: user/repo/number
            parts = args.pr.split('/')
            if len(parts) >= 3:
                repo = '/'.join(parts[:-1])
                pr_number = int(parts[-1])
                analysis_result = assistant.analyze_pull_request(repo, pr_number)
                repo_name = f"{repo}/PR#{pr_number}"
            else:
                print("PR 형식이 올바르지 않습니다. (user/repo/number)")
                return
        elif args.local:
            analysis_result = assistant.analyze_local_project(args.local, args.skip_security)
            repo_name = os.path.basename(args.local)
    
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
        return
    except Exception as e:
        print(f"오류 발생: {e}")
        return
    
    # 결과 출력
    if analysis_result:
        if args.output in ['console', 'all']:
            assistant.report_generator.print_console_report(analysis_result, repo_name)
        
        if args.output in ['html', 'all']:
            assistant.report_generator.generate_html_report(analysis_result, repo_name)
        
        if args.output in ['json', 'all']:
            assistant.report_generator.generate_json_report(analysis_result, repo_name)
        
        print(f"\n분석 완료! 리포트가 {assistant.report_generator.reports_dir} 폴더에 저장되었습니다.")
    else:
        print("분석 결과가 없습니다.")

if __name__ == "__main__":
    main()