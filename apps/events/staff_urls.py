from django.urls import path
from .views import StaffAssignedEventsView

urlpatterns = [
    path('assigned/', StaffAssignedEventsView.as_view(), name='staff-assigned-events'),
]