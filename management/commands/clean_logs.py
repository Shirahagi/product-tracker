from django.core.management.base import BaseCommand
from tracker.models import ScanRecord
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = '清理超过7天的历史日志'

    def handle(self, *args, **options):
        seven_days_ago = timezone.now() - timedelta(days=7)
        # 找到 7 天前的所有记录并删除
        deleted_count, _ = ScanRecord.objects.filter(scanned_at__lt=seven_days_ago).delete()
        self.stdout.write(self.style.SUCCESS(f'成功清理了 {deleted_count} 条旧日志'))