"""PDF 下载器：负责下载到本地临时目录并做基础校验与清理。"""

import os
import tempfile
import time

from astrbot.api import logger


class Downloader:
    def __init__(self, http, cfg, save_dir=None):
        self.http = http
        self.cfg = cfg
        self.save_dir = save_dir or os.path.join(tempfile.gettempdir(), "astrbot_cie_papers")

    async def download(self, url: str, fname: str):
        """下载并校验，返回 (本地路径, 结果)；结果: 'ok' / 'not_found' / 'invalid' / 'error'。"""
        try:
            os.makedirs(self.save_dir, exist_ok=True)
        except OSError:
            return None, "error"
        self._cleanup_old()
        path = os.path.join(self.save_dir, fname)
        reason = await self.http.download(url, path, self.cfg.timeout)
        if reason == "ok":
            return path, "ok"
        if reason not in ("not_found",):
            logger.warning(f"下载失败({reason}) {url}")
        self._safe_remove(path)
        return None, reason

    @staticmethod
    def _safe_remove(path: str) -> None:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    def _cleanup_old(self, max_age: int = 86400) -> None:
        now = time.time()
        try:
            for name in os.listdir(self.save_dir):
                p = os.path.join(self.save_dir, name)
                if os.path.isfile(p) and now - os.path.getmtime(p) > max_age:
                    try:
                        os.remove(p)
                    except OSError:
                        pass
        except OSError:
            pass
