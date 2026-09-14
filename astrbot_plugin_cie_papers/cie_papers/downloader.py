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
        """下载并校验，成功返回本地路径，失败返回 None。"""
        try:
            os.makedirs(self.save_dir, exist_ok=True)
        except OSError:
            return None
        self._cleanup_old()
        path = os.path.join(self.save_dir, fname)
        try:
            ok = await self.http.download(url, path, self.cfg.timeout)
        except Exception as e:
            logger.warning(f"下载失败 {url}: {e}")
            ok = False
        if ok:
            return path
        self._safe_remove(path)
        return None

    @staticmethod
    def _safe_remove(path: str) -> None:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

    @staticmethod
    def _cleanup_old(save_dir: str, max_age: int = 86400) -> None:
        now = time.time()
        try:
            for name in os.listdir(save_dir):
                p = os.path.join(save_dir, name)
                if os.path.isfile(p) and now - os.path.getmtime(p) > max_age:
                    try:
                        os.remove(p)
                    except OSError:
                        pass
        except OSError:
            pass
