import time
from typing import Optional
from tqdm import tqdm

class Timer:
    """시간 측정 유틸리티"""
    
    def __init__(self, description: str = ""):
        self.description = description
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """타이머 시작"""
        self.start_time = time.time()
        if self.description:
            print(f"{self.description} 시작...")
        return self
    
    def stop(self):
        """타이머 정지"""
        self.end_time = time.time()
        elapsed = self.elapsed_time()
        if self.description:
            print(f"{self.description} 완료 (소요시간: {elapsed:.1f}초)")
        return elapsed
    
    def elapsed_time(self) -> float:
        """경과 시간 반환"""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

class ProgressTracker:
    """진행상황 추적기"""
    
    def __init__(self, total_steps: int, description: str = "진행"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = time.time()
        self.step_times = []
    
    def step(self, message: str = ""):
        """다음 단계로 진행"""
        self.current_step += 1
        elapsed = time.time() - self.start_time
        self.step_times.append(elapsed)
        
        # 예상 완료 시간 계산
        if self.current_step > 0:
            avg_time_per_step = elapsed / self.current_step
            remaining_steps = self.total_steps - self.current_step
            eta = remaining_steps * avg_time_per_step
        else:
            eta = 0
        
        progress_percent = (self.current_step / self.total_steps) * 100
        
        status = f"[{self.current_step}/{self.total_steps}] {progress_percent:.1f}%"
        if eta > 0:
            status += f" (예상 완료: {eta:.0f}초 후)"
        
        if message:
            status += f" - {message}"
        
        print(f"{status}")
    
    def finish(self):
        """완료 처리"""
        total_time = time.time() - self.start_time
        print(f"{self.description} 완료! 총 소요시간: {total_time:.1f}초")

def format_time(seconds: float) -> str:
    """시간을 읽기 쉬운 형태로 포맷팅"""
    if seconds < 60:
        return f"{seconds:.1f}초"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}분 {secs:.0f}초"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}시간 {minutes}분"

def show_progress_summary(total_files: int, analysis_time: float, avg_score: float):
    """진행 결과 요약 표시"""
    print("\n" + "="*50)
    print("분석 결과 요약")
    print("="*50)
    print(f"분석된 파일: {total_files}개")
    print(f"총 소요시간: {format_time(analysis_time)}")
    print(f"파일당 평균 시간: {analysis_time/total_files:.1f}초" if total_files > 0 else "")
    print(f"평균 점수: {avg_score}/10")
    
    # 성능 평가
    if total_files > 0:
        files_per_minute = (total_files / analysis_time) * 60
        print(f"분석 속도: {files_per_minute:.1f}파일/분")
    
    print("="*50)