"""
prop_placer.py
==============
언리얼 엔진 4 Python API를 사용하여 씬에 StaticMesh 프랍을 자동 배치합니다.

지원 배치 모드:
  - grid    : N×M 격자 배치
  - random  : 지정 범위 내 랜덤 배치
  - circle  : 원형/방사형 배치
  - single  : 개별 배치 (각 프랍 독립 렌더링용)

Usage (UE Python Console):
    import sys
    sys.path.insert(0, r"D:/2023011204/렌더링툴/ue_scripts")
    import prop_placer
    config = { ... }  # config/default_config.json 내용
    actors = prop_placer.place_props(asset_paths, config)
"""

import math
import random
import json

try:
    import unreal
    HAS_UNREAL = True
except ImportError:
    HAS_UNREAL = False


# ──────────────────────────────────────────────────────────────────────────────
# 내부 헬퍼
# ──────────────────────────────────────────────────────────────────────────────

def _load_static_mesh(object_path):
    """에셋 경로로 StaticMesh 오브젝트를 로드합니다."""
    return unreal.EditorAssetLibrary.load_asset(object_path)


def _spawn_actor(mesh_asset, location, rotation=None, scale=None, label=None):
    """
    씬에 StaticMeshActor를 스폰합니다.

    Args:
        mesh_asset: unreal.StaticMesh 오브젝트
        location: unreal.Vector
        rotation: unreal.Rotator (없으면 (0,0,0))
        scale: unreal.Vector (없으면 (1,1,1))
        label: str — 액터 레이블 (없으면 메시 이름 사용)

    Returns:
        스폰된 unreal.StaticMeshActor
    """
    if rotation is None:
        rotation = unreal.Rotator(0, 0, 0)
    if scale is None:
        scale = unreal.Vector(1, 1, 1)

    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor,
        location,
        rotation
    )
    
    mesh_component = actor.static_mesh_component
    mesh_component.set_static_mesh(mesh_asset)
    actor.set_actor_scale3d(scale)
    
    if label:
        actor.set_actor_label(label)
    
    return actor


def _get_mesh_bounds(mesh_asset):
    """
    StaticMesh의 바운딩 박스 크기를 반환합니다.
    
    Returns:
        (float, float, float): (width_x, width_y, height_z) in cm
    """
    bounds = mesh_asset.get_editor_property("extended_bounds")
    box_extent = bounds.box_extent  # 반지름 값 (전체 크기의 절반)
    return (
        box_extent.x * 2,
        box_extent.y * 2,
        box_extent.z * 2
    )


# ──────────────────────────────────────────────────────────────────────────────
# 배치 모드별 위치 계산
# ──────────────────────────────────────────────────────────────────────────────

def _positions_grid(count, spacing, start_x=0.0, start_y=0.0, cols=None):
    """격자 배치 위치 리스트 반환."""
    if cols is None:
        cols = math.ceil(math.sqrt(count))
    positions = []
    for i in range(count):
        col = i % cols
        row = i // cols
        x = start_x + col * spacing
        y = start_y + row * spacing
        positions.append((x, y))
    return positions


def _positions_random(count, area, seed=None):
    """랜덤 배치 위치 리스트 반환."""
    rng = random.Random(seed)
    half = area / 2.0
    return [(rng.uniform(-half, half), rng.uniform(-half, half)) for _ in range(count)]


def _positions_circle(count, radius):
    """원형 배치 위치 리스트 반환."""
    positions = []
    for i in range(count):
        angle = (2 * math.pi * i) / count
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        positions.append((x, y))
    return positions


def _positions_single(spacing=0.0):
    """단일 배치 — 원점 하나만 반환 (개별 렌더링용)."""
    return [(0.0, 0.0)]


# ──────────────────────────────────────────────────────────────────────────────
# 메인 함수
# ──────────────────────────────────────────────────────────────────────────────

def clear_placed_props(tag="auto_placed_prop"):
    """
    이전에 배치된 프랍 액터들을 씬에서 제거합니다.
    
    Args:
        tag: str — 액터 태그. place_props() 에서 붙인 태그와 동일해야 합니다.
    """
    if not HAS_UNREAL:
        return
    
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    removed = 0
    for actor in all_actors:
        if actor.actor_has_tag(tag):
            unreal.EditorLevelLibrary.destroy_actor(actor)
            removed += 1
    
    unreal.log(f"[prop_placer] {removed}개 이전 프랍 제거 완료")


