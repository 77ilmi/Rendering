"""
auto_renderer.py
================
언리얼 엔진 4 Python API를 사용하여 씬을 렌더링합니다.

지원 렌더링 방식:
  1. High Resolution Screenshot (hires)  — 빠르고 간단
  2. Movie Render Queue (mrq)            — 고품질, 다양한 패스 지원

Usage (UE Python Console):
    import sys
    sys.path.insert(0, r"D:/2023011204/렌더링툴/ue_scripts")
    import auto_renderer
    auto_renderer.render_hires(output_path="D:/output/render_001.png", config=config)
"""

import os
import json
import math
import time

try:
    import unreal
    HAS_UNREAL = True
except ImportError:
    HAS_UNREAL = False


# ──────────────────────────────────────────────────────────────────────────────
# 카메라 설정
# ──────────────────────────────────────────────────────────────────────────────

CAMERA_PRESETS = {
    "front":       {"pitch": 0,   "yaw": 0,   "distance_mult": 1.2},
    "side":        {"pitch": 0,   "yaw": 90,  "distance_mult": 1.2},
    "top":         {"pitch": -89, "yaw": 0,   "distance_mult": 1.5},
    "isometric":   {"pitch": -45, "yaw": 45,  "distance_mult": 1.5},
    "perspective": {"pitch": -30, "yaw": 30,  "distance_mult": 1.4},
    "custom":      {"pitch": -45, "yaw": 45,  "distance_mult": 1.5},
}


def _get_scene_bounds(actors):
    """
    배치된 액터들의 씬 바운드 박스를 계산합니다.
    
    Returns:
        (center: unreal.Vector, extent: unreal.Vector)
    """
    if not actors:
        return unreal.Vector(0, 0, 0), unreal.Vector(500, 500, 500)
    
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")
    
    for actor in actors:
        origin, extent = actor.get_actor_bounds(False)
        min_x = min(min_x, origin.x - extent.x)
        min_y = min(min_y, origin.y - extent.y)
        min_z = min(min_z, origin.z - extent.z)
        max_x = max(max_x, origin.x + extent.x)
        max_y = max(max_y, origin.y + extent.y)
        max_z = max(max_z, origin.z + extent.z)
    
    center = unreal.Vector(
        (min_x + max_x) / 2,
        (min_y + max_y) / 2,
        (min_z + max_z) / 2
    )
    extent = unreal.Vector(
        (max_x - min_x) / 2,
        (max_y - min_y) / 2,
        (max_z - min_z) / 2
    )
    return center, extent


def _calculate_camera_transform(actors, config):
    """
    씬 바운드에 맞는 최적 카메라 위치/회전을 계산합니다.
    
    Returns:
        (location: unreal.Vector, rotation: unreal.Rotator)
    """
    cam_cfg = config.get("camera", {})
    preset_name = cam_cfg.get("preset", "isometric")
    preset = CAMERA_PRESETS.get(preset_name, CAMERA_PRESETS["isometric"])
    
    pitch = cam_cfg.get("angle_pitch", preset["pitch"])
    yaw   = cam_cfg.get("angle_yaw",   preset["yaw"])
    dist_mult = float(cam_cfg.get("distance_multiplier", preset["distance_mult"]))
    height_offset = float(cam_cfg.get("height_offset", 0.0))
    
    center, extent = _get_scene_bounds(actors)
    
    # 씬 크기 기반 거리 계산
    max_extent = max(extent.x, extent.y, extent.z)
    distance = max_extent * 3.0 * dist_mult
    
    # 카메라 방향 벡터 계산
    pitch_rad = math.radians(pitch)
    yaw_rad   = math.radians(yaw)
    
    dx = distance * math.cos(pitch_rad) * math.cos(yaw_rad)
    dy = distance * math.cos(pitch_rad) * math.sin(yaw_rad)
    dz = distance * math.sin(-pitch_rad)
    
    location = unreal.Vector(
        center.x - dx,
        center.y - dy,
        center.z + dz + height_offset
    )
    rotation = unreal.Rotator(pitch, yaw + 180, 0)
    
    return location, rotation


def setup_viewport_camera(actors, config):
    """
    에디터 뷰포트 카메라를 씬에 맞게 이동시킵니다.
    
    Args:
        actors (list): 배치된 액터 목록
        config (dict): 설정 딕셔너리
    """
    if not HAS_UNREAL:
        return
    
    location, rotation = _calculate_camera_transform(actors, config)
    
    # 에디터 뷰포트 카메라 이동
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(location, rotation)
    unreal.log(f"[auto_renderer] 카메라 이동: {location} / {rotation}")


# ──────────────────────────────────────────────────────────────────────────────
# 렌더링: High Resolution Screenshot
# ──────────────────────────────────────────────────────────────────────────────

