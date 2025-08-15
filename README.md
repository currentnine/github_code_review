# AI 코드 리뷰 어시스턴트

GitHub 레포지토리와 로컬 프로젝트를 AI로 자동 분석하여 코드 품질을 평가하고 개선점을 제안하는 도구입니다.

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# 아나콘다 환경 생성
conda create -n code-review python=3.10
conda activate code-review

# 의존성 설치
pip install -r requirements.txt
```

### 2. API 설정
1. **GitHub 토큰 발급**
   - GitHub → Settings → Developer settings → Personal access tokens
   - `repo` 권한으로 토큰 생성

2. **Ollama 설치**
   - https://ollama.ai/download 에서 다운로드
   - 모델 설치: `ollama pull codellama`

3. **환경 변수 설정**
```bash
# .env 파일 생성
cp .env.example .env
# .env 파일에서 GITHUB_TOKEN 입력
```

### 3. 연결 테스트
```bash
python main.py --test
```

## 📖 사용법

### GitHub 레포지토리 분석
```bash
python main.py --repo microsoft/vscode
python main.py --repo facebook/react --max-files 10
```

### Pull Request 분석
```bash
python main.py --pr facebook/react/12345
```

### 로컬 프로젝트 분석
```bash
python