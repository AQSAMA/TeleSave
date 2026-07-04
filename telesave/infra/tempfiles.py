import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def temporary_workdir(base_dir: Path) -> Iterator[Path]:
    base_dir.mkdir(parents=True, exist_ok=True)
    path = Path(tempfile.mkdtemp(prefix="job-", dir=base_dir))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
