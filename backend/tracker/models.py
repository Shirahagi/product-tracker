from django.db import models

class Item(models.Model):
    barcode = models.CharField(max_length=100, unique=True, verbose_name="条码")
    name = models.CharField(max_length=100, blank=True, verbose_name="货物名称")
    intended_target = models.CharField(max_length=100, blank=True, null=True, verbose_name="预定目标通道")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最后更新时间")
    last_channel = models.CharField(max_length=100, default="未分流", verbose_name="最近分流通道")

    def __str__(self):
        return self.barcode

class ScanRecord(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='scan_records', verbose_name="关联货物")
    target_channel = models.CharField(max_length=100, verbose_name="分流通道", default="未分流")
    scanned_at = models.DateTimeField(auto_now_add=True, verbose_name="扫码时间")

    def __str__(self):
        return f"{self.item.barcode} at {self.target_channel}"
    
class RoutingRule(models.Model):
    # 根据条码的前几位来判定去向（比如 "A" 开头的去通道 1）
    code_prefix = models.CharField(max_length=50, unique=True, verbose_name="条码前缀")
    target_channel = models.CharField(max_length=50, verbose_name="目标通道")
    
    def __str__(self):
        return f"码[{self.code_prefix}] -> {self.target_channel}"