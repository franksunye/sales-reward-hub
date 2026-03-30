/**
 * Sales Reward Hub Precision Scheduler
 * 
 * 这个 Cloudflare Worker 作为精准调度器，根据不同 cron 触发不同 workflow。
 */

const CRON_SIGN_BROADCAST = "0,30 0-15 * * *";
const CRON_PENDING_ORDERS = "30 0 * * *";

export default {
  // Cron Trigger 入口
  async scheduled(event, env, ctx) {
    console.log(`⏰ Cron triggered at ${new Date().toISOString()} with cron=${event.cron}`);
    
    // 按 cron 路由触发 GitHub Actions workflows
    const result = await triggerGitHubWorkflows(env, { cron: event.cron });
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
      return new Response(JSON.stringify({
        service: 'Sales Reward Hub Scheduler',
        status: 'running',
        utc_time: now.toISOString(),
        github_repo: `${env.GITHUB_OWNER}/${env.GITHUB_REPO}`,
        schedules: getScheduleConfig(env)
      }, null, 2), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return new Response('Sales Reward Hub Scheduler - Use /status or /trigger', { status: 200 });
  }
};

function getScheduleConfig(env) {
  return {
    [CRON_SIGN_BROADCAST]: [
      env.GITHUB_WORKFLOW_SIGN_BROADCAST || 'beijing-signing-broadcast.yml'
    ],
    [CRON_PENDING_ORDERS]: [
      env.GITHUB_WORKFLOW_PENDING_ORDERS || 'pending-orders-reminder.yml'
    ],
  };
}

function getTargetWorkflows(env, options = {}) {
  const scheduleConfig = getScheduleConfig(env);

  if (options.cron && scheduleConfig[options.cron]) {
    return scheduleConfig[options.cron];
  }

  if (options.target === 'sign-broadcast') {
    return scheduleConfig[CRON_SIGN_BROADCAST];
  }

  if (options.target === 'pending-orders') {
    return scheduleConfig[CRON_PENDING_ORDERS];
  }

  return Array.from(new Set([
    ...scheduleConfig[CRON_SIGN_BROADCAST],
    ...scheduleConfig[CRON_PENDING_ORDERS],
  ]));
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
