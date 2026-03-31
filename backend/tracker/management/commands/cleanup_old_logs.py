from django.core.management.base import BaseCommand
from tracker.models import ItemLog

class Command(BaseCommand):
    help = '清理超过7天的货物日志'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='保留天数（默认7天）'
        )

    def handle(self, *args, **options):
        days = options['days']
        deleted_count = ItemLog.cleanup_old_logs()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'成功删除 {deleted_count} 条超过 {days} 天的日志记录'
            )
        )
