"""
ue_launcher.py
==============
언리얼 엔진 에디터를 subprocess로 실행하거나,
이미 실행 중인 UE 에디터에 Python 스크립트를 주입합니다.

UE4의 Remote Execution 기능(UDP Multicast)을 통해 Python 명령을 전송합니다.
에디터 Preferences > Python > Enable Remote Execution 활성화 필요.
"""

import os
import sys
import json
import socket
import struct
import threading
import subprocess
import time
import uuid


# ──────────────────────────────────────────────────────────────────────────────
# UE Remote Execution Protocol
# (UE4 source: Engine/Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyRemoteExecution.cpp)
# ──────────────────────────────────────────────────────────────────────────────

MULTICAST_GROUP  = "239.0.0.1"
MULTICAST_PORT   = 6766
COMMAND_PORT     = 6776  # TCP 커맨드 포트
BUFFER_SIZE      = 65536

MSG_TYPE_PING       = "ping"
MSG_TYPE_PONG       = "pong"
MSG_TYPE_OPEN_CONNECTION  = "open_connection"
MSG_TYPE_CLOSE_CONNECTION = "close_connection"
MSG_TYPE_COMMAND    = "command"
MSG_TYPE_COMMAND_RESULT = "command_result"


class UERemoteClient:
    """
    UE4 Remote Execution Python Client.
    에디터가 실행 중이고 Remote Execution이 활성화된 상태에서 사용합니다.
    """
    
    def __init__(self, multicast_group=MULTICAST_GROUP, multicast_port=MULTICAST_PORT,
                 command_port=COMMAND_PORT, timeout=10.0):
        self.multicast_group = multicast_group
        self.multicast_port  = multicast_port
        self.command_port    = command_port
        self.timeout = timeout
        self._node_id = str(uuid.uuid4())
        self._remote_node_id = None
        self._tcp_socket = None

    def _build_message(self, msg_type, data=None):
        msg = {
            "version": 1,
            "magic": "ue_py",
            "type": msg_type,
            "source": self._node_id,
        }
        if data:
            msg.update(data)
        return json.dumps(msg).encode("utf-8")

    def discover(self):
        """UDP Multicast으로 UE 에디터를 검색합니다."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(self.timeout)
        
        # 멀티캐스트 그룹 참여
        group = socket.inet_aton(self.multicast_group)
        mreq  = struct.pack("4sL", group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.bind(("", self.multicast_port))
        
        # Ping 전송
        ping = self._build_message(MSG_TYPE_PING)
        sock.sendto(ping, (self.multicast_group, self.multicast_port))
        
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            msg = json.loads(data.decode("utf-8"))
            if msg.get("type") == MSG_TYPE_PONG:
                self._remote_node_id = msg.get("source")
                return addr[0], msg.get("command_port", self.command_port)
        except socket.timeout:
            return None, None
        finally:
            sock.close()
        
        return None, None

    def connect(self):
        """UE 에디터에 TCP 연결합니다."""
        host, port = self.discover()
        if host is None:
            raise ConnectionError("UE 에디터를 찾을 수 없습니다. Remote Execution이 활성화되었는지 확인하세요.")
        
        self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_socket.settimeout(self.timeout)
        self._tcp_socket.connect((host, port or self.command_port))
        
        # 연결 개방 메시지
        open_msg = self._build_message(MSG_TYPE_OPEN_CONNECTION, {
            "dest": self._remote_node_id
        })
        self._send_tcp(open_msg)
        return True

    def _send_tcp(self, data: bytes):
        length = struct.pack(">I", len(data))
        self._tcp_socket.sendall(length + data)

    def _recv_tcp(self) -> dict:
        raw_len = self._recv_all(4)
        length  = struct.unpack(">I", raw_len)[0]
        raw     = self._recv_all(length)
        return json.loads(raw.decode("utf-8"))

    def _recv_all(self, n: int) -> bytes:
        data = b""
        while len(data) < n:
            chunk = self._tcp_socket.recv(n - len(data))
            if not chunk:
                raise ConnectionError("연결이 끊어졌습니다.")
            data += chunk
        return data

    def run_command(self, python_code: str, exec_mode="ExecuteFile") -> dict:
        """
        UE 에디터에서 Python 코드를 실행합니다.
        
        Args:
            python_code (str): 실행할 Python 코드 또는 파일 경로
            exec_mode (str): "ExecuteStatement" | "ExecuteFile" | "EvaluateStatement"

        Returns:
            dict: {"success": bool, "result": str, "output": str}
        """
        cmd_msg = self._build_message(MSG_TYPE_COMMAND, {
            "dest": self._remote_node_id,
            "command": python_code,
            "unattended": True,
            "exec_mode": exec_mode,
        })
        self._send_tcp(cmd_msg)
        
        response = self._recv_tcp()
        return {
            "success": response.get("success", False),
            "result":  response.get("result", ""),
            "output":  response.get("output", ""),
        }

    def close(self):
        """TCP 연결을 닫습니다."""
        if self._tcp_socket:
            try:
                close_msg = self._build_message(MSG_TYPE_CLOSE_CONNECTION, {
                    "dest": self._remote_node_id
                })
                self._send_tcp(close_msg)
            except Exception:
                pass
            self._tcp_socket.close()
            self._tcp_socket = None


# ──────────────────────────────────────────────────────────────────────────────
# 고수준 API
# ──────────────────────────────────────────────────────────────────────────────

def execute_pipeline_in_ue(config: dict, ue_scripts_dir: str) -> bool:
    """
    UE 에디터에 원격으로 파이프라인 스크립트를 실행합니다.
    
    Args:
        config (dict): 설정 딕셔너리
        ue_scripts_dir (str): ue_scripts 폴더 절대 경로

    Returns:
        bool: 전송 성공 여부
    """
    import tempfile
    
    # 임시 config 파일 저장
    config_path = os.path.join(
        config.get("output_path", tempfile.gettempdir()),
        "session_config.json"
    )
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False)
    
    # 실행 코드 구성
    code = f"""
import sys
sys.path.insert(0, r"{ue_scripts_dir.replace(chr(92), "/")}")
import importlib, run_all
importlib.reload(run_all)
run_all.run(config_path=r"{config_path.replace(chr(92), "/")}")
"""
    
    client = UERemoteClient()
    try:
        client.connect()
        result = client.run_command(code.strip(), exec_mode="ExecuteStatement")
        return result.get("success", False)
    except ConnectionError as e:
        print(f"[ue_launcher] 연결 오류: {e}")
        return False
    finally:
        client.close()


def launch_ue_editor(ue_editor_path: str, uproject_path: str, python_script_path: str = None) -> subprocess.Popen:
    """
    UE4Editor.exe를 subprocess로 실행합니다.
    
    Args:
        ue_editor_path (str): UE4Editor.exe 절대 경로
        uproject_path (str): .uproject 파일 절대 경로
        python_script_path (str|None): 실행할 Python 스크립트 경로
    
    Returns:
        subprocess.Popen
    """
    cmd = [ue_editor_path, uproject_path]
    
    if python_script_path:
        cmd += [f'-ExecutePythonScript="{python_script_path}"']
    
    cmd += ["-log", "-stdout"]
    
    print(f"[ue_launcher] UE 에디터 실행: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc


def is_ue_remote_available(timeout=3.0) -> bool:
    """UE Remote Execution이 사용 가능한지 확인합니다."""
    client = UERemoteClient(timeout=timeout)
    host, _ = client.discover()
    return host is not None
