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

    async def download(self, url: str, path: str, timeout: int) -> str:
        """下载到 path，返回结果：'ok' / 'not_found' / 'invalid' / 'error'。"""
        session = self._ensure()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status == 404:
                    return "not_found"
                if resp.status != 200:
                    return "error"
                first = True
                written = 0
                with open(path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(65536):
                        if first:
                            if not chunk.startswith(b"%PDF"):
                                f.close()
                                return "invalid"
                            first = False
                        f.write(chunk)
                        written += len(chunk)
                return "ok" if written >= 500 else "invalid"
        except Exception:
            return "error"

    async def close(self):
        if self._session is not None and not self._session.closed:
            await self._session.close()