def place_props(asset_object_paths, config, mode_override=None):
    """
    프랍 에셋들을 씬에 배치합니다.

    Args:
        asset_object_paths (list[str]): UE 에셋 오브젝트 경로 목록
        config (dict): default_config.json 형식의 설정 딕셔너리
        mode_override (str|None): 배치 모드 강제 지정 ("grid"|"random"|"circle"|"single")

    Returns:
        list[unreal.Actor]: 배치된 액터 목록
    """
    if not HAS_UNREAL:
        print("[prop_placer] UE 환경이 아닙니다. 더미 실행.")
        return []

    layout_cfg = config.get("layout", {})
    mode = mode_override or layout_cfg.get("mode", "grid")
    spacing = float(layout_cfg.get("grid_spacing", 300.0))
    cols = int(layout_cfg.get("grid_columns", 5))
    random_area = float(layout_cfg.get("random_area", 2000.0))
    circle_radius = float(layout_cfg.get("circle_radius", 1000.0))
    ground_z = float(layout_cfg.get("ground_z", 0.0))
    do_random_rot = bool(layout_cfg.get("random_rotation", False))
    scale_min = float(layout_cfg.get("random_scale_min", 1.0))
    scale_max = float(layout_cfg.get("random_scale_max", 1.0))

    count = len(asset_object_paths)
    if count == 0:
        unreal.log_warning("[prop_placer] 배치할 에셋이 없습니다.")
        return []

    # ── 위치 계산
    if mode == "grid":
        positions = _positions_grid(count, spacing, cols=cols)
    elif mode == "random":
        positions = _positions_random(count, random_area)
    elif mode == "circle":
        positions = _positions_circle(count, circle_radius)
    elif mode == "single":
        # single 모드는 caller 쪽에서 한 개씩 호출하는 방식 사용
        # 여기서는 모두 원점에 쌓이지 않도록 grid처럼 배치
        positions = _positions_grid(count, spacing, cols=cols)
    else:
        unreal.log_error(f"[prop_placer] 알 수 없는 배치 모드: {mode}")
        return []

    placed_actors = []
    rng = random.Random(42)

    with unreal.ScopedEditorTransaction("Auto Place Props") as _:
        for i, obj_path in enumerate(asset_object_paths):
            mesh = _load_static_mesh(obj_path)
            if mesh is None:
                unreal.log_warning(f"[prop_placer] 로드 실패: {obj_path}")
                continue

            px, py = positions[i] if i < len(positions) else (0.0, 0.0)
            location = unreal.Vector(px, py, ground_z)

            # 회전
            if do_random_rot:
                yaw = rng.uniform(0, 360)
                rotation = unreal.Rotator(0, yaw, 0)
            else:
                rotation = unreal.Rotator(0, 0, 0)

            # 스케일
            if scale_min != scale_max:
                s = rng.uniform(scale_min, scale_max)
            else:
                s = scale_min
            scale = unreal.Vector(s, s, s)

            # 스폰
            mesh_name = obj_path.split(".")[-1]
            actor = _spawn_actor(mesh, location, rotation, scale, label=f"AutoProp_{mesh_name}")
            
            # 식별 태그 추가
            actor.tags.append("auto_placed_prop")
            
            placed_actors.append(actor)
            unreal.log(f"[prop_placer] 배치: {mesh_name} @ ({px:.0f}, {py:.0f})")

    unreal.log(f"[prop_placer] 총 {len(placed_actors)}개 프랍 배치 완료 (모드: {mode})")
    return placed_actors


def place_single_prop(asset_object_path, config, index=0):
    """
    단일 프랍 하나를 씬 원점에 배치합니다 (개별 렌더링용).

    Args:
        asset_object_path (str): UE 에셋 오브젝트 경로
        config (dict): 설정 딕셔너리
        index (int): 그리드 인덱스 (0이면 원점)

    Returns:
        unreal.Actor 또는 None
    """
    actors = place_props([asset_object_path], config, mode_override="single")
    return actors[0] if actors else None
