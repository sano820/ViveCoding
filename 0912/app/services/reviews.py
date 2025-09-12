from collections import Counter

def extract_keywords(reviews: list[str], top_n: int = 5):
    keywords = []
    for r in reviews:
        if "맛" in r: keywords.append("맛")
        if "친절" in r: keywords.append("친절")
        if "분위기" in r: keywords.append("분위기")
        if "청결" in r: keywords.append("청결")
    counter = Counter(keywords)
    return [k for k, _ in counter.most_common(top_n)]
