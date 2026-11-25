"""Staff-only member record routes."""

from django.urls import path

from .views import StaffMemberDetailView

urlpatterns = [
    path("<int:user_id>/", StaffMemberDetailView.as_view(), name="staff-member-detail"),
]
