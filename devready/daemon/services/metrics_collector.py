"""Background metrics collector using psutil."""
from __future__ import annotations

import asyncio
import logging
from collections import deque
from typing import Deque, Optional

import psutil

logger = logging.getLogger(__name__)

_CPU_THRESHOLD = 2.0
_MEM_THRESHOLD_MB = 150.0


class MetricsCollector:
    def __init__(self) -> None:
        self._cpu_samples: Deque[float] = deque(maxlen=1000)
        self._mem_samples: Deque[float] = deque(maxlen=1000)
        self.scan_count: int = 0
        self._scan_durations: Deque[float] = deque(maxlen=1000)
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._collect_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _collect_loop(self) -> None:
        while True:
            await asyncio.sleep(5)
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.Process().memory_info().rss / (1024 * 1024)
            self._cpu_samples.append(cpu)
            self._mem_samples.append(mem)
            if cpu > _CPU_THRESHOLD:
                logger.warning("CPU usage %.1f%% exceeds threshold %.1f%%", cpu, _CPU_THRESHOLD)
            if mem > _MEM_THRESHOLD_MB:
                logger.warning("Memory usage %.1f MB exceeds threshold %.1f MB", mem, _MEM_THRESHOLD_MB)

    def record_scan(self, duration: float) -> None:
        self.scan_count += 1
        self._scan_durations.append(duration)

    @property
    def current_cpu(self) -> float:
        return self._cpu_samples[-1] if self._cpu_samples else 0.0

    @property
    def current_memory_mb(self) -> float:
        return self._mem_samples[-1] if self._mem_samples else psutil.Process().memory_info().rss / (1024 * 1024)

    @property
    def avg_scan_duration(self) -> float:
        if not self._scan_durations:
            return 0.0
        return sum(self._scan_durations) / len(self._scan_durations)
