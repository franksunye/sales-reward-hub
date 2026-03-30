# Backlog (Production)

最后更新: 2026-03-30
范围: 北京签约播报 / 待预约工单提醒（Metabase -> Turso/SQLite -> Outbox -> 企业微信Webhook）

## P0
- [ ] 增加 `notification_outbox` 运维查询脚本（sent/failed/dead_letter 统计）
- [ ] 增加补发脚本（按 `activity_code` + `status` + 时间窗口补发）
- [ ] 增加死信告警（`dead_letter > 0`）
- [ ] 增加 webhook 失败率告警（连续失败阈值）

## P1
- [x] 月度累计切换方案（`BJ-SIGN-BROADCAST-YYYY-MM`）
- [ ] 消息模板版本化（便于审计某次发送使用的模板）
- [ ] 增加 outbox 保留策略（按月归档历史成功记录）
- [ ] 增加手动回放 Runbook（含 SQL 与操作步骤）
- [ ] 将通知路由配置从 `.env` / GitHub Secrets 迁移到数据库
  目标: 不再使用超长 `WECOM_WEBHOOK_PENDING_ORDERS_ORG_MAP` JSON，改为“业务通道 + 服务商 + webhook”的可维护模型
  建议: 新增通知路由表，支持默认路由与服务商专属路由；代码改为数据库优先、环境变量兜底；先迁移 `pending_orders_reminder`，后续复用到 `sign_broadcast` / SLA 等通道

## P2
- [ ] 增加可视化运营报表（发送量、成功率、重试次数、死信）
- [ ] 统一 docs 结构（active / archive）并补迁移脚本

## 发布后检查清单
- [ ] GitHub Actions 最近 3 次定时执行全部成功
- [ ] Turso 中 `performance_data.notification_sent` 与 `notification_outbox.status='sent'` 对齐
- [ ] 企业微信测试群抽样消息内容正确
- [ ] 无 `dead_letter` 记录
