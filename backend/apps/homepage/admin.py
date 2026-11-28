"""Django admin registration for approved public website content."""

from django.contrib import admin

from .models import (
    ContentCard,
    ContentSection,
    FeaturedResource,
    FooterLink,
    Homepage,
    InstitutionalUpdate,
    PopularSearch,
    ResourceCategory,
)


@admin.register(Homepage)
class HomepageAdmin(admin.ModelAdmin):
    list_display = ("hero_title", "is_published", "updated_at", "updated_by")
    list_filter = ("is_published",)
    search_fields = ("hero_title",)
    readonly_fields = ("updated_at", "updated_by")

    def has_add_permission(self, request):
        return not Homepage.objects.exists()


@admin.register(PopularSearch)
class PopularSearchAdmin(admin.ModelAdmin):
    list_display = ("label", "query", "sort_order", "is_published")
    list_filter = ("is_published", "homepage")
    search_fields = ("label", "query")


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ("label", "slug", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("label", "slug")


@admin.register(ContentSection)
class ContentSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "sort_order", "is_published")
    list_filter = ("kind", "is_published")
    search_fields = ("title", "slug")


@admin.register(ContentCard)
class ContentCardAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "sort_order", "is_published")
    list_filter = ("is_published", "section")
    search_fields = ("title",)


@admin.register(FeaturedResource)
class FeaturedResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "resource_type", "source", "access", "is_published")
    list_filter = ("resource_type", "source", "access", "is_published")
    search_fields = ("title", "source_id")


@admin.register(InstitutionalUpdate)
class InstitutionalUpdateAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "published_at", "event_date", "is_published")
    list_filter = ("kind", "is_published")
    search_fields = ("title", "summary")


@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    list_display = ("label", "group", "url", "sort_order", "is_approved")
    list_filter = ("group", "is_approved")
    search_fields = ("label", "url")
