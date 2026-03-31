import pandas as pd
import traceback
from django.core.management.base import BaseCommand
from tracker.models import ProductionLine, Station, RoutingRule

class Command(BaseCommand):
    help = '从 Excel 一键导入全线配置'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Excel文件的路径')

    def handle(self, *args, **options):
        file_path = options['excel_file']
        self.stdout.write(f"正在处理配置文件: {file_path}...")

        try:
            # --- 1. 处理分流规则 (Rules Sheet) ---
            self.stdout.write("正在同步 Rules (分流规则)...")
            df_rules = pd.read_excel(file_path, sheet_name='Rules')
            
            # 自动清洗数据：去掉全空的行，去掉包含 --- 的装饰行
            df_rules = df_rules.dropna(how='all')
            
            RoutingRule.objects.all().delete()
            for index, row in df_rules.iterrows():
                # 检查你的 Rules 表头是否叫 '条码前缀' 和 '目标通道ID'
                # 使用 .iloc[0] 这种方式按位置读取，更稳健
                prefix = str(row.iloc[0]).strip()
                target = str(row.iloc[1]).strip()
                
                if '---' in prefix or 'nan' in prefix.lower():
                    continue
                
                RoutingRule.objects.create(code_prefix=prefix, target_channel=target)
            
            self.stdout.write(self.style.SUCCESS('✅ 分流规则同步成功'))

            # --- 2. 处理产线和工位 (Stations Sheet) ---
            self.stdout.write("正在同步 Stations (产线与工位)...")
            df_stations = pd.read_excel(file_path, sheet_name='Stations')
            df_stations = df_stations.dropna(how='all')
            
            # 过滤掉包含 --- 的行
            df_stations = df_stations[~df_stations.iloc[:, 0].astype(str).str.contains('---')]

            # 根据第二列（产线编码）分组
            # 你的表头：产品名(0), 产线编码(1), 工位名(2), 逻辑ID(3), 类型(4)...
            for line_code, group in df_stations.groupby(df_stations.columns[1]):
                line_name = group.iloc[0, 0] # 第一列是产品名
                
                line, _ = ProductionLine.objects.update_or_create(
                    code=str(line_code).strip(),
                    defaults={'name': str(line_name).strip()}
                )
                line.stations.all().delete()

                for _, row in group.iterrows():
                    # 严格对应你截图中的列顺序
                    Station.objects.create(
                        line=line,
                        name=str(row.iloc[2]),          # 工位名
                        station_id=str(row.iloc[3]),    # 逻辑ID
                        station_type=str(row.iloc[4]).lower().strip(), # 类型 (entry/sorting/exit)
                        tag_trigger=str(row.iloc[5]),   # 触发标签
                        tag_barcode=str(row.iloc[6]),   # 条码标签
                        tag_action=str(row.iloc[7]) if pd.notna(row.iloc[7]) else None, # 动作标签
                        loc_name_pass=str(row.iloc[8]), # 放行位置
                        loc_name_divert=str(row.iloc[9]) if pd.notna(row.iloc[9]) else "" # 转向位置名
                    )
            
            self.stdout.write(self.style.SUCCESS(f' 全线硬件及位置配置同步成功！'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f' 导入失败!'))
            # 打印详细的报错位置，这能告诉我们是哪一行代码崩了
            self.stdout.write(self.style.ERROR(traceback.format_exc()))