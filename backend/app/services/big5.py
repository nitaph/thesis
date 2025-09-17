import json
from pathlib import Path

# Local, immutable copy of IPIP-50 keyed map with +/− items and trait mapping
_IPIP_FILE = Path(__file__).resolve().parents[1] / "prompts" / "ipip50_keyed.json"

with _IPIP_FILE.open("r", encoding="utf-8") as f:
    IPIP_KEY = json.load(f)
# {
#   "items": [
#     {"index":1, "trait":"E", "key":"+","text":"..."},
#     ...
#   ],
#   "scoring_note":"Official IPIP 50-item scoring. + keyed map 1→5; − keyed map 5→1."
# }

TRAITS = ["O","C","E","A","N"]

def score_ipip50(answers: list[int]) -> dict:
    if len(answers) != 50:
        raise ValueError("answers must be length 50")
    sums = {t: 0 for t in TRAITS}
    for i, ans in enumerate(answers, start=1):
        item = IPIP_KEY["items"][i-1]
        trait = item["trait"]
        key = item["key"]
        if not (1 <= ans <= 5):
            raise ValueError("answers must be integers 1–5")
        mapped = ans if key == "+" else (6 - ans)  # +:1->1..5->5 ; −:1->5..5->1
        sums[trait] += mapped
    # each trait has 10 items; sums already 10–50 integers by construction
    return sums
