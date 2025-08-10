from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DataIngestionConfig:
    root_dir: Path
    image_URL: str
    report_URL: str
    image_data_file: Path
    report_data_file: Path
    unzip_dir_image: Path
    unzip_dir_report: Path