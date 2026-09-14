"""CIE (Cambridge International) 试卷下载插件（入口）。

数据来源：XtremePapers（默认）或自定义 API。
具体逻辑已拆分到 cie_papers 子包，main.py 仅负责命令注册与路由。

命令:
  /cie                             查看帮助
  /cie list [等级|代码|代码+考季]  分步引导查找（推荐）
  /cie get <代码> <考季><年份> <卷号> [类型]  直接下载
"""

from __future__ import annotations

import os
import re
import sys

# 保证子包可导入（cie_papers）
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
if _PKG_DIR not in sys.path:
    sys.path.insert(0, _PKG_DIR)

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

try:
    import astrbot.api.message_components as Comp

    FileComp = Comp.File
except Exception:  # pragma: no cover
    FileComp = None

from cie_papers.config import Cfg, SESSION_NAMES, TYPE_NAMES
from cie_papers.sources import get_source, DEFAULT_UA
from cie_papers.http import HttpClient
from cie_papers.resolver import SubjectResolver, parse_fname, sort_key
from cie_papers.downloader import Downloader
from cie_papers.output import OutputFormatter

_STRIP_CODE_RE = re.compile(r"\s*\(\d{4}\)\s*$")

HELP_TEXT = (
    "【CIE 试卷下载】使用说明\n\n"
    "📋 分步查找（推荐，简单）:\n"
    "  /cie list                  查看所有科目与代码\n"
    "  /cie list <代码>           查看该科目可用卷号与考季\n"
    "  /cie list <代码> <考季>    查看某考季的具体文件\n"
    "  例: /cie list 0580 s20\n\n"
    "⚡ 直接下载（熟练后）:\n"
    "  /cie get <代码> <考季><年份> <卷号> [类型]\n"
    "  例: /cie get 0580 s20 21        试卷+答案\n"
    "  例: /cie get 0580 s20 21 qp     仅试卷\n"
    "  例: /cie get 9709 w19 32 ms     仅答案\n\n"
    "📌 考季: s=5/6月 m=3月 w=10/11月\n"
    "📌 类型: qp=试卷 ms=答案 gt=分数线 er=考官报告 all=试卷+答案(默认)\n"
    "📌 常用: 0580数学 0620化学 0625物理 0610生物 0478计算机\n"
    "        9709数学(AL) 9701化学(AL) 9702物理(AL) 9700生物(AL)\n"
    "📌 输出形式/下载源/超时等可在插件配置中修改\n"
    "数据来源: XtremePapers"
)


