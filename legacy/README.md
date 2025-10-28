# 旧架构代码备份

本目录包含已移除的旧架构代码（8月、9月job）。

## 文件说明

- jobs.py - 旧job定义（8月、9月）
- modules/data_processing_module.py - 旧数据处理函数
- modules/notification_module.py - 旧通知函数

## 恢复方法

如需恢复旧代码，可使用以下命令：

\\\ash
git checkout backup/legacy-code -- legacy/
\\\

## 新架构位置

新架构代码位于：
- modules/core/beijing_jobs.py - 新job定义
- modules/core/shanghai_jobs.py - 新job定义
- modules/core/processing_pipeline.py - 新数据处理
- modules/core/notification_service.py - 新通知服务

## 备份时间

创建于: 2025-10-28 17:46:01
