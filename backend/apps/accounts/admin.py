"""Admin registration for accounts."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.audit.models import record_audit_event

from .models import UserAccount, UserRole


class UserRoleInline(admin.TabularInline):
    """Assign roles on the user page (ILMDAS-28)."""

    model = UserRole
    fk_name = "user"
    extra = 0
    fields = ("role", "assigned_at", "assigned_by")
    readonly_fields = ("assigned_at", "assigned_by")

    def has_change_permission(self, request, obj=None) -> bool:
        # Existing assignments are read-only: a change is a remove plus an add, so every
        # role change is audited as role.revoked / role.assigned (ILMDAS-31).
        return False


@admin.register(UserAccount)
class UserAccountAdmin(DjangoUserAdmin):
    ordering = ("username",)
    inlines = (UserRoleInline,)

    def save_formset(self, request, form, formset, change):
        """Audit role changes made here, as the role API does (ILMDAS-31)."""
        if formset.model is not UserRole:
            return super().save_formset(request, form, formset, change)

        added = formset.save(commit=False)
        for assignment in formset.deleted_objects:
            _audit_role_change(request, "role.revoked", assignment)
            assignment.delete()
        for assignment in added:
            assignment.assigned_by = request.user
            assignment.save()
            _audit_role_change(request, "role.assigned", assignment)
        formset.save_m2m()

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


def _audit_role_change(request, action: str, assignment: UserRole) -> None:
    record_audit_event(
        action=action,
        actor=request.user,
        object_type="UserRole",
        object_id=str(assignment.user_id),
        details={
            "target_user": assignment.user.username,
            "role_code": assignment.role.code,
            "role_name": assignment.role.name,
            "via": "admin",
        },
        request=request,
    )
