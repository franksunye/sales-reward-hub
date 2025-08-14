# 奖励翻倍通知功能修复计划

## 问题描述

目前系统中存在两个与奖励翻倍通知相关的BUG：

1. **上海技术工程师错误参与奖励翻倍**：上海的技术工程师无"徽章"，并不应参与奖励翻倍活动，但当前系统中他们也参与了进来。

2. **北京幸运数字奖励错误翻倍**：北京只有节节高奖励才会参与奖励翻倍，但当前系统中幸运数字奖励也有翻倍提示。

这两个问题都发生在通知模块中，导致发送给活动运营负责人的消息出现错误。

## 根本原因分析

通过代码审查，我们发现问题出在 `notification_module.py` 文件的 `generate_award_message` 函数中：

1. 当前实现没有区分城市，所有带有精英徽章的管家（包括上海的）都会获得奖励翻倍。
2. 当前实现没有区分奖励类型，所有奖励（包括幸运数字奖励）都会被翻倍。

## 修复方案

我们将修改 `generate_award_message` 函数，添加以下逻辑：

1. 添加城市参数，只有北京的精英管家才能获得奖励翻倍。
2. 添加奖励类型检查，只有"节节高"类型的奖励才会被翻倍。

### 代码修改计划

1. 修改 `generate_award_message` 函数签名，添加 `city` 参数：
   ```python
   def generate_award_message(record, awards_mapping, city="BJ"):
   ```

2. 修改奖励翻倍逻辑，增加城市和奖励类型检查：
   ```python
   if ENABLE_BADGE_MANAGEMENT and (service_housekeeper in ELITE_HOUSEKEEPER) and city == "BJ":
       # 添加徽章
       service_housekeeper = f'{BADGE_NAME}{service_housekeeper}'
       for award in record["奖励名称"].split(', '):
           if award in awards_mapping:
               award_info = awards_mapping[award]
               # 检查奖励类型，只有节节高奖励才翻倍
               reward_type = record["奖励类型"].split(', ')[record["奖励名称"].split(', ').index(award)] if len(record["奖励类型"].split(', ')) == len(record["奖励名称"].split(', ')) else ""
               if reward_type == "节节高":
                   try:
                       award_info_double = str(int(award_info) * 2)
                       award_messages.append(f'达成 {award} 奖励条件，奖励金额 {award_info} 元，同时触发"精英连击双倍奖励"，奖励金额\U0001F680直升至 {award_info_double} 元！\U0001F9E7\U0001F9E7\U0001F9E7')
                   except ValueError:
                       award_messages.append(f'达成{award}奖励条件，获得签约奖励{award_info}元 \U0001F9E7\U0001F9E7\U0001F9E7')
               else:
                   award_messages.append(f'达成{award}奖励条件，获得签约奖励{award_info}元 \U0001F9E7\U0001F9E7\U0001F9E7')
   ```

3. 修改调用 `generate_award_message` 的函数，传入正确的城市参数：
   - 在 `notify_awards_may_beijing` 和 `notify_awards_apr_beijing` 函数中传入 "BJ"
   - 在 `notify_awards_shanghai_generate_message_march` 函数中传入 "SH"

## 测试计划

1. **单元测试**：
   - 测试北京精英管家的节节高奖励是否正确翻倍
   - 测试北京精英管家的幸运数字奖励是否不再翻倍
   - 测试上海管家的奖励是否都不再翻倍

2. **集成测试**：
   - 使用测试数据运行完整的通知流程
   - 验证发送的消息内容是否符合预期

3. **回归测试**：
   - 确保修改不会影响其他功能
   - 验证所有通知功能仍然正常工作

## 部署计划

1. 在主干分支上进行修复
2. 完成测试后，部署到生产环境
3. 监控系统运行情况，确保问题已解决

## 时间线

1. 代码修改：1小时
2. 测试：2小时
3. 部署：30分钟
4. 验证：1小时

总计：约4.5小时

## 责任人

- 开发：Frank和AI助手
- 测试：Frank
- 部署：Frank
