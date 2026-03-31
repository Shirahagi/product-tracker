from django.contrib import admin
from .models import Item, ScanRecord, RoutingRule, ItemLog, ProductionLine, Station

# --- 1. 新增：工位内联配置 ---
# 这样你在编辑“产线”界面时，可以直接在下方增删“工位”
class StationInline(admin.TabularInline):
    model = Station
    extra = 1  # 默认显示一个空行供快速添加
    fields = ('name', 'station_id', 'station_type', 'tag_trigger', 'tag_barcode', 'tag_action')

# --- 2. 新增：产线管理 ---
@admin.register(ProductionLine)
class ProductionLineAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    inlines = [StationInline] # 关键：把工位管理嵌入产线页面

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'line', 'station_id', 'station_type')
    list_filter = ('line', 'station_type')
    search_fields = ('name', 'station_id')

# --- 3. 原有：货物管理 (进行了增强，加入了所属产线显示) ---
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    # list_display 加入了 'line'，方便看这件货属于哪条线
    list_display = ('barcode', 'line', 'intended_target', 'current_location', 'status', 'updated_at')
    list_filter = ('line', 'status', 'created_at')
    search_fields = ('barcode',)
    readonly_fields = ('created_at', 'updated_at')

# --- 4. 保持原有配置不变 ---
@admin.register(ScanRecord)
class ScanRecordAdmin(admin.ModelAdmin):
    list_display = ('item', 'target_channel', 'scanned_at')
    list_filter = ('scanned_at',)
    search_fields = ('item__barcode', 'target_channel')
    readonly_fields = ('scanned_at',)

@admin.register(RoutingRule)
class RoutingRuleAdmin(admin.ModelAdmin):
    list_display = ('code_prefix', 'target_channel')
    search_fields = ('code_prefix', 'target_channel')

@admin.register(ItemLog)
class ItemLogAdmin(admin.ModelAdmin):
    list_display = ('barcode', 'action', 'scanned_at')
    list_filter = ('scanned_at',)
    search_fields = ('barcode', 'action')
    readonly_fields = ('scanned_at',)
    date_hierarchy = 'scanned_at'