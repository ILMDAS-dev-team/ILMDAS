"""Admin registration for accounts."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import UserAccount, UserRole


class UserRoleInline(admin.TabularInline):
    """Assign roles on the user page (ILMDAS-28)."""

    model = UserRole
    fk_name = "user"
    extra = 0
    fields = ("role", "assigned_at", "assigned_by")
    readonly_fields = ("assigned_at", "assigned_by")


@admin.register(UserAccount)
class UserAccountAdmin(DjangoUserAdmin):
    ordering = ("username",)
    inlines = (UserRoleInline,)
    list_display = ("username", "email", "status", "is_staff", "date_joined", "last_login")
    list_filter = ("user_roles__role", "status", "is_staff", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "status",
                    "is_staff",
                ),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")
