"""共享的异步 HTTP 客户端（aiohttp）。"""

import aiohttp


class HttpClient:
    def __init__(self, ua: str):
        self.ua = ua
        self._session = None

    def _ensure(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers={"User-Agent": self.ua})
        return self._session

    async def get_text(self, url: str, timeout: int) -> str:
        session = self._ensure()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            return await resp.text()

    async def download(self, url: str, path: str, timeout: int) -> bool:
        """下载到 path，校验为合法 PDF 后返回 True，否则 False（并删除文件）。"""
        session = self._ensure()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            if resp.status != 200:
                return False
            first = True
            written = 0
            with open(path, "wb") as f:
                async for chunk in resp.content.iter_chunked(65536):
                    if first:
                        if not chunk.startswith(b"%PDF"):
                            f.close()
                            return False
                        first = False
                    f.write(chunk)
                    written += len(chunk)
            return written >= 500

    async def close(self):
        if self._session is not None and not self._session.closed:
            await self._session.close()
