from django.db import models
from django.utils import timezone
from datetime import timedelta

class Item(models.Model):
    barcode = models.CharField(max_length=100, unique=True, verbose_name="条码")
    name = models.CharField(max_length=100, blank=True, verbose_name="货物名称")
    intended_target = models.CharField(max_length=100, blank=True, null=True, verbose_name="预定目标通道")
    current_location = models.CharField(max_length=100, blank=True, default="待定位", verbose_name="当前位置")
    last_channel = models.CharField(max_length=100, default="未分流", verbose_name="最近分流通道")
    status = models.CharField(max_length=20, default="online", verbose_name="状态") # online / offline
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="上线时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    line = models.ForeignKey('ProductionLine', on_delete=models.SET_NULL, null=True, blank=True, related_name='items', verbose_name="所属产线")
    
    

    def __str__(self):
        return self.barcode

    class Meta:
        verbose_name = "货物"
        verbose_name_plural = "货物列表"


class ItemLog(models.Model):
    """独立的日志表，在 Item 被删除后仍可查询，自动保留7天"""
    barcode = models.CharField(max_length=100, db_index=True, verbose_name="条码")
    action = models.CharField(max_length=200, verbose_name="操作/状态")
    scanned_at = models.DateTimeField(auto_now_add=True, verbose_name="记录时间", db_index=True)

    def __str__(self):
        return f"{self.barcode} - {self.action} - {self.scanned_at}"

    class Meta:
        verbose_name = "货物日志"
        verbose_name_plural = "货物日志列表"
        ordering = ['-scanned_at']
        indexes = [
            models.Index(fields=['barcode', '-scanned_at']),
        ]

    @staticmethod
    def cleanup_old_logs():
        """清理超过7天的日志"""
        cutoff_date = timezone.now() - timedelta(days=7)
        deleted_count, _ = ItemLog.objects.filter(scanned_at__lt=cutoff_date).delete()
        return deleted_count


class ScanRecord(models.Model):
    """扫码记录（在线货物，关联到Item）"""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='scan_records', verbose_name="关联货物")
    target_channel = models.CharField(max_length=100, verbose_name="分流通道", default="未分流")
    scanned_at = models.DateTimeField(auto_now_add=True, verbose_name="扫码时间")

    def __str__(self):
        return f"{self.item.barcode} at {self.target_channel}"

    class Meta:
        verbose_name = "扫码记录"
        verbose_name_plural = "扫码记录列表"

    
class RoutingRule(models.Model):
    # 根据条码的前几位来判定去向（比如 "A" 开头的去通道 1）
    code_prefix = models.CharField(max_length=50, unique=True, verbose_name="条码前缀")
    target_channel = models.CharField(max_length=50, verbose_name="目标通道")
    
    def __str__(self):
        return f"码[{self.code_prefix}] -> {self.target_channel}"

    class Meta:
        verbose_name = "路由规则"
        verbose_name_plural = "路由规则列表"

class ProductionLine(models.Model):
    """产线模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name="产线名称")
    code = models.CharField(max_length=50, unique=True, verbose_name="产线编码") # 如 Line_1

    def __str__(self):
        return self.name

class Station(models.Model):
    STATION_TYPES = [
        ('entry', '起点/上线'),
        ('sorting', '分流/中转'),
        ('exit', '终点/下线'),
    ]
    
    line = models.ForeignKey(ProductionLine, related_name='stations', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name="工位名称") # 如：1号分流口
    station_id = models.CharField(max_length=50, verbose_name="逻辑ID") # 如：1
    station_type = models.CharField(max_length=20, choices=STATION_TYPES)
    
    # 1. KEP 硬件地址
    tag_trigger = models.CharField(max_length=255, verbose_name="触发标签")
    tag_barcode = models.CharField(max_length=255, verbose_name="条码标签")
    tag_action = models.CharField(max_length=255, blank=True, null=True, verbose_name="动作标签")

    # 2. 动态位置描述 (解决 loc_map 问题)
    loc_name_pass = models.CharField(max_length=100, verbose_name="放行后显示的位置", default="", help_text="如：通道 1-2")
    loc_name_divert = models.CharField(max_length=100, verbose_name="转向后显示的位置", default="", help_text="如：分流 1")

    def __str__(self):
        return f"{self.line.name} - {self.name}"

    class Meta:
        verbose_name = "工位配置"
        verbose_name_plural = "工位配置列表"