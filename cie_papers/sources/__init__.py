"""数据源工厂。"""

from .base import BaseSource
from .directory import DirectorySource

DEFAULT_BASE = "https://papers.xtremepape.rs"
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def get_source(cfg, http) -> BaseSource:
    """根据配置返回数据源；custom 源地址留空时回退默认源。"""
    src = (cfg.source or "xtremepapers").lower()
    if src == "custom":
        base = cfg.custom_api_base.rstrip("/")
        if base:
            return DirectorySource(base, http, cfg)
    return DirectorySource(DEFAULT_BASE, http, cfg)
