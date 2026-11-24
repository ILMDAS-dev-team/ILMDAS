"""Admin registration for accounts."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import UserAccount


@admin.register(UserAccount)
class UserAccountAdmin(DjangoUserAdmin):
    ordering = ("username",)
    list_display = ("username", "status", "is_staff", "date_joined", "last_login")
    list_filter = ("status", "is_staff", "is_superuser")
    search_fields = ("username",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Status",
            {"fields": ("status", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "status", "is_staff"),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")
