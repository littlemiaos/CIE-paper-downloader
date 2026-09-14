"""目录型数据源：目录浏览 + 直链下载。

XtremePapers 及结构相同的镜像 / 自定义 API 通用。
"""

import re
from urllib.parse import quote, unquote_plus

from .base import BaseSource

_FOLDER_RE = re.compile(
    r'href="index\.php\?dirpath=\.([^"]*?)/&(?:amp;)?order=0"\s+class="directory">\[([^\]<]+)\]</a>'
)
_FILE_RE = re.compile(r'class="file">([^<]+)</a>')


class DirectorySource(BaseSource):
    """基于 index.php 目录浏览 + 直链下载的数据源。"""

    def __init__(self, base_url: str, http, cfg):
        self.base_url = base_url.rstrip("/")
        self.http = http
        self.cfg = cfg

    def file_url(self, level: str, folder: str, filename: str) -> str:
        return f"{self.base_url}/CAIE/{quote(level)}/{quote(folder)}/{filename}"

    async def list_subjects(self, level: str) -> dict:
        url = f"{self.base_url}/index.php?dirpath=./CAIE/{quote(level)}/&order=0"
        html = await self.http.get_text(url, self.cfg.timeout)
        out = {}
        for m in _FOLDER_RE.finditer(html):
            dirpath = unquote_plus(m.group(1))
            name = m.group(2).strip()
            parts = [p for p in dirpath.split("/") if p and p != "."]
            if len(parts) < 3 or parts[0] != "CAIE":
                continue
            cm = re.search(r"\((\d{4})\)", name)
            if cm:
                out[cm.group(1)] = parts[2]
        return out

    async def list_files(self, level: str, folder: str) -> list:
        url = f"{self.base_url}/index.php?dirpath=./CAIE/{quote(level)}/{quote(folder)}/&order=0"
        html = await self.http.get_text(url, self.cfg.timeout)
        return [m.group(1) for m in _FILE_RE.finditer(html)]
