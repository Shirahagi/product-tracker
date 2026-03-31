from django.core.management.base import BaseCommand
from tracker.models import Item, ItemLog, ScanRecord
from django.utils import timezone
from datetime import timedelta
import random

class Command(BaseCommand):
    help = '生成测试数据 (200条货物)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=200,
            help='生成数据条数（默认200）'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # 清理旧数据（可选）
        # Item.objects.all().delete()
        # ItemLog.objects.all().delete()
        
        # 配置
        channels = ['通道1', '通道2', '通道3']
        locations = ['主通道', '分流1', '分流2', '分流3', '通道1-2', '通道2-3', '主线末端', '已下线']
        statuses = ['online', 'offline']
        
        created_count = 0
        
        for i in range(count):
            # 生成条码（格式：A/B/C开头 + 5位数字）
            prefix = random.choice(['A', 'B', 'C'])
            barcode = f"{prefix}{str(i+1).zfill(6)}"
            
            # 检查是否已存在
            if Item.objects.filter(barcode=barcode).exists():
                continue
            
            # 随机选择配置
            intended_target = random.choice(channels)
            current_location = random.choice(locations)
            status = random.choice(statuses)
            
            # 生成创建时间（最近30天内）
            days_ago = random.randint(0, 29)
            created_time = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            # 创建 Item
            item = Item.objects.create(
                barcode=barcode,
                name=f"产品_{barcode}",
                intended_target=intended_target,
                current_location=current_location,
                status=status,
                last_channel=f"自动登记：去往{intended_target}",
            )
            
            # 覆盖时间戳（因为 auto_now_add 会自动设置为现在）
            item.created_at = created_time
            item.updated_at = created_time
            item.save(update_fields=['created_at', 'updated_at'])
            
            # 为该货物创建 3-8 条日志
            log_count = random.randint(3, 8)
            current_time = created_time
            
            for j in range(log_count):
                # 日志时间递进
                current_time = current_time + timedelta(hours=random.randint(1, 4), minutes=random.randint(0, 59))
                
                action_templates = [
                    f"初始登记：去往{intended_target}",
                    "分流口 1: 放行 (目标: 通道2)",
                    "分流口 2: 转向 (目标: 通道2)",
                    "分流口 3: 放行 (目标: 通道1)",
                    "人工干预：强制重导向至通道1",
                    "流程结束：货物已下线",
                ]
                
                action = random.choice(action_templates)
                
                # 创建 ItemLog（永久日志）
                ItemLog.objects.create(
                    barcode=barcode,
                    action=action,
                    scanned_at=current_time
                )
                
                # 创建 ScanRecord（在线日志）
                if status == 'online':
                    ScanRecord.objects.create(
                        item=item,
                        target_channel=action,
                        scanned_at=current_time
                    )
            
            created_count += 1
            
            if (created_count) % 50 == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'已生成 {created_count} 条数据...')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n成功生成 {created_count} 条测试数据！')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  - Item 表：{created_count} 条')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  - ItemLog 表：约 {created_count * 5} 条')
        )
        self.stdout.write(
            self.style.SUCCESS(f'  - ScanRecord 表：约 {created_count * 4} 条（在线货物）')
        )
