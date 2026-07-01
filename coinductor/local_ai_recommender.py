from __future__ import annotations

import ctypes
import platform
import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class LocalAiRecommendation:
    model: str
    fit: str
    reason: str


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
        gpu_name, gpu_vram_gb = _nvidia_gpu()
        recommendations = self._recommend(ram_gb, gpu_vram_gb)
        gpu_label = f"{gpu_name} ({gpu_vram_gb:.0f} GB VRAM)" if gpu_name else "No NVIDIA GPU detected"
        summary = f"{platform.system()} detected, {ram_gb:.0f} GB RAM, {gpu_label}."
        return LocalAiHardwareSnapshot(summary, ram_gb, gpu_name, gpu_vram_gb, tuple(recommendations))

    def _recommend(self, ram_gb: float, gpu_vram_gb: float) -> list[LocalAiRecommendation]:
        if gpu_vram_gb >= 15 and ram_gb >= 30:
            return [
                LocalAiRecommendation("qwen3:14b", "Best fit", "Good balance for stronger consumer GPUs with about 16 GB VRAM."),
                LocalAiRecommendation("qwen3:8b", "Safer/faster", "Lower memory pressure and faster responses."),
                LocalAiRecommendation("llama3.1:8b", "Alternative", "Popular general-purpose 8B-class local model."),
            ]
        if gpu_vram_gb >= 10:
            return [
                LocalAiRecommendation("qwen3:8b", "Best fit", "Practical 8B-class starting point for mid-range GPUs."),
                LocalAiRecommendation("llama3.1:8b", "Alternative", "General-purpose option with similar hardware expectations."),
                LocalAiRecommendation("qwen3:4b", "Safer/faster", "Lower memory usage if 8B feels slow."),
            ]
        if gpu_vram_gb >= 6 or ram_gb >= 16:
            return [
                LocalAiRecommendation("qwen3:4b", "Best fit", "Smaller model for limited VRAM or CPU/RAM fallback."),
                LocalAiRecommendation("llama3.2:3b", "Safer/faster", "Good lightweight baseline for setup help and summaries."),
                LocalAiRecommendation("qwen3:8b", "Try carefully", "May work slowly with partial offload on some systems."),
            ]
        return [
            LocalAiRecommendation("llama3.2:3b", "Best fit", "Small local model for basic app help."),
            LocalAiRecommendation("qwen3:1.7b", "Safer/faster", "Very small fallback for low-memory systems."),
            LocalAiRecommendation("qwen3:4b", "Try carefully", "May be slow without enough memory."),
        ]


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
