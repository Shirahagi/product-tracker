from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.get_items),
    path('scan/', views.manual_scan),
    path('manual-scan/', views.manual_scan),
    path('update-channel/<int:item_id>/', views.update_item_channel),
    path('item-logs/<int:item_id>/', views.get_item_logs),
    path('channels/', views.get_routing_channels),
    path('simulate/', views.simulate_hardware),
    path('sorting-logic/', views.sorting_logic),
]