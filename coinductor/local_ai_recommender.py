from __future__ import annotations

import ctypes
import json
import platform
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class LocalAiRecommendation:
    model: str
    fit: str
    reason: str
    purpose: str = "Text"


@dataclass(frozen=True)
class LocalAiHardwareSnapshot:
    summary: str
    ram_gb: float
    gpu_name: str
    gpu_vram_gb: float
    recommendations: tuple[LocalAiRecommendation, ...]


class LocalAiRecommender:
    def inspect(self) -> LocalAiHardwareSnapshot:
        ram_gb = _system_ram_gb()
        gpu_name, gpu_vram_gb = _gpu_info()
        recommendations = self._recommend(ram_gb, gpu_vram_gb)
        gpu_label = f"{gpu_name} ({gpu_vram_gb:.0f} GB VRAM)" if gpu_name and gpu_vram_gb else gpu_name or "No supported GPU detected"
        summary = f"{platform.system()} detected, {ram_gb:.0f} GB RAM, {gpu_label}."
        return LocalAiHardwareSnapshot(summary, ram_gb, gpu_name, gpu_vram_gb, tuple(recommendations))

    def _recommend(self, ram_gb: float, gpu_vram_gb: float) -> list[LocalAiRecommendation]:
        if gpu_vram_gb >= 15 and ram_gb >= 30:
            return [
                LocalAiRecommendation("qwen3:14b", "Best fit", "Good balance for stronger consumer GPUs with about 16 GB VRAM."),
                LocalAiRecommendation(
                    "qwen3-vl:8b",
                    "Best vision",
                    "Dedicated image model for screenshots; Coinductor uses it only when an image is attached.",
                    "Vision",
                ),
                LocalAiRecommendation("qwen3:8b", "Safer/faster", "Lower memory pressure and faster responses."),
                LocalAiRecommendation("llama3.1:8b", "Alternative", "Popular general-purpose 8B-class local model."),
            ]
        if gpu_vram_gb >= 10:
            return [
                LocalAiRecommendation("qwen3:8b", "Best fit", "Practical 8B-class starting point for mid-range GPUs; use mainly if 14B does not fit."),
                LocalAiRecommendation(
                    "qwen3-vl:8b",
                    "Vision",
                    "Image-capable companion model; close other GPU-heavy apps if memory is tight.",
                    "Vision",
                ),
                LocalAiRecommendation("llama3.1:8b", "Alternative", "General-purpose option with similar hardware expectations."),
                LocalAiRecommendation("qwen3:4b", "Safer/faster", "Lower memory usage if 8B feels slow."),
            ]
        if gpu_vram_gb >= 6 or ram_gb >= 16:
            return [
                LocalAiRecommendation("qwen3:4b", "Basic help only", "Smaller model for limited VRAM or CPU/RAM fallback; not preferred for portfolio analysis."),
                LocalAiRecommendation(
                    "qwen3-vl:4b",
                    "Basic vision",
                    "Smaller image-capable model for screenshots on limited hardware.",
                    "Vision",
                ),
                LocalAiRecommendation("llama3.2:3b", "Basic help only", "Lightweight baseline for setup help; expect weaker reasoning."),
                LocalAiRecommendation("qwen3:8b", "Try carefully", "May work slowly with partial offload on some systems."),
            ]
        return [
            LocalAiRecommendation("llama3.2:3b", "Basic help only", "Small local model for basic app help; not recommended for trading analysis."),
            LocalAiRecommendation(
                "qwen3-vl:2b",
                "Basic vision",
                "Small image model for simple screenshot help; expect weaker interpretation.",
                "Vision",
            ),
            LocalAiRecommendation("qwen3:1.7b", "Basic help only", "Very small fallback for low-memory systems; expect inaccurate or incomplete answers."),
            LocalAiRecommendation("qwen3:4b", "Try carefully", "May be slow without enough memory."),
        ]



# A packaged build has no console, so every subprocess.run here would flash a
# black window on screen. CREATE_NO_WINDOW exists only on Windows.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

def _system_ram_gb() -> float:
    if platform.system().lower() == "windows":
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return status.ullTotalPhys / (1024**3)
    return 0.0


def _gpu_info() -> tuple[str, float]:
    for detector in (_nvidia_gpu, _rocm_gpu, _windows_video_controller):
        name, vram_gb = detector()
        if name:
            return name, vram_gb
    return "", 0.0


def _nvidia_gpu() -> tuple[str, float]:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return "", 0.0
    try:
        completed = subprocess.run(
            [
                executable,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return "", 0.0

    first_line = completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else ""
    if not first_line or "," not in first_line:
        return "", 0.0
    name, memory_mb = [part.strip() for part in first_line.split(",", 1)]
    try:
        return name, float(memory_mb) / 1024
    except ValueError:
        return name, 0.0


def _rocm_gpu() -> tuple[str, float]:
    executable = shutil.which("rocm-smi")
    if not executable:
        return "", 0.0
    try:
        completed = subprocess.run(
            [executable, "--showproductname", "--showmeminfo", "vram", "--json"],
            check=True,
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return "", 0.0
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return "AMD GPU detected by rocm-smi", 0.0
    for details in payload.values():
        if not isinstance(details, dict):
            continue
        name = str(details.get("Card series") or details.get("GPU use") or details.get("Product Name") or "AMD GPU").strip()
        vram_raw = str(details.get("VRAM Total Memory (B)") or details.get("VRAM Total Used Memory (B)") or "").strip()
        try:
            vram_gb = float(vram_raw) / (1024**3) if vram_raw else 0.0
        except ValueError:
            vram_gb = 0.0
        return name, vram_gb
    return "AMD GPU detected by rocm-smi", 0.0


def _windows_video_controller() -> tuple[str, float]:
    if platform.system().lower() != "windows":
        return "", 0.0
    executable = shutil.which("powershell") or shutil.which("pwsh")
    if not executable:
        return "", 0.0
    try:
        completed = subprocess.run(
            [
                executable,
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json -Compress",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return "", 0.0
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return "", 0.0
    controllers = payload if isinstance(payload, list) else [payload]
    candidates: list[tuple[str, float]] = []
    for item in controllers:
        if not isinstance(item, dict):
            continue
        name = str(item.get("Name") or "").strip()
        if not name:
            continue
        adapter_ram = item.get("AdapterRAM") or 0
        try:
            vram_gb = float(adapter_ram) / (1024**3)
        except (TypeError, ValueError):
            vram_gb = 0.0
        if any(marker in name.lower() for marker in ("nvidia", "geforce", "rtx", "radeon", "amd")):
            candidates.append((name, vram_gb))
    if not candidates:
        return "", 0.0
    return max(candidates, key=lambda item: item[1])
