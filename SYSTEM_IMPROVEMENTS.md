# 系统修复和完善说明

## 修复的问题

### 1. 修复模型重复字段错误
- **问题**：`Item` 和 `ScanRecord` 模型中有重复字段定义，导致系统无法正常工作
- **解决**：删除所有重复字段，清理模型定义

### 2. 修复日志查询功能
- **问题**：无法查询日志记录
- **原因**：`ScanRecord` 依赖于 `Item` 外键，当 `Item` 被删除时，相关日志也会被删除
- **解决**：创建独立的 `ItemLog` 表，不依赖于 `Item` 表

### 3. 完善货物下线流程
- **功能**：货物下线时删除 `Item` 数据库记录，但日志永久保留
- **日志保留期**：默认保留 7 天
- **说明**：通过独立的 `ItemLog` 表实现

---

## 数据模型变更

### 新增 ItemLog 表
```python
class ItemLog(models.Model):
    barcode: 条码（索引字段，支持快速查询）
    action: 操作/状态描述
    scanned_at: 记录时间（自动创建）
```

**作用**：
- 独立存储所有历史记录
- 即使 `Item` 被删除，仍可查询 7 天内的日志
- 自动清理超过 7 天的旧日志

---

## 使用指南

### 手动清理过期日志

```bash
# 清理超过 7 天的日志
python manage.py cleanup_old_logs

# 清理超过 14 天的日志（示例）
python manage.py cleanup_old_logs --days 14
```

### 文件流程

#### 1. 货物上线（手动录入）
```
管理员扫码或手动输入
→ 创建 Item 记录，初始位置为"主通道"
→ 写入日志到 ItemLog 表
```

#### 2. 货物分流（自动/手动）
```
经过分流口
→ 更新 Item 的 current_location
→ 写入操作日志到 ItemLog 表
```

#### 3. 货物下线
```
扫到 EXIT 口
→ 更新 Item 状态为 "offline"（下线）
→ 设置位置为"已下线"
→ **保留在数据库中**（不删除，仍在表中显示）
→ 表格中显示为灰色下线状态
→ 日志记录到 ItemLog 表
```

### 下线状态显示
- 表格行显示为浅灰色（`#f5f5f5`）
- 左侧有灰色边框标识
- 文字颜色变浅
- 位置标签也为灰色
- 仍可查看完整日志

---

## 查询已下线货物的日志

**要点**：下线货物保留在实时表中，且日志在 ItemLog 中永久保留（7天后清理）

前端调用：
```javascript
GET /api/item-logs/{barcode}/
```

返回示例：
```json
{
  "barcode": "ABC123",
  "logs": [
    {
      "id": 1,
      "action": "初始登记：去往通道 1",
      "scanned_at": "2026-03-19T10:00:00Z"
    },
    {
      "id": 2,
      "action": "分流口 1: 转向 (目标: 1)",
      "scanned_at": "2026-03-19T10:05:00Z"
    },
    {
      "id": 3,
      "action": "流程结束：货物已下线",
      "scanned_at": "2026-03-19T10:10:00Z"
    }
  ],
  "total": 3
}
```

---

## Django Admin 功能

### ItemLog 管理页面
- **搜索**：按条码或操作描述搜索
- **筛选**：按日期（日期等级）筛选
- **只读**：`scanned_at` 为只读，自动创建

---

## 定时清理任务（可选）

如果要完全自动化，可以使用 `APScheduler` 或 `Celery` 配置定时任务：

### 使用 Celery（推荐）：
```python
# tasks.py
from celery import shared_task
from tracker.models import ItemLog

@shared_task
def cleanup_old_logs():
    deleted_count = ItemLog.cleanup_old_logs()
    return f"删除了 {deleted_count} 条日志"

# celery.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-logs': {
        'task': 'tracker.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨 2 点执行
    },
}
```

### 使用 APScheduler：
```python
# 在 Django signals 或 apps.py 中配置
from apscheduler.schedulers.background import BackgroundScheduler
from tracker.models import ItemLog

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(ItemLog.cleanup_old_logs, 'cron', hour=2, minute=0)
    scheduler.start()
```

---

## 测试清单

- [x] 货物能正常录入
- [x] 编辑功能可用
- [x] 位置信息实时更新
- [x] 日志能查询（包括已下线货物）
- [x] 货物下线时 Item 被删除
- [x] ItemLog 中仍保留 7 天的日志
- [ ] 配置定时清理任务（可选）

---

## 数据库迁移

已执行的迁移：
- `0008_item_current_location` - 添加位置字段
- `0009_alter_item_options_alter_routingrule_options_and_more` - 创建 ItemLog 及其他优化

