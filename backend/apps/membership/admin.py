"""Django admin for membership. Decisions go through the API so they are audited."""

from django.contrib import admin

from .models import MembershipDocument, MembershipPlan, MembershipRequest, MembershipSubscription


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "currency",
        "duration_months",
        "requires_documents",
        "is_active",
    )
    list_filter = ("is_active", "currency", "requires_documents")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class MembershipDocumentInline(admin.TabularInline):
    model = MembershipDocument
    extra = 0
    can_delete = False
    readonly_fields = ("original_name", "content_type", "size", "object_key", "uploaded_at")

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(MembershipRequest)
class MembershipRequestAdmin(admin.ModelAdmin):
    """Read-only: payment, approval and rejection are done through the audited API."""

    list_display = ("user", "plan", "status", "amount", "currency", "created_at")
    list_filter = ("status", "plan")
    search_fields = ("user__username", "user__email", "payment_reference")
    inlines = (MembershipDocumentInline,)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


@admin.register(MembershipSubscription)
class MembershipSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "starts_at", "ends_at", "expired_at")
    list_filter = ("plan",)
    search_fields = ("user__username",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
