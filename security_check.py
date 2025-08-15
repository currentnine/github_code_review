import os
import re
import sys
from pathlib import Path
from typing import List, Dict

class SecurityChecker:
    def __init__(self):
        # 검사할 패턴들
        self.sensitive_patterns = [
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Access Token'),
            (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API Key'),
            (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
            (r'password\s*=\s*["\'][^"\']{3,}["\']', '하드코딩된 비밀번호'),
            (r'secret\s*=\s*["\'][^"\']{3,}["\']', '하드코딩된 시크릿'),
            (r'token\s*=\s*["\'][^"\']{10,}["\']', '하드코딩된 토큰'),
            (r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']', 'API 키'),
        ]
        
        # 제외할 파일들
        self.exclude_files = {'.env', '.env.example', 'security_check.py', 'README.md'}
        self.exclude_dirs = {'.git', '__pycache__', 'venv', 'node_modules', '.vscode', '.idea'}
    
    def check_directory(self, directory: str = '.') -> List[Dict]:
        """디렉토리 내 모든 파일 보안 검사"""
        issues = []
        
        for root, dirs, files in os.walk(directory):
            # 제외 디렉토리 스킵
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                if file in self.exclude_files:
                    continue
                    
                file_path = os.path.join(root, file)
                file_issues = self.check_file(file_path)
                issues.extend(file_issues)
        
        return issues
    
    def check_file(self, file_path: str) -> List[Dict]:
        """단일 파일 보안 검사"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            for i, line in enumerate(content.split('\n'), 1):
                for pattern, description in self.sensitive_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append({
                            'file': file_path,
                            'line': i,
                            'content': line.strip()[:50] + '...' if len(line.strip()) > 50 else line.strip(),
                            'type': description,
                            'pattern': pattern
                        })
        except Exception:
            # 바이너리 파일이나 읽을 수 없는 파일은 무시
            pass
        
        return issues
    
    def check_staged_env_files(self) -> List[str]:
        """git staged 상태의 환경 변수 파일 검사"""
        env_files = ['.env', '.env.local', '.env.production']
        staged_env_files = []
        
        for env_file in env_files:
            if os.path.exists(env_file):
                # git status 확인하여 staged 파일인지 체크
                import subprocess
                try:
                    result = subprocess.run(['git', 'status', '--porcelain', env_file], 
                                         capture_output=True, text=True)
                    if result.stdout.strip():
                        staged_env_files.append(env_file)
                except:
                    pass
        
        return staged_env_files
    
    def generate_security_report(self, issues: List[Dict]) -> str:
        """보안 검사 리포트 생성"""
        if not issues:
            return "보안 검사 통과! 민감한 데이터가 발견되지 않았습니다."
        
        report = f"{len(issues)}개의 보안 이슈 발견!\n\n"
        
        # 타입별로 그룹화
        issues_by_type = {}
        for issue in issues:
            issue_type = issue['type']
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        for issue_type, type_issues in issues_by_type.items():
            report += f"🚨 {issue_type} ({len(type_issues)}개):\n"
            for issue in type_issues:
                report += f"   {issue['file']}:{issue['line']}\n"
                report += f"      {issue['content']}\n"
            report += "\n"
        
        report += "수정 방법:\n"
        report += "   1. 민감한 데이터를 .env 파일로 이동\n"
        report += "   2. .gitignore에 해당 파일 추가\n"
        report += "   3. git reset으로 스테이징 취소\n"
        
        return report

def main():
    """독립 실행용 메인 함수"""
    print("🔒 보안 검사 시작...")
    
    # 검사할 디렉토리
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    checker = SecurityChecker()
    
    # 1. 민감한 데이터 검사
    sensitive_issues = checker.check_directory(directory)
    
    # 2. 환경 변수 파일 검사
    staged_env_files = checker.check_staged_env_files()
    
    # 3. 결과 출력
    if sensitive_issues:
        print(checker.generate_security_report(sensitive_issues))
    
    if staged_env_files:
        print("❌ 환경 변수 파일이 커밋 대상에 포함됨!")
        for file in staged_env_files:
            print(f"   {file}")
        print()
    
    # 4. 최종 결과
    if sensitive_issues or staged_env_files:
        print("git commit 전에 보안 이슈를 해결해주세요!")
        return False
    else:
        print("보안 검사 통과!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)