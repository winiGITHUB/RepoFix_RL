import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def run_submission(language: str, source_code: str, sample_input: str) -> dict:
    """Run a local submission with a strict timeout; not a security sandbox."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="codereview-") as folder:
        root = Path(folder)
        if language == "python":
            source = root / "main.py"
            source.write_text(source_code, encoding="utf-8")
            command = [sys.executable, "-I", str(source)]
        elif language == "cpp":
            compiler = os.getenv("CPP_COMPILER", "g++")
            compiler_path = shutil.which(compiler)
            if compiler_path is None:
                return {"compile_status": "unavailable", "run_status": "not_run", "stdout": "", "stderr": f"找不到 C++ 编译器 {compiler}。请安装 g++/MinGW 并配置 PATH。", "duration_ms": 0}
            source = root / "main.cpp"
            executable = root / ("main.exe" if os.name == "nt" else "main")
            source.write_text(source_code, encoding="utf-8")
            try:
                compiled = subprocess.run([compiler_path, "-std=c++17", "-O0", "-pipe", str(source), "-o", str(executable)], cwd=root, capture_output=True, text=True, timeout=20, check=False)
            except subprocess.TimeoutExpired:
                return {"compile_status": "timeout", "run_status": "not_run", "stdout": "", "stderr": "编译超时", "duration_ms": int((time.perf_counter()-started)*1000)}
            if compiled.returncode:
                return {"compile_status": "failed", "run_status": "not_run", "stdout": compiled.stdout[-4000:], "stderr": compiled.stderr[-4000:], "duration_ms": int((time.perf_counter()-started)*1000)}
            command = [str(executable)]
        else:
            raise ValueError("language must be python or cpp")
        try:
            completed = subprocess.run(command, cwd=root, input=sample_input, capture_output=True, text=True, timeout=3, check=False)
            return {"compile_status": "passed", "run_status": "completed" if completed.returncode == 0 else "error", "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:] or (f"进程退出码 {completed.returncode}" if completed.returncode else ""), "duration_ms": int((time.perf_counter()-started)*1000)}
        except subprocess.TimeoutExpired as exc:
            return {"compile_status": "passed", "run_status": "timeout", "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "", "stderr": "程序运行超过 3 秒，已终止。", "duration_ms": int((time.perf_counter()-started)*1000)}
