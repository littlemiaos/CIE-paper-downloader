"""输出格式化：单体输出（pdf / image / text）与批量输出（逐个文件 / 合并转发）。"""


class OutputFormatter:
    def __init__(self, cfg, comp):
        # comp 为 astrbot.api.message_components 模块（可能为 None）
        self.cfg = cfg
        self.comp = comp

    def _c(self, name):
        return getattr(self.comp, name, None) if self.comp is not None else None

    # ------------------------------------------------------------ 单体
    async def build(self, event, path, fname, url, label):
        """根据配置生成结果列表（由调用方逐条 yield）。"""
        fmt = self.cfg.output_format
        if fmt == "text":
            return [event.plain_result(f"📄 {label}「{fname}」\n🔗 {url}")]
        if fmt == "image":
            img = self._pdf_to_image(path)
            if img:
                return [
                    event.plain_result(f"🖼 {label}「{fname}」(第 1 页预览)\n🔗 {url}"),
                    event.image_result(img),
                ]
            # 转图失败则退回文字
            return [event.plain_result(f"📄 {label}「{fname}」\n🔗 {url}")]
        # 默认 pdf
        results = [event.plain_result(f"📄 {label}「{fname}」\n🔗 {url}")]
        file_comp = self._c("File")
        if file_comp is not None and path:
            results.append(event.chain_result([file_comp(name=fname, file=path)]))
        return results

    # ------------------------------------------------------------ 批量
    async def build_batch(self, event, items, title):
        """items: [(path_or_None, fname, url, label)]，按配置选择输出方式。"""
        if self.cfg.batch_output == "forward":
            result = self._build_forward(event, items, title)
            if result is not None:
                return result
        # 逐个文件（合并转发不支持时也退回到这里）
        results = []
        for path, fname, url, label in items:
            results.extend(await self.build(event, path, fname, url, label))
        return results

    def _build_forward(self, event, items, title):
        """把批量结果合并转发为一条「聊天记录」。不支持时返回 None。"""
        node_comp = self._c("Node")
        nodes_comp = self._c("Nodes")
        plain_comp = self._c("Plain")
        file_comp = self._c("File")
        if node_comp is None or nodes_comp is None or plain_comp is None:
            return None
        try:
            nodes = []
            for path, fname, url, label in items:
                content = [plain_comp(f"{label}｜{fname}\n{url}")]
                if file_comp is not None and path:
                    content.append(file_comp(name=fname, file=path))
                nodes.append(node_comp(name=title, uin="0", content=content))
            return [event.chain_result([nodes_comp(nodes=nodes)])]
        except Exception:
            return None

    # ------------------------------------------------------------ 工具
    @staticmethod
    def _pdf_to_image(path: str):
        """把 PDF 第 1 页转成 PNG，返回图片路径；失败返回 None。"""
        if not path:
            return None
        try:
            import fitz  # PyMuPDF
        except Exception:
            return None
        try:
            doc = fitz.open(path)
            page = doc[0]
            pix = page.get_pixmap(dpi=120)
            img = path[:-4] + ".png"
            pix.save(img)
            doc.close()
            return img
        except Exception:
            return None
