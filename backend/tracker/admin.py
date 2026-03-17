from django.contrib import admin
from .models import Item, ScanRecord, RoutingRule

admin.site.register(Item)
admin.site.register(ScanRecord)
admin.site.register(RoutingRule)