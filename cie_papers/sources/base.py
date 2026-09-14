"""数据源抽象基类。"""

from abc import ABC, abstractmethod


class BaseSource(ABC):
    """统一数据源接口，便于切换默认源与自定义 API。"""

    @abstractmethod
    def file_url(self, level: str, folder: str, filename: str) -> str:
        """返回文件的直接下载 URL。"""

    @abstractmethod
    async def list_subjects(self, level: str) -> dict:
        """返回某等级的科目映射 {代码: 目录名}。"""

    @abstractmethod
    async def list_files(self, level: str, folder: str) -> list:
        """返回某科目目录下的文件名列表。"""
