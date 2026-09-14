"""科目目录解析与缓存，以及文件名解析工具。"""

import re
import time

from astrbot.api import logger

from .config import COMMON_SUBJECTS

LEVELS = ["IGCSE", "AS and A Level", "O Level"]


def parse_fname(fname: str, code: str):
    """解析形如 0580_s20_qp_21.pdf 的文件名 -> (考季, 年份, 类型, 卷号)。"""
    m = re.fullmatch(re.escape(code) + r"_([smw])(\d{2})_([a-z]+)_(\d{2})\.pdf", fname, re.I)
    if m:
        return m.group(1).lower(), m.group(2), m.group(3).lower(), m.group(4)
    return None


def sort_key(fname: str, code: str):
    p = parse_fname(fname, code)
    if not p:
        return (0, 0, 0, 0)
    session, year, ptype, paper = p
    sess_rank = {"m": 1, "s": 2, "w": 3}.get(session, 0)
    type_rank = {"qp": 1, "ms": 2, "gt": 3, "er": 4, "in": 5}.get(ptype, 9)
    try:
        paper_n = int(paper)
    except ValueError:
        paper_n = 0
    return (int(year), sess_rank, type_rank, paper_n)


class SubjectResolver:
    """把科目代码解析为 (等级, 目录名)，并缓存 1 小时。"""

    def __init__(self, source):
        self.source = source
        self._map = {}
        self._cache_time = 0.0

    async def get_map(self) -> dict:
        if self._map and time.time() - self._cache_time < 3600:
            return self._map
        mapping = {}
        for level in LEVELS:
            try:
                subjects = await self.source.list_subjects(level)
                for code, folder in subjects.items():
                    mapping[code] = (level, folder)
            except Exception as e:  # 单个等级失败不影响其它等级
                logger.warning(f"获取 {level} 科目列表失败: {e}")
        for code, pair in COMMON_SUBJECTS.items():
            mapping.setdefault(code, pair)
        self._map = mapping
        self._cache_time = time.time()
        return mapping

    async def resolve(self, code: str):
        mapping = await self.get_map()
        return mapping.get(code)
