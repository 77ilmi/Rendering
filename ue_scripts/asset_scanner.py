"""
asset_scanner.py
================
언리얼 엔진 4 Python API를 사용하여 Content Browser에서
StaticMesh 에셋을 스캔하고 JSON으로 출력합니다.

UE 에디터 내에서 실행되는 스크립트입니다.
Usage (UE Python Console):
    import importlib, sys
    sys.path.insert(0, r"D:/2023011204/렌더링툴/ue_scripts")
    import asset_scanner; importlib.reload(asset_scanner)
    asset_scanner.scan_and_export(r"D:/2023011204/렌더링툴/output/assets.json")
"""

import json
import os

try:
    import unreal
    HAS_UNREAL = True
except ImportError:
    HAS_UNREAL = False
    print("[asset_scanner] 경고: unreal 모듈을 찾을 수 없습니다. UE 에디터 내에서 실행해주세요.")


def get_all_static_meshes(content_paths=None):
    """
    지정된 Content 경로에서 StaticMesh 에셋을 모두 검색합니다.
    
    Args:
        content_paths (list): 검색할 Content 경로 리스트. 기본값: ["/Game/"]
    
    Returns:
        list: 에셋 정보 딕셔너리 리스트
            - package_path: 에셋 패키지 경로 (예: /Game/Props/Chair)
            - name: 에셋 이름
            - object_path: 전체 오브젝트 경로
    """
    if not HAS_UNREAL:
        return []
    
    if content_paths is None:
        content_paths = ["/Game/"]
    
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    
    all_assets = []
    
    for content_path in content_paths:
        # 해당 경로의 모든 StaticMesh 에셋 검색
        filter_ = unreal.ARFilter(
            class_names=["StaticMesh"],
            package_paths=[content_path],
            recursive_paths=True
        )
        
        assets = asset_registry.get_assets(filter_)
        
        for asset_data in assets:
            info = {
                "package_path": str(asset_data.package_path),
                "name": str(asset_data.asset_name),
                "object_path": str(asset_data.object_path),
                "package_name": str(asset_data.package_name)
            }
            all_assets.append(info)
    
    unreal.log(f"[asset_scanner] {len(all_assets)}개 StaticMesh 에셋 발견")
    return all_assets


def scan_and_export(output_json_path, content_paths=None):
    """
    에셋을 스캔하고 결과를 JSON 파일로 저장합니다.
    
    Args:
        output_json_path (str): 출력할 JSON 파일 경로 (절대 경로)
        content_paths (list): 검색 대상 Content 경로 리스트
    
    Returns:
        list: 발견된 에셋 정보 딕셔너리 리스트
    """
    assets = get_all_static_meshes(content_paths)
    
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(assets, f, ensure_ascii=False, indent=2)
    
    if HAS_UNREAL:
        unreal.log(f"[asset_scanner] 에셋 목록 저장 완료: {output_json_path}")
    else:
        print(f"[asset_scanner] 에셋 목록 저장 완료: {output_json_path}")
    
    return assets


if __name__ == "__main__":
    # 직접 실행 시 테스트 더미 데이터 생성
    dummy_assets = [
        {"package_path": "/Game/Props", "name": "SM_Chair", "object_path": "/Game/Props/SM_Chair.SM_Chair", "package_name": "/Game/Props/SM_Chair"},
        {"package_path": "/Game/Props", "name": "SM_Table", "object_path": "/Game/Props/SM_Table.SM_Table", "package_name": "/Game/Props/SM_Table"},
        {"package_path": "/Game/Props", "name": "SM_Lamp",  "object_path": "/Game/Props/SM_Lamp.SM_Lamp",  "package_name": "/Game/Props/SM_Lamp"},
    ]
    print(json.dumps(dummy_assets, ensure_ascii=False, indent=2))
