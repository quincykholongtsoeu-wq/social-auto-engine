"""FIKILE Growth Engine: deterministic pre-publish content scorer.

No paid AI provider is required. The scorer is intentionally explainable so
we can later compare predicted quality with real platform performance.
"""

from dataclasses import dataclass, asdict
import re
from typing import Dict, List


@dataclass
class ScoreResult:
    total: int
    hook: int
    clarity: int
    engagement: int
    originality: int
    cta: int
    penalties: int
    verdict: str
    reasons: List[str]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


QUESTION_WORDS = ("what", "why", "how", "which", "would", "do you", "have you")
CTA_WORDS = ("comment", "share", "follow", "tell us", "tell me", "learn more", "read", "watch", "save")
SPAM_PHRASES = ("guaranteed money", "instant cash", "click now!!!", "100% guaranteed")


def score_post(text: str) -> ScoreResult:
    text = (text or "").strip()
    reasons: List[str] = []
    if not text:
        return ScoreResult(0, 0, 0, 0, 0, 0, 0, "REJECT", ["Post is empty"])

    lower = text.lower()
    words = re.findall(r"\b[\w'-]+\b", text)
    word_count = len(words)
    first_line = text.splitlines()[0].strip()

    # Hook: reward a concise opening that creates curiosity or specificity.
    hook = 8
    if len(first_line) <= 120:
        hook += 5
    if "?" in first_line:
        hook += 4
    if re.search(r"\d", first_line):
        hook += 3
    hook = min(hook, 20)

    # Clarity: useful social copy is neither empty nor an unreadable wall.
    clarity = 8
    if 20 <= word_count <= 220:
        clarity += 8
    elif word_count < 10 or word_count > 400:
        clarity -= 4
    avg_word_len = sum(map(len, words)) / max(word_count, 1)
    if avg_word_len <= 7:
        clarity += 4
    clarity = max(0, min(clarity, 20))

    # Engagement: questions and explicit invitations create a testable response hypothesis.
    engagement = 7
    if "?" in text:
        engagement += 5
    if any(q in lower for q in QUESTION_WORDS):
        engagement += 4
    if any(c in lower for c in CTA_WORDS):
        engagement += 4
    engagement = min(engagement, 20)

    # Originality proxy: penalise hashtag stuffing/repetitive shouting, reward substance.
    originality = 15
    hashtag_count = len(re.findall(r"(?<!\w)#\w+", text))
    if hashtag_count > 8:
        originality -= 6
        reasons.append("Too many hashtags")
    if word_count >= 30:
        originality += 5
    originality = max(0, min(originality, 20))

    cta = 6
    if any(c in lower for c in CTA_WORDS):
        cta += 9
    if text.rstrip().endswith("?"):
        cta += 5
    cta = min(cta, 20)

    penalties = 0
    if any(p in lower for p in SPAM_PHRASES):
        penalties += 20
        reasons.append("Spam-like claim detected")
    if len(re.findall(r"!", text)) > 5:
        penalties += 5
        reasons.append("Excessive exclamation marks")
    if len(re.findall(r"https?://", lower)) > 2:
        penalties += 5
        reasons.append("Too many outbound links")

    total = max(0, min(100, hook + clarity + engagement + originality + cta - penalties))
    verdict = "APPROVE" if total >= 70 else "REVISE" if total >= 50 else "REJECT"

    if hook < 14:
        reasons.append("Opening hook can be stronger")
    if engagement < 14:
        reasons.append("Add a genuine conversation trigger")
    if cta < 12:
        reasons.append("Add a clear, natural next action")

    return ScoreResult(total, hook, clarity, engagement, originality, cta, penalties, verdict, reasons)
