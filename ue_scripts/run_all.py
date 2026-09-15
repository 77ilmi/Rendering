"""
run_all.py
==========
전체 파이프라인 진입점입니다.
GUI 또는 커맨드라인에서 JSON config를 받아 아래 순서로 실행합니다:

  1. 에셋 스캔 (asset_scanner)
  2. 이전 프랍 제거 (prop_placer.clear_placed_props)
  3. 프랍 배치 (prop_placer.place_props)
  4. 렌더링 (auto_renderer.render)
  5. 결과 JSON 저장

Usage (UE Python Console):
    import sys, json
    sys.path.insert(0, r"D:/2023011204/렌더링툴/ue_scripts")
    import run_all
    run_all.run(config_path=r"D:/2023011204/렌더링툴/config/session_config.json")

커맨드라인 Usage:
    # UE4Editor.exe로 Python 스크립트 실행 시:
    -ExecutePythonScript="D:/2023011204/렌더링툴/ue_scripts/run_all.py D:/2023011204/렌더링툴/config/session_config.json"
"""

import os
import sys
import json
import time
import datetime

try:
    import unreal
    HAS_UNREAL = True
except ImportError:
    HAS_UNREAL = False

# 스크립트 디렉토리를 경로에 추가
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import asset_scanner
import prop_placer
import auto_renderer


# ──────────────────────────────────────────────────────────────────────────────
# 진행 상태 콜백
# ──────────────────────────────────────────────────────────────────────────────

class ProgressReporter:
    """렌더링 진행 상태를 JSON 파일에 기록합니다 (GUI가 폴링)."""
    
    def __init__(self, status_file_path):
        self.status_file = status_file_path
        self._update("idle", 0, "대기 중")
    
    def _update(self, state, progress, message, extra=None):
        data = {
            "state": state,
            "progress": progress,  # 0.0 ~ 1.0
            "message": message,
            "timestamp": datetime.datetime.now().isoformat(),
            **(extra or {})
        }
        try:
            os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def scanning(self):      self._update("scanning",   0.1, "에셋 스캔 중...")
    def placing(self, i, total): 
        self._update("placing", 0.1 + 0.3 * (i/max(total,1)), f"프랍 배치 중... ({i}/{total})")
    def rendering(self, i, total, name=""):
        self._update("rendering", 0.4 + 0.55 * (i/max(total,1)), f"렌더링 중... {name} ({i}/{total})")
    def done(self, results):
        self._update("done", 1.0, "완료!", {"results": results})
    def error(self, msg):
        self._update("error", 0.0, f"오류: {msg}")


# ──────────────────────────────────────────────────────────────────────────────
# 메인 파이프라인
# ──────────────────────────────────────────────────────────────────────────────

def run(config_path=None, config=None):
    """
    전체 배치 + 렌더링 파이프라인을 실행합니다.
    
    Args:
        config_path (str|None): session_config.json 파일 경로. config가 있으면 무시.
        config (dict|None): 설정 딕셔너리. config_path보다 우선.

    Returns:
        dict: 실행 결과
            - success (bool)
            - rendered_files (list[str]): 렌더링된 파일 경로 목록
            - errors (list[str])
    """
    # ── 설정 로드
    if config is None:
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(_SCRIPT_DIR)),
                "config", "default_config.json"
            )
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    
    output_path = config.get("output_path", "")
    if not output_path:
        raise ValueError("config에 output_path가 설정되지 않았습니다.")
    
    # 상태 파일 경로
    status_file = os.path.join(output_path, ".render_status.json")
    reporter = ProgressReporter(status_file)
    
    rendered_files = []
    errors = []
    
    try:
        # ── 1. 에셋 스캔
        reporter.scanning()
        
        scan_cfg = config.get("scan", {})
        content_paths = scan_cfg.get("content_paths", ["/Game/"])
        
        # GUI에서 선택된 에셋 목록이 있으면 사용, 없으면 전체 스캔
        selected_assets = config.get("selected_assets", None)
        
        if selected_assets:
            assets = selected_assets  # [{"object_path": "...", "name": "..."}, ...]
        else:
            assets_json_path = os.path.join(output_path, "assets.json")
            assets = asset_scanner.scan_and_export(assets_json_path, content_paths)
        
        if not assets:
            reporter.error("에셋을 찾을 수 없습니다.")
            return {"success": False, "rendered_files": [], "errors": ["에셋 없음"]}
        
        asset_paths = [a["object_path"] for a in assets]
        
        # ── 2. 이전 프랍 제거
        prop_placer.clear_placed_props()
        
        render_cfg = config.get("render", {})
        do_per_prop = bool(render_cfg.get("per_prop", True))
        do_group    = bool(render_cfg.get("group",    False))
        
        # ── 3a. 개별 렌더링 (프랍 하나씩)
        if do_per_prop:
            for i, asset in enumerate(assets):
                obj_path = asset["object_path"]
                name     = asset.get("name", f"prop_{i:03d}")
                
                reporter.placing(i + 1, len(assets))
                
                # 기존 프랍 제거
                prop_placer.clear_placed_props()
                
                # 단일 프랍 배치
                actor = prop_placer.place_single_prop(obj_path, config)
                
                reporter.rendering(i + 1, len(assets), name)
                
                # 렌더링
                out_file = os.path.join(output_path, f"{name}.png")
                success  = auto_renderer.render(out_file, [actor] if actor else [], config)
                
                if success:
                    rendered_files.append(out_file)
                else:
                    errors.append(f"렌더링 실패: {name}")
        
        # ── 3b. 그룹 렌더링 (모든 프랍 함께)
        if do_group:
            prop_placer.clear_placed_props()
            
            reporter.placing(0, len(asset_paths))
            actors = prop_placer.place_props(asset_paths, config)
            
            reporter.rendering(0, 1, "group")
            out_file = os.path.join(output_path, "group_render.png")
            success  = auto_renderer.render(out_file, actors, config)
            
            if success:
                rendered_files.append(out_file)
            else:
                errors.append("그룹 렌더링 실패")
        
        # ── 4. 결과 저장
        result = {
            "success": len(errors) == 0,
            "rendered_files": rendered_files,
            "errors": errors
        }
        
        result_json_path = os.path.join(output_path, "render_result.json")
        with open(result_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        reporter.done(rendered_files)
        
        if HAS_UNREAL:
            unreal.log(f"[run_all] 파이프라인 완료. 렌더링: {len(rendered_files)}개, 오류: {len(errors)}개")
        else:
            print(f"[run_all] 파이프라인 완료. 렌더링: {len(rendered_files)}개")
        
        return result
    
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        reporter.error(str(e))
        if HAS_UNREAL:
            unreal.log_error(f"[run_all] 파이프라인 오류:\n{err_msg}")
        else:
            print(f"[run_all] 오류:\n{err_msg}")
        return {"success": False, "rendered_files": rendered_files, "errors": [str(e)]}


# ──────────────────────────────────────────────────────────────────────────────
# 커맨드라인 진입점
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # UE4Editor.exe -ExecutePythonScript="run_all.py config.json" 형태로 실행됨
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else None
    result = run(config_path=cfg_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
