import requests
import base64
import time
from typing import List, Dict, Optional
from tqdm import tqdm
from config import Config

class GitHubClient:
    def __init__(self):
        self.token = Config.GITHUB_TOKEN
        self.base_url = Config.GITHUB_API_URL
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """GitHub API 요청"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 401:
                print("GitHub 토큰이 유효하지 않습니다.")
                return None
            elif response.status_code == 403:
                print("API 요청 한도를 초과했습니다.")
                return None
            elif response.status_code != 200:
                print(f"API 오류: {response.status_code}")
                return None
                
            return response.json()
        except requests.RequestException as e:
            print(f"네트워크 오류: {e}")
            return None
    
    def get_repo_info(self, repo: str) -> Optional[Dict]:
        """레포지토리 정보 가져오기"""
        print(f"{repo} 레포지토리 정보 조회 중...")
        return self._make_request(f"repos/{repo}")
    
    def get_repo_contents(self, repo: str, path: str = "") -> Optional[List[Dict]]:
        """레포지토리 파일 목록 가져오기"""
        endpoint = f"repos/{repo}/contents/{path}"
        return self._make_request(endpoint)
    
    def get_file_content(self, repo: str, file_path: str) -> Optional[str]:
        """파일 내용 가져오기"""
        content_data = self._make_request(f"repos/{repo}/contents/{file_path}")
        
        if not content_data or content_data.get('type') != 'file':
            return None
        
        try:
            # Base64 디코딩
            content = base64.b64decode(content_data['content']).decode('utf-8')
            return content
        except Exception as e:
            print(f"파일 디코딩 오류 ({file_path}): {e}")
            return None
    
    def get_all_files(self, repo: str, path: str = "") -> List[Dict]:
        """모든 파일 재귀적으로 가져오기"""
        print(f"{repo} 파일 탐색 중...")
        all_files = []
        
        def _recursive_get_files(current_path: str, pbar: tqdm):
            contents = self.get_repo_contents(repo, current_path)
            if not contents:
                return
            
            for item in contents:
                pbar.set_description(f"탐색 중: {item['path']}")
                
                if item['type'] == 'file':
                    # 지원하는 확장자만 필터링
                    if any(item['name'].endswith(ext) for ext in Config.SUPPORTED_EXTENSIONS):
                        all_files.append({
                            'name': item['name'],
                            'path': item['path'],
                            'size': item['size'],
                            'download_url': item['download_url']
                        })
                        pbar.update(1)
                elif item['type'] == 'dir':
                    # 디렉토리면 재귀 호출
                    _recursive_get_files(item['path'], pbar)
                
                # API 속도 제한 방지
                time.sleep(0.1)
        
        with tqdm(desc="파일 스캔", unit="파일") as pbar:
            _recursive_get_files(path, pbar)
        
        print(f"총 {len(all_files)}개 파일 발견")
        return all_files
    
    def get_pull_request(self, repo: str, pr_number: int) -> Optional[Dict]:
        """Pull Request 정보 가져오기"""
        print(f"PR #{pr_number} 정보 조회 중...")
        return self._make_request(f"repos/{repo}/pulls/{pr_number}")
    
    def get_pr_files(self, repo: str, pr_number: int) -> Optional[List[Dict]]:
        """Pull Request에서 변경된 파일들 가져오기"""
        return self._make_request(f"repos/{repo}/pulls/{pr_number}/files")
    
    def test_connection(self) -> bool:
        """GitHub API 연결 테스트"""
        print("GitHub API 연결 테스트 중...")
        user_data = self._make_request("user")
        
        if user_data:
            print(f"GitHub 연결 성공! 사용자: {user_data.get('login')}")
            return True
        else:
            print("GitHub API 연결 실패")
            return False