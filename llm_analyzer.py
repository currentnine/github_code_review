import requests
import json
import time
from typing import Dict, List, Optional
from tqdm import tqdm
from config import Config

class LLMAnalyzer:
    def __init__(self):
        self.ollama_url = Config.OLLAMA_URL
        self.model = Config.OLLAMA_MODEL
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Ollama API 호출"""
        try:
            url = f"{self.ollama_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 일관된 분석을 위해 낮게 설정
                    "top_p": 0.9
                }
            }
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                print(f"Ollama API 오류: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"Ollama 연결 오류: {e}")
            print("Ollama가 실행 중인지 확인해주세요: ollama serve")
            return None
    
    def analyze_code(self, code: str, file_path: str, language: str = "", progress_bar: tqdm = None) -> Dict:
        """단일 파일 코드 분석"""
        if progress_bar:
            progress_bar.set_description(f"분석 중: {file_path}")
        
        # 언어 자동 감지
        if not language:
            language = self._detect_language(file_path)
        
        start_time = time.time()
        
        prompt = f"""다음 {language} 코드를 분석해서 JSON 형태로 결과를 반환해주세요:

파일: {file_path}

코드:
```{language}
{code}
```

다음 형식으로 분석 결과를 반환해주세요:
{{
    "overall_score": 7.5,
    "issues": [
        {{
            "type": "bug",
            "severity": "high",
            "line": 15,
            "message": "잠재적 null pointer exception",
            "suggestion": "null 체크 추가 필요"
        }}
    ],
    "improvements": [
        "변수명을 더 명확하게 수정",
        "주석 추가 필요"
    ],
    "positive_points": [
        "코드 구조가 깔끔함",
        "에러 처리가 적절함"
    ]
}}

분석할 항목:
- 버그 가능성
- 보안 취약점
- 성능 이슈
- 코드 스타일
- 가독성
- 유지보수성
"""
        
        response = self._call_ollama(prompt)
        
        analysis_time = time.time() - start_time
        
        if progress_bar:
            progress_bar.set_postfix({"시간": f"{analysis_time:.1f}s"})
        
        if response:
            try:
                # JSON 파싱 시도
                result = self._parse_json_response(response)
                return result
            except Exception as e:
                if progress_bar:
                    progress_bar.write(f"분석 결과 파싱 오류 ({file_path}): {e}")
                return self._create_fallback_result(response)
        
        return self._create_empty_result()
    
    def analyze_multiple_files(self, files: List[Dict]) -> Dict:
        """여러 파일 통합 분석"""
        total_files = len(files[:Config.MAX_FILES_PER_ANALYSIS])
        print(f"AI 코드 분석 시작: {total_files}개 파일")
        
        results = []
        total_score = 0
        start_time = time.time()
        
        with tqdm(total=total_files, desc="코드 분석", unit="파일") as pbar:
            for file_info in files[:Config.MAX_FILES_PER_ANALYSIS]:
                if file_info.get('content'):
                    result = self.analyze_code(
                        file_info['content'], 
                        file_info['path'],
                        progress_bar=pbar
                    )
                    result['file_path'] = file_info['path']
                    results.append(result)
                    total_score += result.get('overall_score', 5.0)
                    
                    pbar.update(1)
                    
                    # 간격 추가 (LLM 서버 부하 방지)
                    time.sleep(0.5)
        
        total_time = time.time() - start_time
        
        # 전체 통계 계산
        avg_score = total_score / len(results) if results else 0
        total_issues = sum(len(r.get('issues', [])) for r in results)
        
        print(f"분석 완료! 소요시간: {total_time:.1f}초")
        
        return {
            'summary': {
                'total_files': len(results),
                'average_score': round(avg_score, 1),
                'total_issues': total_issues,
                'analysis_time': round(total_time, 1),
                'analysis_timestamp': self._get_timestamp()
            },
            'files': results
        }
    
    def _detect_language(self, file_path: str) -> str:
        """파일 확장자로 언어 감지"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
            '.html': 'html',
            '.css': 'css'
        }
        
        for ext, lang in extension_map.items():
            if file_path.endswith(ext):
                return lang
        
        return 'text'
    
    def _parse_json_response(self, response: str) -> Dict:
        """LLM 응답에서 JSON 추출"""
        # JSON 블록 찾기
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            json_str = response[start_idx:end_idx+1]
            return json.loads(json_str)
        
        raise ValueError("JSON 형식을 찾을 수 없음")
    
    def _create_fallback_result(self, response: str) -> Dict:
        """JSON 파싱 실패 시 기본 결과"""
        return {
            "overall_score": 5.0,
            "issues": [],
            "improvements": ["LLM 응답 파싱 실패"],
            "positive_points": [],
            "raw_response": response[:500]  # 처음 500자만 저장
        }
    
    def _create_empty_result(self) -> Dict:
        """빈 결과 생성"""
        return {
            "overall_score": 0.0,
            "issues": [],
            "improvements": ["분석 실패"],
            "positive_points": [],
            "error": "LLM 분석 실패"
        }
    
    def _get_timestamp(self) -> str:
        """현재 시간 반환"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def test_connection(self) -> bool:
        """Ollama 연결 테스트"""
        print("Ollama 연결 테스트 중...")
        
        test_response = self._call_ollama("Hello, are you working?")
        
        if test_response:
            print("Ollama 연결 성공!")
            return True
        else:
            print("Ollama 연결 실패")
            print("다음 명령어로 Ollama를 시작해보세요:")
            print("   ollama serve")
            print(f"   ollama pull {self.model}")
            return False