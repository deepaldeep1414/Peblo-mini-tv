"""
Public, unauthenticated endpoints. This is the ONLY router the viewer UI
is allowed to call (see README Part E for why: it keeps the read path
fast/cacheable and keeps admin surface area away from a child-facing app).
"""
import json

from fastapi import APIRouter, HTTPException

from app.services.publish import CATALOGUE_KEY
from app.storage import get_storage

router = APIRouter(tags=["catalog"])


def _load_catalogue() -> dict:
    storage = get_storage()
    if not storage.exists(CATALOGUE_KEY):
        raise HTTPException(404, "No catalogue has been published yet.")
    return json.loads(storage.read_bytes(CATALOGUE_KEY))


@router.get("/catalog")
def get_catalog():
    return _load_catalogue()


@router.get("/catalog/search")
def search_catalog(
    q: str | None = None,
    category: str | None = None,
    language: str | None = None,
    section: str | None = None,
):
    """
    In-memory filter over the already-published, already-small catalogue
    file. Fine at the scale this catalogue lives at (hundreds of shows);
    see README Part E for where this stops working and what replaces it
    (Postgres full-text / a search index) as the catalogue grows.
    """
    catalogue = _load_catalogue()
    results = []

    for sec in catalogue["sections"]:
        if section and sec["section"] != section:
            continue
        for show in sec["shows"]:
            if category and show.get("category") != category:
                continue

            matched_show = True
            if q:
                ql = q.lower()
                title_hit = ql in show["title"].lower()
                cat_hit = ql in (show.get("category") or "").lower()
                matched_show = title_hit or cat_hit

            matching_episodes = []
            for season in show["seasons"]:
                for ep in season["episodes"]:
                    if language:
                        langs = [lg["language"] for lg in ep.get("languages", [])] or [None]
                        if language not in langs:
                            continue
                    if q and not matched_show:
                        if q.lower() not in ep["title"].lower():
                            continue
                    matching_episodes.append(ep)

            if q and not matched_show and not matching_episodes:
                continue
            if language and not matching_episodes and not q and not category:
                # language filter with nothing matching in this show
                if not any(
                    language in [lg["language"] for lg in ep.get("languages", [])]
                    for season in show["seasons"] for ep in season["episodes"]
                ):
                    continue

            results.append({
                "section": sec["section"],
                "show": {k: v for k, v in show.items() if k != "seasons"},
                "matching_episode_count": len(matching_episodes),
            })

    return {"query": {"q": q, "category": category, "language": language, "section": section}, "results": results}
