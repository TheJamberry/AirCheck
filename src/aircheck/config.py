import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import yaml


@dataclass
class Config:
    device: Union[int, str] = 0
    sample_rate: int = 44100
    channels: int = 2
    off_air_channel: int = 0
    program_channel: int = 1
    chunk_duration: float = 8.0
    check_interval: float = 2.0
    min_rms: float = 0.001
    match_threshold: float = 0.85
    max_delay_ms: float = 5000.0


def load_config(path: Path) -> Config:
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    known = {f.name for f in dataclasses.fields(Config)}
    filtered = {k: v for k, v in data.items() if k in known}
    return Config(**filtered)
