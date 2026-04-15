/**
 * Sales Reward Hub Precision Scheduler
 *
 * 这个 Cloudflare Worker 只保留一个 cron 心跳：
 * - 北京时间 08:00-23:30，每 30 分钟触发一次
 *
 * 然后在 Worker 内部根据北京时间路由不同 workflow：
 * - 每个心跳都触发北京签约播报
 * - 每个心跳都触发项目结算电子表格同步
 * - 08:30 额外触发待预约工单提醒
 * - 09:00 额外触发 SLA 日报
 */

const CRON_HEARTBEAT = "0,30 0-15 * * *";

export default {
  // Cron Trigger 入口
  async scheduled(event, env, ctx) {
    console.log(`⏰ Cron triggered at ${new Date().toISOString()} with cron=${event.cron}`);

    // 按北京时间路由触发 GitHub Actions workflows
    const result = await triggerGitHubWorkflows(env, { now: new Date() });
    console.log(`✅ GitHub Actions triggered:`, result);
  },
  
  // HTTP 请求入口 (用于手动测试)
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    if (url.pathname === '/trigger') {
      // 手动触发 (用于测试)
      const target = url.searchParams.get('target') || 'all';
      const result = await triggerGitHubWorkflows(env, { target });
      return new Response(JSON.stringify(result, null, 2), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    if (url.pathname === '/status') {
      // 状态检查
      const now = new Date();
      const routing = getTimeBasedScheduleConfig(env);
      return new Response(JSON.stringify({
        service: 'Sales Reward Hub Scheduler',
        status: 'running',
        utc_time: now.toISOString(),
        github_repo: `${env.GITHUB_OWNER}/${env.GITHUB_REPO}`,
        schedules: {
          cron: CRON_HEARTBEAT,
          timezone: "Asia/Shanghai",
          routing,
        }
      }, null, 2), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return new Response('Sales Reward Hub Scheduler - Use /status or /trigger', { status: 200 });
  }
};

function getWorkflowNames(env) {
  return {
    signBroadcast: env.GITHUB_WORKFLOW_SIGN_BROADCAST || 'beijing-signing-broadcast.yml',
    projectSettlementSmartsheet: env.GITHUB_WORKFLOW_PROJECT_SETTLEMENT_SMARTSHEET || 'project-settlement-smartsheet.yml',
    pendingOrders: env.GITHUB_WORKFLOW_PENDING_ORDERS || 'pending-orders-reminder.yml',
    dailyServiceReport: env.GITHUB_WORKFLOW_DAILY_SERVICE_REPORT || 'daily-service-report.yml',
  };
}

function getTimeBasedScheduleConfig(env) {
  const workflows = getWorkflowNames(env);
  return {
    "08:00-23:30/30m": [workflows.signBroadcast, workflows.projectSettlementSmartsheet],
    "08:30": [workflows.pendingOrders],
    "09:00": [workflows.dailyServiceReport],
  };
}

function getTargetWorkflows(env, options = {}) {
  const workflows = getWorkflowNames(env);

  if (options.target === 'sign-broadcast') {
    return [workflows.signBroadcast];
  }

  if (options.target === 'project-settlement-smartsheet') {
    return [workflows.projectSettlementSmartsheet];
  }

  if (options.target === 'pending-orders') {
    return [workflows.pendingOrders];
  }

  if (options.target === 'daily-service-report') {
    return [workflows.dailyServiceReport];
  }

  if (options.target === 'all') {
    return [workflows.signBroadcast, workflows.projectSettlementSmartsheet, workflows.pendingOrders, workflows.dailyServiceReport];
  }

  const current = options.now instanceof Date ? options.now : new Date();
  const shanghai = getShanghaiParts(current);
  const targetWorkflows = [workflows.signBroadcast, workflows.projectSettlementSmartsheet];

  if (shanghai.hour === 8 && shanghai.minute === 30) {
    targetWorkflows.push(workflows.pendingOrders);
  }

  if (shanghai.hour === 9 && shanghai.minute === 0) {
    targetWorkflows.push(workflows.dailyServiceReport);
  }

  return targetWorkflows;
}

function getShanghaiParts(date) {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });

  const parts = formatter.formatToParts(date);
  const lookup = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return {
    year: Number(lookup.year),
    month: Number(lookup.month),
    day: Number(lookup.day),
    hour: Number(lookup.hour),
    minute: Number(lookup.minute),
  };
}

async function triggerSingleGitHubWorkflow(env, workflow) {
  const { GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO } = env;
  
  if (!GITHUB_TOKEN || !GITHUB_OWNER || !GITHUB_REPO) {
    return { success: false, error: 'Missing required environment variables (GITHUB_TOKEN, GITHUB_OWNER, or GITHUB_REPO)' };
  }
  
  const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/${workflow}/dispatches`;
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Accept': 'application/vnd.github.v3+json',
      'Authorization': `Bearer ${GITHUB_TOKEN}`,
      'User-Agent': 'Sales-Reward-Scheduler',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ref: 'main'  // 目标分支
    })
  });
  
  if (response.status === 204) {
    return { workflow, success: true, message: 'Workflow triggered successfully' };
  }
  
  const errorText = await response.text();
  return { 
    workflow,
    success: false, 
    status: response.status,
    error: errorText 
  };
}

async function triggerGitHubWorkflows(env, options = {}) {
  const workflows = getTargetWorkflows(env, options);
  const results = [];

  for (const workflow of workflows) {
    results.push(await triggerSingleGitHubWorkflow(env, workflow));
  }

  return {
    workflows,
    results,
    success: results.every((item) => item.success),
  };
}
