"""Shared test fixtures and mock setup."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure required directories exist for tests
_project_root = Path(__file__).parent.parent
for _d in ("uploads", "outputs", "logs"):
    (_project_root / _d).mkdir(exist_ok=True)

# Mock heavy dependencies BEFORE any app imports
_torch_mock = MagicMock()
_torch_mock.cuda.is_available.return_value = False
_torch_mock.__version__ = "2.0.0"
_torch_mock.version.cuda = "11.8"
sys.modules["torch"] = _torch_mock

_fw_mock = MagicMock()
_fw_mock.__version__ = "1.2.1"
sys.modules["faster_whisper"] = _fw_mock

_psutil_mock = MagicMock()
_proc_mock = MagicMock()
_mem_info = MagicMock()
_mem_info.rss = 200 * 1024 * 1024
_mem_info.vms = 500 * 1024 * 1024
_proc_mock.memory_info.return_value = _mem_info
_proc_mock.cpu_percent.return_value = 10.0
_proc_mock.num_threads.return_value = 4
_psutil_mock.Process.return_value = _proc_mock
_vmem = MagicMock()
_vmem.total = 16 * 1024**3
_vmem.used = 8 * 1024**3
_vmem.available = 8 * 1024**3
_vmem.percent = 50.0
_psutil_mock.virtual_memory.return_value = _vmem
_cpu_freq = MagicMock()
_cpu_freq.current = 3600.0
_psutil_mock.cpu_freq.return_value = _cpu_freq
_psutil_mock.cpu_percent.return_value = 20.0
_psutil_mock.cpu_count.side_effect = lambda logical=True: 8 if logical else 4
_disk = MagicMock()
_disk.read_bytes = 100 * 1024**2
_disk.write_bytes = 50 * 1024**2
_psutil_mock.disk_io_counters.return_value = _disk
sys.modules["psutil"] = _psutil_mock

# Mock argos-translate
_argos_package_mock = MagicMock()
_argos_package_mock.get_installed_packages.return_value = []
_argos_package_mock.get_available_packages.return_value = []
sys.modules["argostranslate"] = MagicMock()
sys.modules["argostranslate.package"] = _argos_package_mock
_argos_translate_mock = MagicMock()
_argos_translate_mock.get_installed_languages.return_value = []
sys.modules["argostranslate.translate"] = _argos_translate_mock
