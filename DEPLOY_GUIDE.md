# GitHub → Render auto-deployment (beginner steps)

Your repository: https://github.com/harshithareddy0008/mcp-customer-support-agent

Your existing Render app: https://mcp-customer-support-agent.onrender.com

## Upload without terminal — GitHub Desktop

1. Install GitHub Desktop from https://desktop.github.com and sign in to GitHub.
2. **File → Clone repository →** select `harshithareddy0008/mcp-customer-support-agent`.
3. Unzip `supportdesk-ai-mcp-mvp-github-ready.zip` somewhere else.
4. Copy **everything inside the extracted ZIP**, including `.github` and `support-mcp-agent`, into the cloned repository folder. Choose **Replace files** when prompted. Make sure it contains **one** `support-mcp-agent` folder, not a nested duplicate.
5. GitHub Desktop will show changes. Summary: `feat: launch SupportDesk AI MCP MVP`. Click **Commit to main**, then **Push origin**.
6. Open GitHub → **Actions**. The workflow should run unit tests and the real MCP smoke test. A green check confirms the four protocol tools passed on GitHub's runner.

## Enable automatic deployment in the EXISTING Render service

1. Render Dashboard → `mcp-customer-support-agent` → **Settings**.
2. Confirm **Connected Repository** is `harshithareddy0008/mcp-customer-support-agent` and **Branch** is `main`.
3. Confirm **Root Directory** is `support-mcp-agent` (without leading `/`).
4. Build Command: `pip install -r requirements.txt`.
5. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
6. Under **Auto-Deploy**, choose **After CI Checks Pass** (best) or **On Commit** (immediately after each push). Save settings.
7. Commits/pushes to `main` now trigger Render deployments automatically. If you set *After CI Checks Pass*, Render waits for GitHub Actions to pass before deploying.
8. Open your Render URL and check `/health` and all four demo prompts.

A `render.yaml` file in GitHub does **not** reconfigure an already-existing manually created Render service by itself. The YAML at the repository root is for a new Render Blueprint. Don't create a second service just to update this one.

## If Render shows 503

- Check Render → Logs for `MCP handshake or tool execution failed` and copy the full Python traceback.
- Verify **Root Directory** and **PORT** configurations.
- On a fresh deployment, see the `/health` route and startup logs first.
- Visit GitHub → Actions and review the **real MCP smoke test** step. If it failed, don't claim tool calls work yet.

Render free instances may spin down and SQLite `/tmp` demo data can reset. No production user data or private emails should be entered.

## Set Gemini secret (do not push your .env)

1. Get free-tier API key from https://aistudio.google.com/apikey.
2. For local development: copy `support-mcp-agent/.env.example` to `support-mcp-agent/.env`, then set `GEMINI_API_KEY=<your actual key>`.
3. Render → existing `mcp-customer-support-agent` service → **Environment** → Add Environment Variable. Key: `GEMINI_API_KEY`, Value: your secret key. Optionally `GEMINI_MODEL` = `gemini-2.5-flash-lite`.
4. Save (and redeploy if needed). Use the app; a response marked `Gemini planner` confirms model routing. If you see `Rules planner`, check Render logs for a generic Gemini planning error and verify your key/quota.
5. Keep `.env` out of GitHub and never share keys in chat/screenshots. The Gemini model is proprietary; the app's own code and MCP integration are open-source.
