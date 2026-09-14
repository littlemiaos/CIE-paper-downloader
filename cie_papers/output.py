"""输出格式化：pdf / image / text 三种形式。"""


class OutputFormatter:
    def __init__(self, cfg, file_comp):
        self.cfg = cfg
        self.file_comp = file_comp

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
        if self.file_comp is not None:
            results.append(event.chain_result([self.file_comp(file=path, name=fname)]))
        return results

    @staticmethod
    def _pdf_to_image(path: str):
        """把 PDF 第 1 页转成 PNG，返回图片路径；失败返回 None。"""
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
