from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import PublishStatus, Show
from app.schemas.schemas import ValidationIssue, ValidationReport


def build_validation_report(db: Session) -> ValidationReport:
    """
    Surfaces everything currently blocking publish, grouped by show, so
    an editor can fix it without asking an engineer. Rules enforced here
    mirror (and are the source of truth for) the checks applied at
    publish time -- see services/publish.py.
    """
    issues_by_show: dict[str, list[ValidationIssue]] = defaultdict(list)

    shows = db.query(Show).all()
    for show in shows:
        label = show.title or "(untitled show)"

        if show.status == PublishStatus.published and show.section is None:
            issues_by_show[show.id].append(ValidationIssue(
                entity_type="show", entity_id=show.id, entity_label=label,
                field="section",
                message=f'"{label}" is marked published but has no section assigned. '
                        f"Assign a section before it can appear in the catalogue.",
            ))

        seen_group_lang: dict[tuple[str, str], str] = {}

        for season in show.seasons:
            for ep in season.episodes:
                ep_label = f'{label} · S{season.number}E{ep.episode_number} "{ep.title}"'

                if ep.status != PublishStatus.published:
                    continue  # drafts don't block publish

                if not ep.duration_seconds:
                    issues_by_show[show.id].append(ValidationIssue(
                        entity_type="episode", entity_id=ep.id, entity_label=ep_label,
                        field="duration_seconds",
                        message=f"{ep_label} is published but has no duration set.",
                    ))

                if not ep.artworks or not any(a.kind == "thumbnail" for a in ep.artworks):
                    issues_by_show[show.id].append(ValidationIssue(
                        entity_type="episode", entity_id=ep.id, entity_label=ep_label,
                        field="artwork",
                        message=f"{ep_label} is published but is missing a thumbnail image.",
                    ))

                if ep.content_group:
                    key = (ep.content_group, ep.language)
                    if key in seen_group_lang and seen_group_lang[key] != ep.id:
                        issues_by_show[show.id].append(ValidationIssue(
                            entity_type="episode", entity_id=ep.id, entity_label=ep_label,
                            field="content_group",
                            message=f"Duplicate language '{ep.language}' for content group "
                                    f"'{ep.content_group}' in \"{label}\". Each language variant "
                                    f"of an episode must be unique.",
                        ))
                    seen_group_lang[key] = ep.id

        if show.status == PublishStatus.published:
            has_poster = any(a.kind == "poster" for a in show.artworks)
            has_banner = any(a.kind == "banner" for a in show.artworks)
            if not has_poster:
                issues_by_show[show.id].append(ValidationIssue(
                    entity_type="show", entity_id=show.id, entity_label=label,
                    field="artwork", message=f'"{label}" is missing its poster image.',
                ))
            if not has_banner:
                issues_by_show[show.id].append(ValidationIssue(
                    entity_type="show", entity_id=show.id, entity_label=label,
                    field="artwork", message=f'"{label}" is missing its banner image.',
                ))

    count = sum(len(v) for v in issues_by_show.values())
    return ValidationReport(
        generated_at=datetime.utcnow(),
        blocking_issue_count=count,
        issues_by_show=dict(issues_by_show),
    )
