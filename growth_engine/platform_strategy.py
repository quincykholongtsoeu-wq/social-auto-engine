"""Platform routing for FIKILE Growth Engine.

Meta is not a hard dependency. The engine can build, score, approve, package,
and learn from content while individual publisher adapters are connected later.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformTarget:
    name: str
    priority: int
    status: str
    objective: str
    content_types: tuple[str, ...]
    notes: str


PLATFORMS = (
    PlatformTarget(
        name="linkedin",
        priority=1,
        status="connect_now",
        objective="authority + B2B leads + professional engagement",
        content_types=("text", "image", "document"),
        notes="Use member publishing first; organization publishing may require additional permissions.",
    ),
    PlatformTarget(
        name="mastodon",
        priority=2,
        status="adapter_candidate",
        objective="open-network testing + fast API experimentation",
        content_types=("text", "image"),
        notes="Open API supports publishing, scheduling and engagement actions with user OAuth.",
    ),
    PlatformTarget(
        name="facebook",
        priority=3,
        status="blocked_credentials",
        objective="reach + engagement + monetization experiments",
        content_types=("text", "image", "video", "reel"),
        notes="Keep adapter ready; Meta developer verification is not on the critical path.",
    ),
)


def active_targets() -> list[PlatformTarget]:
    """Return targets that can be developed/tested without Meta credentials."""
    return [p for p in sorted(PLATFORMS, key=lambda x: x.priority) if p.name != "facebook"]


def campaign_package(text: str, hook: str, cta: str) -> dict[str, str]:
    """Create simple platform-specific variants without an external AI API."""
    core = text.strip()
    return {
        "linkedin": f"{hook.strip()}\n\n{core}\n\n{cta.strip()}",
        "mastodon": f"{hook.strip()}\n\n{core}\n\n{cta.strip()}",
        "facebook_pending": f"{hook.strip()}\n\n{core}\n\n{cta.strip()}",
    }
