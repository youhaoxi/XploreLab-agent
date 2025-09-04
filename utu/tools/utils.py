import re


class ContentFilter:
    def __init__(self, banned_sites: list[str] = None):
        if banned_sites:
            self.RE_MATCHED_SITES = re.compile(r"^(" + "|".join(banned_sites) + r")")
        else:
            self.RE_MATCHED_SITES = None

    def filter_results(self, results: list[dict], limit: int, key: str = "link") -> list[dict]:
        # can also use search operator `-site:huggingface.co`
        # ret: {title, link, snippet, position, | sitelinks}
        res = []
        for result in results:
            if self.RE_MATCHED_SITES is None or not self.RE_MATCHED_SITES.match(result[key]):
                res.append(result)
            if len(res) >= limit:
                break
        return res
