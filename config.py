import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    # GitHub API 설정
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_API_URL = 'https://api.github.com'
    
    # Ollama 설정
    OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'codellama')
    
    # 지원하는 파일 확장자
    SUPPORTED_EXTENSIONS = os.getenv(
        'SUPPORTED_EXTENSIONS', 
        '.py,.js,.ts,.java,.cpp,.c,.go,.rb,.php,.html,.css'
    ).split(',')
    
    # 분석 설정
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 50000))  # 50KB
    MAX_FILES_PER_ANALYSIS = int(os.getenv('MAX_FILES_PER_ANALYSIS', 20))
    
    # 리포트 설정
    REPORTS_DIR = 'reports'
    
    @classmethod
    def validate(cls):
        """필수 설정값 검증"""
        if not cls.GITHUB_TOKEN:
            print("⚠️  GITHUB_TOKEN이 설정되지 않았습니다.")
            print("   GitHub 개인 액세스 토큰을 .env 파일에 추가해주세요.")
            return False
        return True