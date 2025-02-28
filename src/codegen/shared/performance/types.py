from dataclasses import dataclass


@dataclass
class MemoryStats:
    memory_rss_gb: float
    memory_vms_gb: float