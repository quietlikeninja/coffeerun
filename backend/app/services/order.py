from app.schemas.order import ConsolidatedItem


def format_order_line(
    count: int,
    size_abbreviation: str,
    drink_type_name: str,
    milk_option_name: str | None,
    sugar: int,
    notes: str | None,
) -> str:
    parts = [f"{count}x {size_abbreviation}"]
    if milk_option_name:
        parts.append(milk_option_name)
    parts.append(drink_type_name)

    extras = []
    if sugar > 0:
        extras.append(f"{sugar} sugar{'s' if sugar > 1 else ''}")
    line = " ".join(parts)
    if extras:
        line += ", " + ", ".join(extras)
    if notes:
        line += f" ({notes})"
    return line


def consolidate_order_items(items: list[dict]) -> list[ConsolidatedItem]:
    """Group identical order items and produce consolidated summary."""
    groups: dict[tuple, dict] = {}
    for item in items:
        key = (
            item["drink_type_name"],
            item["size_name"],
            item["size_abbreviation"],
            item["milk_option_name"],
            item["sugar"],
            (item.get("notes") or "").strip().lower(),
        )
        if key not in groups:
            groups[key] = {**item, "count": 0, "original_notes": item.get("notes")}
        groups[key]["count"] += 1

    consolidated = []
    for key, group in groups.items():
        display_text = format_order_line(
            count=group["count"],
            size_abbreviation=group["size_abbreviation"],
            drink_type_name=group["drink_type_name"],
            milk_option_name=group["milk_option_name"],
            sugar=group["sugar"],
            notes=group["original_notes"],
        )
        consolidated.append(
            ConsolidatedItem(
                count=group["count"],
                drink_type_name=group["drink_type_name"],
                size_name=group["size_name"],
                size_abbreviation=group["size_abbreviation"],
                milk_option_name=group["milk_option_name"],
                sugar=group["sugar"],
                notes=group["original_notes"],
                display_text=display_text,
            )
        )

    # Sort by count descending, then alphabetically
    consolidated.sort(key=lambda x: (-x.count, x.display_text))
    return consolidated
