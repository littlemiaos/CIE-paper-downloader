"""配置默认值与常量，以及配置读取的轻量封装。"""

DEFAULT_TIMEOUT = 60
DEFAULT_OUTPUT = "pdf"
DEFAULT_SOURCE = "xtremepapers"
DEFAULT_BATCH_OUTPUT = "file"
DEFAULT_BATCH_LIMIT = 20

OUTPUT_FORMATS = ("pdf", "image", "text")
SOURCE_OPTIONS = ("xtremepapers", "custom")
BATCH_OUTPUTS = ("file", "forward")

SESSION_NAMES = {"s": "5/6月", "m": "3月", "w": "10/11月"}
TYPE_NAMES = {
    "qp": "试卷",
    "ms": "答案",
    "gt": "分数线",
    "er": "考官报告",
    "sf": "源文件",
    "in": "插入页",
    "ci": "保密须知",
    "tn": "教师笔记",
    "pt": "预发布材料",
    "rp": "资源包",
}

# 常用科目兜底（在线爬取失败时使用）: code -> (等级, 目录名)
COMMON_SUBJECTS = {
    # IGCSE
    "0580": ("IGCSE", "Mathematics"),
    "0606": ("IGCSE", "Mathematics - Additional"),
    "0607": ("IGCSE", "Mathematics - International"),
    "0620": ("IGCSE", "Chemistry"),
    "0625": ("IGCSE", "Physics"),
    "0610": ("IGCSE", "Biology"),
    "0455": ("IGCSE", "Economics"),
    "0450": ("IGCSE", "Business Studies"),
    "0478": ("IGCSE", "Computer Science"),
    "0417": ("IGCSE", "Information and Communication Technology"),
    "0500": ("IGCSE", "English - First Language"),
    "0510": ("IGCSE", "English as a Second Language (Speaking endorsement)"),
    "0511": ("IGCSE", "English as a Second Language (Count-in speaking)"),
    "0486": ("IGCSE", "English - Literature"),
    "0475": ("IGCSE", "English - Literature in English"),
    "0452": ("IGCSE", "Accounting"),
    "0460": ("IGCSE", "Geography"),
    "0470": ("IGCSE", "History"),
    "0493": ("IGCSE", "Islamiyat"),
    "0448": ("IGCSE", "Pakistan Studies"),
    "0680": ("IGCSE", "Environmental Management"),
    "0653": ("IGCSE", "Science - Combined"),
    "0654": ("IGCSE", "Sciences - Co-ordinated (Double)"),
    "0457": ("IGCSE", "Global Perspectives"),
    "0410": ("IGCSE", "Music"),
    "0411": ("IGCSE", "Drama"),
    "0413": ("IGCSE", "Physical Education"),
    "0445": ("IGCSE", "Design & Technology"),
    "0400": ("IGCSE", "Art & Design"),
    "0648": ("IGCSE", "Food & Nutrition"),
    "0509": ("IGCSE", "Chinese - First Language"),
    "0523": ("IGCSE", "Chinese - Second Language"),
    "0547": ("IGCSE", "Chinese (Mandarin) - Foreign Language"),
    "0471": ("IGCSE", "Travel & Tourism"),
    "0495": ("IGCSE", "Sociology"),
    "0490": ("IGCSE", "Religious Studies"),
    "0520": ("IGCSE", "French - Foreign Language"),
    "0525": ("IGCSE", "German - Foreign Language"),
    "0530": ("IGCSE", "Spanish - Foreign Language"),
    "0508": ("IGCSE", "Arabic - First Language"),
    "0544": ("IGCSE", "Arabic - Foreign Language"),
    "0548": ("IGCSE", "Afrikaans - Second Language"),
    "0697": ("IGCSE", "Marine Science"),
    "0600": ("IGCSE", "Agriculture"),
    "0453": ("IGCSE", "Development Studies"),
    "0480": ("IGCSE", "Latin"),
    # AS & A Level
    "9709": ("AS and A Level", "Mathematics"),
    "9231": ("AS and A Level", "Mathematics - Further"),
    "9700": ("AS and A Level", "Biology"),
    "9701": ("AS and A Level", "Chemistry"),
    "9702": ("AS and A Level", "Physics"),
    "9708": ("AS and A Level", "Economics"),
    "9609": ("AS and A Level", "Business"),
    "9618": ("AS and A Level", "Computer Science"),
    "9626": ("AS and A Level", "Information Technology"),
    "9706": ("AS and A Level", "Accounting"),
    "9695": ("AS and A Level", "Literature in English"),
    "9698": ("AS and A Level", "Psychology"),
    "9699": ("AS and A Level", "Sociology"),
    "9489": ("AS and A Level", "History"),
    "9680": ("AS and A Level", "Arabic"),
}


class Cfg:
    """对 AstrBotConfig 的轻量封装，统一读取默认值。"""

    def __init__(self, raw):
        self.raw = raw if isinstance(raw, dict) else {}

    def get(self, key, default=None):
        v = self.raw.get(key)
        return default if v is None or v == "" else v

    @property
    def output_format(self):
        v = self.get("output_format", DEFAULT_OUTPUT)
        return v if v in OUTPUT_FORMATS else DEFAULT_OUTPUT

    @property
    def stop_on_failure(self):
        return bool(self.get("stop_on_failure", True))

    @property
    def timeout(self):
        try:
            t = int(self.get("timeout", DEFAULT_TIMEOUT))
            return t if t > 0 else DEFAULT_TIMEOUT
        except (TypeError, ValueError):
            return DEFAULT_TIMEOUT

    @property
    def source(self):
        return self.get("source", DEFAULT_SOURCE)

    @property
    def custom_api_base(self):
        return (self.get("custom_api_base", "") or "").strip()

    @property
    def batch_output(self):
        v = self.get("batch_output", DEFAULT_BATCH_OUTPUT)
        return v if v in BATCH_OUTPUTS else DEFAULT_BATCH_OUTPUT

    @property
    def batch_limit(self):
        try:
            n = int(self.get("batch_limit", DEFAULT_BATCH_LIMIT))
            return n if n > 0 else DEFAULT_BATCH_LIMIT
        except (TypeError, ValueError):
            return DEFAULT_BATCH_LIMIT
