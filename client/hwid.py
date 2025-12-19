from __future__ import annotations
import hashlib
import json
import os
import re
import subprocess
import uuid
from typing import Dict, List, Tuple

def _run_powershell(cmd: str) -> str:
    # Windows에서만 기대. 실패하면 빈 문자열 반환.
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=4,
        )
        return (completed.stdout or "").strip()
    except Exception:
        return ""

def _safe_first_line(s: str) -> str:
    return (s.splitlines()[0].strip() if s else "")

def _get_cpu_id() -> str:
    # Win32_Processor.ProcessorId
    out = _run_powershell("(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty ProcessorId)")
    return _safe_first_line(out)

def _get_bios_serial() -> str:
    out = _run_powershell("(Get-CimInstance Win32_BIOS | Select-Object -First 1 -ExpandProperty SerialNumber)")
    return _safe_first_line(out)

def _get_disk_serial() -> str:
    # PhysicalMedia SerialNumber가 비어있는 환경이 있어 DiskDrive SerialNumber도 시도
    out = _run_powershell("(Get-CimInstance Win32_PhysicalMedia | Select-Object -First 1 -ExpandProperty SerialNumber)")
    v = _safe_first_line(out)
    if v:
        return v
    out2 = _run_powershell("(Get-CimInstance Win32_DiskDrive | Select-Object -First 1 -ExpandProperty SerialNumber)")
    return _safe_first_line(out2)

def _get_machine_guid() -> str:
    # HKLM:\SOFTWARE\Microsoft\Cryptography\MachineGuid
    out = _run_powershell("(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Cryptography' -Name MachineGuid).MachineGuid")
    return _safe_first_line(out)

def _get_mac_address() -> str:
    # uuid.getnode(): MAC or random if not available
    mac = uuid.getnode()
    return f"{mac:012x}"

def build_hwid_components() -> Dict[str, str]:
    # 가능한 것들을 모아 “변화에 덜 민감한” 조합을 구성
    # (CPU/BIOS/Disk는 교체 시 바뀔 수 있음. 정책에 따라 가중치/허용 범위 조정 가능)
    return {
        "cpu": _get_cpu_id(),
        "bios": _get_bios_serial(),
        "disk": _get_disk_serial(),
        "guid": _get_machine_guid(),
        "mac": _get_mac_address(),
    }

def hwid_hash_sha256() -> str:
    comp = build_hwid_components()
    # 빈 값 제거 후 정규화
    items = [f"{k}={comp[k].strip().lower()}" for k in sorted(comp.keys()) if comp[k]]
    raw = "|".join(items).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

if __name__ == "__main__":
    print("HWID components:", json.dumps(build_hwid_components(), indent=2))
    print("HWID hash:", hwid_hash_sha256())
