from django.db import models

class Item(models.Model):
    barcode = models.CharField(max_length=100, unique=True, verbose_name="条码")
    name = models.CharField(max_length=100, blank=True, verbose_name="货物名称")
    current_station = models.CharField(max_length=100, default="未上线", verbose_name="当前工位")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="最后更新时间")

    def __str__(self):
        return self.barcode

class ScanRecord(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='scan_records')
    station_name = models.CharField(max_length=100, verbose_name="扫码工位")
    scanned_at = models.DateTimeField(auto_now_add=True, verbose_name="扫码时间")

    def __str__(self):
        return f"{self.item.barcode} at {self.station_name}"