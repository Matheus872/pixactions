from urllib.parse import quote

from .config import Settings
from .schemas.events import EventLinks


def event_links(settings: Settings, slug: str) -> EventLinks:
    action_url = f"{settings.public_web_url}/actions/events/{slug}"
    return EventLinks(
        checkout_url=f"{settings.public_web_url}/e/{slug}",
        action_url=action_url,
        blink_url=f"https://dial.to/?action=solana-action:{quote(action_url, safe='')}&cluster={settings.solana_cluster}",
    )


def ticket_url(settings: Settings, pubkey: str) -> str:
    return f"{settings.public_web_url}/t/{pubkey}"


def explorer_url(settings: Settings, address: str) -> str:
    return f"https://explorer.solana.com/address/{address}?cluster={settings.solana_cluster}"
