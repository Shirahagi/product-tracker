from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('items/', views.get_items),
    path('scan/', views.manual_scan),
    path('manual-scan/', views.manual_scan),
    path('update-channel/<int:item_id>/', views.update_item_channel),
    path('item-logs/<str:barcode>/', views.get_item_logs),
    path('all-logs/', views.get_all_logs),
    path('channels/', views.get_routing_channels),
    path('simulate/', views.simulate_hardware),
    path('sorting-logic/', views.sorting_logic),
    path('config/', views.get_system_config),
    path('upload-config/', views.upload_config),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")