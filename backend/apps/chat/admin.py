"""
Django admin configuration for the chat application.
"""

from django.contrib import admin

from .models import (
    ChatMessage,
    ChatSession,
)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """
    Administrative interface for ChatSession.
    """

    list_display = (
        "title",
        "trip",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "title",
        "trip__title",
    )

    list_select_related = (
        "trip",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """
    Administrative interface for ChatMessage.
    """

    list_display = (
        "session",
        "role",
        "short_content",
        "created_at",
    )

    list_filter = (
        "role",
        "created_at",
    )

    search_fields = (
        "content",
        "session__title",
        "session__trip__title",
    )

    list_select_related = (
        "session",
        "session__trip",
    )

    ordering = (
        "created_at",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Message")
    def short_content(
        self,
        obj: ChatMessage,
    ) -> str:
        """
        Display a shortened preview of the message.
        """

        if len(obj.content) <= 75:
            return obj.content

        return obj.content[:72] + "..."