@echo off
echo 正在同步产线配置，请稍候...
call venv\Scripts\activate
python backend\manage.py load_config config.xlsx
echo 同步完成！现在可以启动系统了。
pause