def render_hires(output_path, actors, config):
    """
    High Resolution Screenshot으로 씬을 렌더링합니다.
    
    Args:
        output_path (str): 저장할 이미지 파일 경로 (절대 경로, .png)
        actors (list): 씬에 배치된 액터 목록 (카메라 자동 맞춤용)
        config (dict): 설정 딕셔너리

    Returns:
        bool: 성공 여부
    """
    if not HAS_UNREAL:
        print(f"[auto_renderer] [HiRes] 더미 렌더링: {output_path}")
        return True

    render_cfg = config.get("render", {})
    multiplier = int(render_cfg.get("hires_multiplier", 2))
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 카메라 배치
    setup_viewport_camera(actors, config)
    
    # 렌더링 명령 실행
    # UE4 콘솔 커맨드로 High Resolution Screenshot 실행
    filename_no_ext = os.path.splitext(os.path.basename(output_path))[0]
    output_dir = os.path.dirname(output_path)
    
    cmd = f"HighResShot {multiplier} filename={output_path}"
    unreal.SystemLibrary.execute_console_command(
        unreal.EditorLevelLibrary.get_editor_world(),
        cmd
    )
    
    unreal.log(f"[auto_renderer] HiRes 렌더링 요청: {output_path}")
    
    # 렌더링 완료 대기 (파일 생성 감지)
    timeout = 30
    start = time.time()
    while not os.path.exists(output_path) and (time.time() - start) < timeout:
        time.sleep(0.5)
    
    success = os.path.exists(output_path)
    if success:
        unreal.log(f"[auto_renderer] 렌더링 완료: {output_path}")
    else:
        unreal.log_warning(f"[auto_renderer] 렌더링 타임아웃: {output_path}")
    
    return success


# ──────────────────────────────────────────────────────────────────────────────
# 렌더링: Movie Render Queue
# ──────────────────────────────────────────────────────────────────────────────

def render_mrq(output_dir, output_filename, actors, config):
    """
    Movie Render Queue를 사용하여 고품질 렌더링을 수행합니다.
    UE4.27 기준 MoviePipelineEditorLibrary API를 사용합니다.
    
    Args:
        output_dir (str): 렌더링 결과물을 저장할 디렉토리 (절대 경로)
        output_filename (str): 파일 이름 (확장자 없이)
        actors (list): 배치된 액터 목록
        config (dict): 설정 딕셔너리

    Returns:
        bool: 성공 여부
    """
    if not HAS_UNREAL:
        print(f"[auto_renderer] [MRQ] 더미 렌더링: {output_dir}/{output_filename}")
        return True

    render_cfg = config.get("render", {})
    width  = int(render_cfg.get("resolution_width",  1920))
    height = int(render_cfg.get("resolution_height", 1080))
    mrq_preset_path = render_cfg.get("mrq_preset_path", "")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 카메라 배치 후 CineCameraActor 생성
    cam_location, cam_rotation = _calculate_camera_transform(actors, config)
    
    cam_cfg = config.get("camera", {})
    fov = float(cam_cfg.get("fov", 60.0))
    
    # CineCameraActor 스폰
    cine_camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CineCameraActor,
        cam_location,
        cam_rotation
    )
    cine_camera.set_actor_label("AutoRenderCamera")
    cine_camera.camera_component.set_field_of_view(fov)
    
    try:
        # Level Sequence 생성
        level_seq_path = "/Game/Temp/AutoRenderSeq"
        level_seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "AutoRenderSeq",
            "/Game/Temp",
            unreal.LevelSequence,
            unreal.LevelSequenceFactoryNew()
        )
        
        # Movie Pipeline Queue 생성 및 실행
        queue = unreal.MoviePipelineQueue()
        job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
        job.sequence = unreal.SoftObjectPath(level_seq_path)
        job.map = unreal.SoftObjectPath(unreal.EditorLevelLibrary.get_editor_world().get_path_name())
        
        # 출력 설정
        job.get_configuration().find_or_add_setting_by_class(
            unreal.MoviePipelineOutputSetting
        )
        output_settings = job.get_configuration().find_or_add_setting_by_class(
            unreal.MoviePipelineOutputSetting
        )
        output_settings.output_directory = unreal.DirectoryPath(output_dir)
        output_settings.file_name_format  = output_filename
        output_settings.output_resolution  = unreal.IntPoint(width, height)
        
        # PNG 출력 설정
        png_output = job.get_configuration().find_or_add_setting_by_class(
            unreal.MoviePipelineImageSequenceOutput_PNG
        )
        
        # 렌더링 실행
        executor = unreal.MoviePipelinePIEExecutor()
        executor.execute(queue)
        
        unreal.log(f"[auto_renderer] MRQ 렌더링 시작: {output_dir}/{output_filename}")
        return True
        
    except Exception as e:
        unreal.log_error(f"[auto_renderer] MRQ 렌더링 실패: {e}")
        return False
    finally:
        # 임시 카메라 제거
        unreal.EditorLevelLibrary.destroy_actor(cine_camera)


# ──────────────────────────────────────────────────────────────────────────────
# 통합 렌더링 함수
# ──────────────────────────────────────────────────────────────────────────────

def render(output_path, actors, config, method=None):
    """
    설정에 따라 렌더링 방식을 선택하여 실행합니다.
    
    Args:
        output_path (str): 출력 파일 경로 (절대 경로)
        actors (list): 배치된 액터 목록
        config (dict): 설정 딕셔너리
        method (str|None): "hires" 또는 "mrq". None이면 config에서 읽음.

    Returns:
        bool: 성공 여부
    """
    render_cfg = config.get("render", {})
    selected_method = method or render_cfg.get("method", "hires")
    
    if selected_method == "hires":
        return render_hires(output_path, actors, config)
    elif selected_method == "mrq":
        output_dir = os.path.dirname(output_path)
        filename   = os.path.splitext(os.path.basename(output_path))[0]
        return render_mrq(output_dir, filename, actors, config)
    else:
        if HAS_UNREAL:
            unreal.log_error(f"[auto_renderer] 알 수 없는 렌더링 방식: {selected_method}")
        return False
