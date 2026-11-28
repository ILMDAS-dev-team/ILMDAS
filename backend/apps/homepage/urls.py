"""Homepage routes: one public read endpoint and role-guarded content endpoints."""

from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    ContentCardViewSet,
    ContentSectionViewSet,
    FeaturedResourceViewSet,
    FooterLinkViewSet,
    HomepageManageViewSet,
    HomepageView,
    InstitutionalUpdateViewSet,
    PopularSearchViewSet,
    ResourceCategoryViewSet,
)

router = SimpleRouter()
router.register("website/manage/homepage", HomepageManageViewSet, basename="website-homepage")
router.register(
    "website/manage/popular-searches", PopularSearchViewSet, basename="website-popular-search"
)
router.register("website/manage/categories", ResourceCategoryViewSet, basename="website-category")
router.register("website/manage/sections", ContentSectionViewSet, basename="website-section")
router.register("website/manage/cards", ContentCardViewSet, basename="website-card")
router.register(
    "website/manage/featured-resources", FeaturedResourceViewSet, basename="website-featured"
)
router.register("website/manage/updates", InstitutionalUpdateViewSet, basename="website-update")
router.register("website/manage/footer-links", FooterLinkViewSet, basename="website-footer-link")

urlpatterns = [
    path("website/home/", HomepageView.as_view(), name="website-home"),
    *router.urls,
]
