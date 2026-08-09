"""
Write-side business logic for the Itinerary application.

This module contains business operations that modify itinerary data.
Read-optimized database queries belong in selectors.py.
"""

from __future__ import annotations

from django.db import transaction

from apps.core.exceptions import BusinessRuleViolation
from apps.itinerary.models import (
    ItineraryDay,
    ItineraryItem,
)

_ORDER_GAP = 10


class NoRoomToInsert(BusinessRuleViolation):
    """
    Raised when two adjacent itinerary items have no ordering gap left.
    """

    default_message = (
        "No ordering gap available. "
        "The itinerary day requires renumbering."
    )

    default_code = "no_room_to_insert"


def add_item_to_day(
    *,
    day: ItineraryDay,
    title: str,
    order: int | None = None,
    use_transaction: bool = True,
    **extra_fields,
) -> ItineraryItem:
    """
    Append a new itinerary item to the end of a day.

    New items are assigned order values using the configured gap
    strategy (10, 20, 30, ...).

    ``order`` and ``use_transaction`` are optional performance controls
    for callers that already own the surrounding transaction and know the
    desired order. Existing callers keep the original behavior by using
    the defaults.
    """

    def _create() -> ItineraryItem:
        if order is None:
            last_item = (
                day.items
                .order_by("-order")
                .first()
            )

            next_order = (
                last_item.order + _ORDER_GAP
                if last_item
                else _ORDER_GAP
            )
        else:
            next_order = order

        return ItineraryItem.objects.create(
            day=day,
            title=title,
            order=next_order,
            **extra_fields,
        )

    if use_transaction:
        with transaction.atomic():
            return _create()

    return _create()


@transaction.atomic
def insert_item_between(
    *,
    day: ItineraryDay,
    title: str,
    before: ItineraryItem,
    after: ItineraryItem,
    **extra_fields,
) -> ItineraryItem:
    """
    Insert a new itinerary item between two existing items.

    If no ordering gap remains, the day is first renumbered.
    """

    gap = after.order - before.order

    if gap <= 1:
        renumber_day(day=day)

        before.refresh_from_db()
        after.refresh_from_db()

        gap = after.order - before.order

        if gap <= 1:
            raise NoRoomToInsert()

    new_order = before.order + (gap // 2)

    return ItineraryItem.objects.create(
        day=day,
        title=title,
        order=new_order,
        **extra_fields,
    )


@transaction.atomic
def renumber_day(
    *,
    day: ItineraryDay,
) -> None:
    """
    Reset every item's order to a clean

        10, 20, 30...

    sequence.

    This operation is only performed when ordering gaps have
    been exhausted.
    """

    items = list(
        day.items
        .order_by("order")
    )

    for index, item in enumerate(
        items,
        start=1,
    ):
        item.order = index * _ORDER_GAP

    ItineraryItem.objects.bulk_update(
        items,
        ["order"],
    )
