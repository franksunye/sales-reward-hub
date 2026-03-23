# Backlog (Production)

最后更新: 2026-03-23
范围: 北京签约播报（Metabase -> Turso/SQLite -> Outbox -> 企业微信Webhook）

## P0
- [ ] 增加 `notification_outbox` 运维查询脚本（sent/failed/dead_letter 统计）
- [ ] 增加补发脚本（按 `activity_code` + `status` + 时间窗口补发）
- [ ] 增加死信告警（`dead_letter > 0`）
- [ ] 增加 webhook 失败率告警（连续失败阈值）

## P1
- [ ] 月度累计切换方案（`BJ-SIGN-BROADCAST-YYYY-MM`）
- [ ] 消息模板版本化（便于审计某次发送使用的模板）
- [ ] 增加 outbox 保留策略（按月归档历史成功记录）
- [ ] 增加手动回放 Runbook（含 SQL 与操作步骤）

## P2
- [ ] 增加可视化运营报表（发送量、成功率、重试次数、死信）
- [ ] 统一 docs 结构（active / archive）并补迁移脚本

## 发布后检查清单
- [ ] GitHub Actions 最近 3 次定时执行全部成功
- [ ] Turso 中 `performance_data.notification_sent` 与 `notification_outbox.status='sent'` 对齐
- [ ] 企业微信测试群抽样消息内容正确
- [ ] 无 `dead_letter` 记录
