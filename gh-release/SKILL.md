---
name: gh-release
made_by: "Freya"
version: "1.0"
last_updated: "2026-10-28"
description: Publish a local project to GitHub — init git, configure SSH keys, set up proxy for China users, push to remote. Use when the user says "publish to GitHub", "upload to GitHub", "push to GitHub", "create a GitHub repo for this", or "release this project". Not for cloning (use git clone directly) and not for GitHub Actions or CI/CD.
metadata:
  hermes:
    category: dev-tools
    tags: [github, git, ssh, proxy, release, publish, devops]
    related_skills: []
---

# gh-release — 将本地项目发布到 GitHub

全流程自动化的 GitHub 发布助手。覆盖 git 初始化 → SSH 配置 → 代理网络（中国大陆）→ 推送上线。

## 触发条件

- "发布到 GitHub" / "上传到 GitHub" / "push 到 GitHub"
- "把这个项目推到 GitHub" / "创建一个 GitHub 仓库"
- "release this project" / "publish to GitHub"

## 先决检查

开始前先确认三件事：

```bash
# 1. 是否已经是 git 仓库？
git status 2>&1 | head -1
# 如果显示 "fatal: not a git repository" → 需要 init

# 2. 用户有 GitHub 账号吗？
# 问用户：GitHub 用户名？仓库名想叫什么？Public 还是 Private？

# 3. 网络通吗？
curl -sI --connect-timeout 5 https://github.com 2>&1 | head -1
# 超时 → 需要配代理
```

## 流程

```
检查状态 → 初始化 git → 创建 .gitignore → 提交
    → 探测网络/代理 → 选认证方式（SSH 优先，PAT 备用）
        → 加远端 → 推送
```

---

## 第 1 步：初始化 Git

```bash
git init -b main

# 检查是否有 user.name / user.email
git config user.name   # 若为空 →
git config user.email  # 若为空 →
git config --global user.name "用户名"
git config --global user.email "邮箱"
```

### .gitignore（按项目类型选模板）

**通用（Python + macOS + 编辑器）：**
```gitignore
# macOS
.DS_Store

# 备份
*.backup
*.bak

# Python
__pycache__/
*.pyc
*.pyo
.venv/
venv/

# 编辑器
.idea/
.vscode/
*.swp

# 环境变量
.env
.env.local
```

**通用（Node.js / 前端）：**
```gitignore
# macOS
.DS_Store

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build
dist/
build/
.next/

# 编辑器
.idea/
.vscode/
*.swp

# 环境变量
.env
.env.local
```

创建 `.gitignore` 后：

```bash
git add -A
git status --short | wc -l        # 确认文件数
git commit -m "初始提交: <项目描述>"
```

---

## 第 2 步：探测网络代理（中国大陆用户必做）

```bash
# 探测常见代理端口
for port in 7897 7890 1080 10809 6152 1087 8118; do
  if nc -z -w1 127.0.0.1 $port 2>/dev/null; then
    echo "✓ 端口 $port 开放"
    code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 \
      -x http://127.0.0.1:$port https://github.com 2>/dev/null)
    [ "$code" = "200" ] || [ "$code" = "301" ] && \
      echo "  → GitHub 可达 (HTTP $code)"
  fi
done
```

找到可用端口后：

```bash
PROXY_PORT=<探测到的端口>

# git HTTPS 代理
git config --global http.proxy http://127.0.0.1:$PROXY_PORT
git config --global https.proxy http://127.0.0.1:$PROXY_PORT

# SSH over HTTPS 代理
mkdir -p ~/.ssh
cat > ~/.ssh/config << EOF
Host github.com
  HostName github.com
  User git
  ProxyCommand nc -X connect -x 127.0.0.1:$PROXY_PORT %h %p
EOF
chmod 600 ~/.ssh/config
```

---

## 第 3 步：认证（三选一，按优先级）

### 方案 A：SSH Key（推荐 — 一次配置永久有效）

**生成密钥：**
```bash
# 如果已有 key 则跳过
ssh-keygen -t ed25519 -C "你的邮箱" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```

**用户操作**：将公钥粘贴到 GitHub → Settings → SSH and GPG keys → New SSH key

**验证：**
```bash
ssh -T git@github.com 2>&1
# 期望: "Hi <用户名>! You've successfully authenticated..."
```

### 方案 B：Personal Access Token（一次性，适合临时使用）

**用户操作**：GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)
- ✅ 勾选 `repo` 权限
- 生成后复制 `ghp_` 开头的 token

**推送：**
```bash
git remote add origin https://<用户名>@github.com/<用户名>/<仓库名>.git
git push -u origin main
# 密码提示处粘贴 token
```

### 方案 C：gh CLI（需要 OAuth 浏览器授权）

```bash
echo "Y" | gh auth login --web --git-protocol https --hostname github.com
# 会打开浏览器 → 输入一次性验证码 → Authorize
# 然后:
gh repo create <仓库名> --public --source=. --remote=origin --push
```

> ⚠️ 方案 C 在终端未配代理时可能超时。如果代理已配好，这是最便捷的方案。

---

## 第 4 步：推送

```bash
# SSH 方式
git remote add origin git@github.com:<用户名>/<仓库名>.git

# HTTPS + Token 方式
git remote add origin https://<用户名>@github.com/<用户名>/<仓库名>.git

# 推送
git branch -M main
git push -u origin main
```

---

## 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `fatal: not a git repository` | 未 init | 跑第 1 步 |
| `Connection timed out` / `i/o timeout` | 终端未走代理 | 跑第 2 步探测并配代理 |
| `Permission denied (publickey)` | SSH key 未添加或代理未配 | 公钥添加到 GitHub，或确认 `~/.ssh/config` 代理端口正确 |
| `remote origin already exists` | 已有关联远端 | `git remote set-url origin git@github.com:...` 覆盖 |
| `failed to push some refs` | 远端有冲突文件 | `git pull --rebase origin main` 后重新推送 |
| `The requested URL returned error: 403` | Token 权限不够 | 确认 PAT 勾选了 `repo` 权限 |
| `support for password authentication was removed` | 尝试用密码登录 | 改用 SSH key 或 PAT |

---

## 推送后检查

```bash
# 确认远端已同步
git remote -v
git log --oneline -3

# 确认 GitHub API 可见（需要 token 或已认证 gh）
curl -sI "https://api.github.com/repos/<用户名>/<仓库名>" | head -3
# 期望: HTTP/2 200
```

## 维护

此 skill 独立于项目，可单独安装到 Hermes 或任意 AI 运行时：

```bash
# 安装到 Codex
cp -r gh-release ~/.codex/skills/gh-release/

# 安装到其他 AI 产品（按产品文档指定路径）
cp -r gh-release <目标 skills 目录>/gh-release/
```