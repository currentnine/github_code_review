 
import os
import json
from datetime import datetime
from typing import Dict, List
from jinja2 import Template
from config import Config

class ReportGenerator:
    def __init__(self):
        self.reports_dir = Config.REPORTS_DIR
        self._ensure_reports_dir()
    
    def _ensure_reports_dir(self):
        """리포트 디렉토리 생성"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def generate_html_report(self, analysis_result: Dict, repo_name: str = "") -> str:
        """HTML 리포트 생성"""
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_repo_name = repo_name.replace("/", "_") if repo_name else "local"
        filename = f"code_review_{safe_repo_name}_{timestamp}.html"
        filepath = os.path.join(self.reports_dir, filename)
        
        # HTML 템플릿
        html_template = self._get_html_template()
        
        # 템플릿 렌더링
        template = Template(html_template)
        html_content = template.render(
            analysis_result=analysis_result,
            repo_name=repo_name,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # 파일 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML 리포트 생성: {filepath}")
        return filepath
    
    def generate_json_report(self, analysis_result: Dict, repo_name: str = "") -> str:
        """JSON 리포트 생성"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_repo_name = repo_name.replace("/", "_") if repo_name else "local"
        filename = f"code_review_{safe_repo_name}_{timestamp}.json"
        filepath = os.path.join(self.reports_dir, filename)
        
        # JSON 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
        
        print(f"JSON 리포트 생성: {filepath}")
        return filepath
    
    def generate_text_summary(self, analysis_result: Dict) -> str:
        """텍스트 요약 생성"""
        summary = analysis_result.get('summary', {})
        
        text = f"""
코드 리뷰 결과 요약
{'='*50}

전체 통계:
   • 분석 파일 수: {summary.get('total_files', 0)}개
   • 평균 점수: {summary.get('average_score', 0)}/10
   • 총 이슈 수: {summary.get('total_issues', 0)}개

"""
        
        # 파일별 결과
        files = analysis_result.get('files', [])
        if files:
            text += "파일별 결과:\n"
            for file_result in files:
                file_path = file_result.get('file_path', 'Unknown')
                score = file_result.get('overall_score', 0)
                issues_count = len(file_result.get('issues', []))
                
                status_emoji = "✅" if score >= 8 else "⚠️" if score >= 6 else "❌"
                text += f"   {status_emoji} {file_path} (점수: {score}/10, 이슈: {issues_count}개)\n"
        
        return text
    
    def print_console_report(self, analysis_result: Dict, repo_name: str = ""):
        """콘솔 리포트 출력"""
        
        print("\n" + "="*60)
        print(f"코드 리뷰 결과: {repo_name or '로컬 프로젝트'}")
        print("="*60)
        
        # 요약 정보
        summary = analysis_result.get('summary', {})
        print(f"\n전체 통계:")
        print(f"   • 분석 파일: {summary.get('total_files', 0)}개")
        print(f"   • 평균 점수: {summary.get('average_score', 0)}/10")
        print(f"   • 총 이슈: {summary.get('total_issues', 0)}개")
        
        # 파일별 상세 결과
        files = analysis_result.get('files', [])
        
        if not files:
            print("\n분석된 파일이 없습니다.")
            return
        
        print(f"\n파일별 상세 결과:")
        print("-"*60)
        
        for i, file_result in enumerate(files, 1):
            file_path = file_result.get('file_path', 'Unknown')
            score = file_result.get('overall_score', 0)
            issues = file_result.get('issues', [])
            improvements = file_result.get('improvements', [])
            positive_points = file_result.get('positive_points', [])
            
            # 파일 헤더
            status_emoji = "✅" if score >= 8 else "⚠️" if score >= 6 else "❌"
            print(f"\n{i}. {status_emoji} {file_path}")
            print(f"   점수: {score}/10")
            
            # 이슈들
            if issues:
                print(f"   이슈 ({len(issues)}개):")
                for issue in issues[:3]:  # 최대 3개만 표시
                    severity_emoji = "🔴" if issue.get('severity') == 'high' else "🟡" if issue.get('severity') == 'medium' else "🟢"
                    print(f"      {severity_emoji} {issue.get('message', 'N/A')}")
                
                if len(issues) > 3:
                    print(f"      ... 외 {len(issues) - 3}개")
            
            # 개선점
            if improvements:
                print(f"   개선점:")
                for improvement in improvements[:2]:  # 최대 2개만 표시
                    print(f"      • {improvement}")
            
            # 긍정적 점
            if positive_points:
                print(f"   좋은 점:")
                for point in positive_points[:2]:  # 최대 2개만 표시
                    print(f"      • {point}")
            
            if i < len(files):
                print("-"*40)
        
        print("\n" + "="*60)
    
    def _get_html_template(self) -> str:
        """HTML 템플릿 반환"""
        return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>코드 리뷰 리포트 - {{ repo_name or '로컬 프로젝트' }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .summary {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            display: block;
        }
        
        .file-result {
            background: white;
            margin-bottom: 25px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .file-header {
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        
        .file-content {
            padding: 25px;
        }
        
        .score {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
        }
        
        .score-high { background: #28a745; }
        .score-medium { background: #ffc107; color: #333; }
        .score-low { background: #dc3545; }
        
        .issues, .improvements, .positive {
            margin: 20px 0;
        }
        
        .issue-item, .improvement-item, .positive-item {
            padding: 10px;
            margin: 8px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        
        .issue-item {
            background: #fff5f5;
            border-left-color: #dc3545;
        }
        
        .improvement-item {
            background: #fff8e1;
            border-left-color: #ffc107;
        }
        
        .positive-item {
            background: #f0f8ff;
            border-left-color: #28a745;
        }
        
        .severity-high { color: #dc3545; font-weight: bold; }
        .severity-medium { color: #ffc107; font-weight: bold; }
        .severity-low { color: #28a745; font-weight: bold; }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            border-top: 1px solid #e9ecef;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 코드 리뷰 리포트</h1>
        <h2>{{ repo_name or '로컬 프로젝트' }}</h2>
        <p>생성 시간: {{ generation_time }}</p>
    </div>

    <div class="summary">
        <h2>📊 전체 요약</h2>
        <div class="stats">
            <div class="stat-card">
                <span class="stat-number">{{ analysis_result.summary.total_files or 0 }}</span>
                <span>분석된 파일</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{ analysis_result.summary.average_score or 0 }}/10</span>
                <span>평균 점수</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{{ analysis_result.summary.total_issues or 0 }}</span>
                <span>총 이슈 수</span>
            </div>
        </div>
    </div>

    {% for file_result in analysis_result.files %}
    <div class="file-result">
        <div class="file-header">
            <h3>📁 {{ file_result.file_path }}</h3>
            {% set score = file_result.overall_score or 0 %}
            {% if score >= 8 %}
                <span class="score score-high">{{ score }}/10 ✅</span>
            {% elif score >= 6 %}
                <span class="score score-medium">{{ score }}/10 ⚠️</span>
            {% else %}
                <span class="score score-low">{{ score }}/10 ❌</span>
            {% endif %}
        </div>
        
        <div class="file-content">
            {% if file_result.issues %}
            <div class="issues">
                <h4>발견된 이슈</h4>
                {% for issue in file_result.issues %}
                <div class="issue-item">
                    <strong class="severity-{{ issue.severity or 'medium' }}">
                        {{ issue.type or 'general' | upper }}
                    </strong>
                    {% if issue.line %}(라인 {{ issue.line }}){% endif %}
                    <br>
                    {{ issue.message or 'N/A' }}
                    {% if issue.suggestion %}
                        <br><em>제안: {{ issue.suggestion }}</em>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}

            {% if file_result.improvements %}
            <div class="improvements">
                <h4>개선 제안</h4>
                {% for improvement in file_result.improvements %}
                <div class="improvement-item">
                    {{ improvement }}
                </div>
                {% endfor %}
            </div>
            {% endif %}

            {% if file_result.positive_points %}
            <div class="positive">
                <h4>좋은 점</h4>
                {% for point in file_result.positive_points %}
                <div class="positive-item">
                    {{ point }}
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>
    </div>
    {% endfor %}

    <div class="footer">
        <p>AI 코드 리뷰 어시스턴트로 생성됨</p>
        <p>이 리포트는 참고용이며, 최종 판단은 개발자가 해야 합니다.</p>
    </div>
</body>
</html>
        """