@register("astrbot_plugin_cie_papers", "AstrBot", "下载 CIE (Cambridge International) 历年真题/答案等 PDF。", "1.1.0")
class CiePapersPlugin(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.cfg = Cfg(config)
        self.http = HttpClient(DEFAULT_UA)
        self.source = get_source(self.cfg, self.http)
        self.resolver = SubjectResolver(self.source)
        self.downloader = Downloader(self.http, self.cfg)
        self.output = OutputFormatter(self.cfg, FileComp)

    async def initialize(self):
        # 后台预热科目缓存，加速后续查询
        try:
            await self.resolver.get_map()
        except Exception as e:  # pragma: no cover
            logger.warning(f"CIE 插件预热科目列表失败: {e}")

    async def terminate(self):
        await self.http.close()

    # ------------------------------------------------------------------ 工具
    @staticmethod
    def _parse_get(raw: str):
        toks = raw.lower().split()
        if not toks or not re.fullmatch(r"\d{4}", toks[0]):
            return None
        code = toks[0]
        session = year = paper = ptype = None
        i = 1
        if i < len(toks):
            t = toks[i]
            m = re.fullmatch(r"([smw])(\d{2}|\d{4})", t)
            if m:
                session, year = m.group(1), m.group(2)
                i += 1
            elif t in ("s", "m", "w"):
                session = t
                i += 1
        if year is None and i < len(toks) and re.fullmatch(r"\d{2}|\d{4}", toks[i]):
            year = toks[i]
            i += 1
        for t in toks[i:]:
            if t == "all":
                ptype = "all"
            elif t in TYPE_NAMES:
                ptype = t
            elif t in ("s", "m", "w") and session is None:
                session = t
            elif re.fullmatch(r"\d{2}", t) and paper is None:
                paper = t
            elif re.fullmatch(r"\d{2}|\d{4}", t) and year is None:
                year = t
        if session is None or year is None or paper is None:
            return None
        if len(year) == 4:
            year = year[2:]
        if ptype is None:
            ptype = "all"
        return code, session, year, ptype, paper

    # ------------------------------------------------------------------ 命令
    @filter.command("cie")
    async def cie(self, event: AstrMessageEvent):
        text = (event.message_str or "").strip()
        tokens = text.split()
        if tokens and tokens[0].lstrip("/").lower() == "cie":
            tokens = tokens[1:]
        cmd = tokens[0].lower() if tokens else ""
        rest = " ".join(tokens[1:]) if len(tokens) > 1 else ""

        if cmd in ("", "help", "帮助", "h", "?"):
            yield event.plain_result(HELP_TEXT)
            return
        if cmd in (
            "list", "ls", "列表", "科目", "subjects", "subject",
            "papers", "paper", "find", "search", "查找", "文件",
        ):
            yield event.plain_result(await self._cmd_list(rest))
            return
        if cmd in ("get", "download", "下载", "dl", "down"):
            async for r in self._cmd_get(event, rest):
                yield r
            return
        yield event.plain_result(HELP_TEXT)

    async def _cmd_list(self, rest: str) -> str:
        toks = rest.strip().lower().split()
        if not toks:
            return await self._list_subjects("")
        t0 = toks[0]
        if t0 in ("i", "igcse", "ig", "a", "as", "alevel", "al", "a-level", "o", "olevel", "ol", "o-level"):
            return await self._list_subjects(t0)
        if re.fullmatch(r"\d{4}", t0):
            code = t0
            session = year = None
            if len(toks) > 1:
                m = re.fullmatch(r"([smw])(\d{2}|\d{4})", toks[1])
                if m:
                    session, year = m.group(1), m.group(2)
                    if len(year) == 4:
                        year = year[2:]
            if session and year:
                return await self._list_files(code, session, year)
            return await self._list_papers(code)
        return (
            "用法: /cie list [等级 | 科目代码 | 科目代码+考季]\n"
            "例: /cie list          查看全部科目\n"
            "    /cie list igcse    查看 IGCSE 科目\n"
            "    /cie list 0580     查看 0580 可用卷号\n"
            "    /cie list 0580 s20 查看 0580 在 s20 的文件"
        )

    async def _list_subjects(self, level_kw: str) -> str:
        try:
            mapping = await self.resolver.get_map()
        except Exception as e:  # pragma: no cover
            return f"❌ 获取科目列表失败: {e}"
        if not mapping:
            return "⚠️ 获取科目列表失败，请检查网络后重试。"
        level_filter = None
        if level_kw in ("i", "igcse", "ig"):
            level_filter = "IGCSE"
        elif level_kw in ("a", "as", "alevel", "al", "a-level"):
            level_filter = "AS and A Level"
        elif level_kw in ("o", "olevel", "ol", "o-level"):
            level_filter = "O Level"

        levels = ["IGCSE", "AS and A Level", "O Level"] if level_filter is None else [level_filter]
        lines = []
        for lv in levels:
            items = sorted(
                [(c, f) for c, (l, f) in mapping.items() if l == lv],
                key=lambda x: x[1].lower(),
            )
            if not items:
                continue
            short_pairs = [f"{c} {_STRIP_CODE_RE.sub('', f)}" for c, f in items]
            body = " | ".join(short_pairs)
            if len(body) > 900:
                body = body[:900] + " …"
            lines.append(f"【{lv}】共 {len(items)} 科\n{body}")
        if not lines:
            return "未找到任何科目。"
        return "\n\n".join(lines) + "\n\n💡 下一步: /cie list <代码> 查看该科目可用卷号与考季"

    async def _list_papers(self, code: str) -> str:
        try:
            pair = await self.resolver.resolve(code)
        except Exception as e:  # pragma: no cover
            return f"❌ 查询失败: {e}"
        if not pair:
            return f"❌ 未找到科目代码 {code}。可用 /cie list 查看科目列表。"
        level, folder = pair
        try:
            files = await self.source.list_files(level, folder)
        except Exception as e:  # pragma: no cover
            return f"❌ 获取文件列表失败: {e}"
        files = [f for f in files if f.startswith(f"{code}_")]
        if not files:
            return f"未找到 {code} 相关文件。"
        papers = set()
        sess_years = {"s": [], "m": [], "w": []}
        for f in files:
            p = parse_fname(f, code)
            if not p:
                continue
            session, year, _t, paper = p
            papers.add(paper)
            sess_years[session].append(int(year))
        if not papers:
            return f"未解析到 {code} 的文件。"
        papers_sorted = sorted(papers, key=lambda x: int(x))
        lines = [f"【{code}】可用卷号与考季", "卷号(Paper): " + "  ".join(papers_sorted)]
        for s in ("s", "m", "w"):
            ys = sorted(set(sess_years[s]))
            if ys:
                rng = f"{ys[0]}-{ys[-1]}" if len(ys) > 1 else str(ys[0])
                lines.append(f"  {SESSION_NAMES[s]} 考季: {rng}")
        demo_s = "s" if sess_years["s"] else ("w" if sess_years["w"] else "m")
        demo_yr = f"{max(sess_years[demo_s]):02d}"
        lines.append("")
        lines.append(f"💡 查看具体文件: /cie list {code} {demo_s}{demo_yr}")
        lines.append(f"💡 直接下载: /cie get {code} {demo_s}{demo_yr} <卷号>")
        return "\n".join(lines)

    async def _list_files(self, code: str, session: str, year: str) -> str:
        try:
            pair = await self.resolver.resolve(code)
        except Exception as e:  # pragma: no cover
            return f"❌ 查询失败: {e}"
        if not pair:
            return f"❌ 未找到科目代码 {code}。可用 /cie list 查看科目列表。"
        level, folder = pair
        try:
            files = await self.source.list_files(level, folder)
        except Exception as e:  # pragma: no cover
            return f"❌ 获取文件列表失败: {e}"
        sp = f"{code}_{session}{year}_"
        files = [f for f in files if f.startswith(sp)]
        if not files:
            return f"未找到 {code} {session}{year} 相关文件。可 /cie list {code} 查看其它考季。"
        files = sorted(set(files), key=lambda f: sort_key(f, code), reverse=True)
        total = len(files)
        shown = files[:40]
        text = "\n".join(shown)
        if total > 40:
            text += f"\n… 共 {total} 个文件，仅显示前 40 个"
        sess_name = SESSION_NAMES.get(session, session)
        hint = (
            f"\n\n💡 下载: /cie get {code} {session}{year} <卷号> [qp|ms|gt|er]\n"
            f"   例: /cie get {code} {session}{year} 21"
        )
        return f"【{code} {sess_name}{year}】文件（共 {total} 个）:\n{text}{hint}"

    async def _cmd_get(self, event: AstrMessageEvent, rest: str):
        parsed = self._parse_get(rest)
        if parsed is None:
            yield event.plain_result(
                "❌ 参数不完整。\n用法: /cie get <科目代码> <考季><年份> <卷号> [类型]\n"
                "例: /cie get 0580 s20 21\n"
                "    /cie get 9709 w19 32 ms\n"
                "考季: s=5/6月 m=3月 w=10/11月 | 类型: qp/ms/gt/er/all(默认)"
            )
            return
        code, session, year, ptype, paper = parsed
        yield event.plain_result(f"🔍 正在查找并下载 {code}_{session}{year} 试卷 {paper}，请稍候…")

        try:
            pair = await self.resolver.resolve(code)
        except Exception as e:  # pragma: no cover
            logger.error(f"解析科目失败: {e}")
            yield event.plain_result(f"❌ 查询科目失败: {e}")
            return
        if not pair:
            yield event.plain_result(f"❌ 未找到科目代码 {code}。可用 /cie list 查看科目列表。")
            return
        level, folder = pair

        types = ["qp", "ms"] if ptype in (None, "all") else [ptype]
        ok = 0
        stopped = False
        for tp in types:
            fname = f"{code}_{session}{year}_{tp}_{paper}.pdf"
            url = self.source.file_url(level, folder, fname)
            label = TYPE_NAMES.get(tp, tp)
            # text 模式直接发链接，无需下载
            if self.cfg.output_format == "text":
                yield event.plain_result(f"📄 {label}「{fname}」\n🔗 {url}")
                ok += 1
                continue
            path = await self.downloader.download(url, fname)
            if not path:
                yield event.plain_result(f"⚠️ 下载失败: {label}「{fname}」")
                if self.cfg.stop_on_failure:
                    stopped = True
                    break
                continue
            for r in await self.output.build(event, path, fname, url, label):
                yield r
            ok += 1

        if stopped:
            yield event.plain_result("⏹ 已按配置在首次失败时停止。可在插件配置中关闭「下载失败即停止」。")
        elif ok == 0:
            yield event.plain_result(
                f"💡 可尝试 /cie list {code} {session}{year} 查看该考季实际存在的文件。"
            )
