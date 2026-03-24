/**
 * Sales Reward Hub Precision Scheduler
 * 
 * 这个 Cloudflare Worker 作为精准调度器，每 30 分钟运行一次。
 * 它会触发 GitHub Actions 中的 beijing-signing-broadcast.yml。
 */

export default {
  // Cron Trigger 入口
  async scheduled(event, env, ctx) {
    console.log(`⏰ Cron triggered at ${new Date().toISOString()}`);
    
    // 触发 GitHub Actions workflow
    const result = await triggerGitHubWorkflow(env);
    console.log(`✅ GitHub Actions triggered:`, result);
  },
  
  // HTTP 请求入口 (用于手动测试)
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    if (url.pathname === '/trigger') {
      // 手动触发 (用于测试)
      const result = await triggerGitHubWorkflow(env);
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
        workflow: env.GITHUB_WORKFLOW
      }, null, 2), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return new Response('Sales Reward Hub Scheduler - Use /status or /trigger', { status: 200 });
  }
};

async function triggerGitHubWorkflow(env) {
  const { GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, GITHUB_WORKFLOW } = env;
  
  if (!GITHUB_TOKEN || !GITHUB_OWNER || !GITHUB_REPO) {
    return { success: false, error: 'Missing required environment variables (GITHUB_TOKEN, GITHUB_OWNER, or GITHUB_REPO)' };
  }
  
  const targetWorkflow = GITHUB_WORKFLOW || 'beijing-signing-broadcast.yml';
  const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/${targetWorkflow}/dispatches`;
  
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
    return { success: true, message: 'Workflow triggered successfully' };
  }
  
  const errorText = await response.text();
  return { 
    success: false, 
    status: response.status,
    error: errorText 
  };
}
