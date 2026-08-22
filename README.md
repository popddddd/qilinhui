# 麒麟汇（qilinhui）· 量化交易工具 Demo

一个用于演示的量化交易工具 Web 前端：包含 **用户注册、登录、退出** 和 **占位仪表盘**，为后续接入同事开源的量化交易引擎预留位置。

- 后端：Python 3.10 + FastAPI
- 前端：Jinja2 模板 + Bootstrap 5（CDN）
- 数据库：SQLite（本地与线上都用它，零配置）
- 会话：itsdangerous 签名 Cookie + 内存 Session
- 密码：passlib + bcrypt 加密存储

> ⚠️ **Demo 说明**：Render 免费套餐没有持久化磁盘，SQLite 数据保存在服务实例的内存文件系统里，**服务重启后注册数据会被清空**。这是刻意接受的 Demo 行为，不影响功能演示。

---

## 功能清单

| 功能 | 说明 |
| --- | --- |
| 注册 | 校验用户名唯一、邮箱格式、密码 ≥ 6 位；注册成功跳转登录页并提示 |
| 登录 | 支持“记住我”（Session 有效期 7 天）；未勾选则 1 天 |
| 防枚举 | 登录失败一律提示“用户名或密码错误”；同一用户名 10 分钟内失败 3 次后不再校验，直接返回同一通用错误 |
| 登录保护 | 未登录访问 `/dashboard` 自动跳回 `/login` |
| 退出 | 清除 Session 并删除 Cookie |
| Cookie 安全 | `HttpOnly=True` + `SameSite=Lax`，值经 itsdangerous 签名防伪造 |

## 项目结构

```text
quant_trading_demo/
├── app/
│   ├── __init__.py      # 创建 FastAPI app、读取 SESSION_SECRET、挂载静态目录
│   ├── database.py      # SQLite 初始化与 users 表读写
│   ├── models.py        # Pydantic 请求体模型
│   ├── auth.py          # 全部路由与依赖项
│   ├── utils.py         # 密码哈希 / 会话管理工具函数
│   └── static/          # 预留静态资源目录
├── templates/
│   ├── base.html        # 基础模板（Bootstrap 5 CDN）
│   ├── login.html       # 登录表单（含“记住我”）
│   ├── register.html    # 注册表单（JS 校验密码一致性）
│   └── dashboard.html   # 仪表盘占位页
├── main.py              # 本地启动入口
├── requirements.txt     # 依赖清单
├── .python-version      # 指定 Python 3.10
└── README.md            # 本手册
```

---

## 一、本地运行（建议先跑通再部署）

1. **安装 Python 3.10**（或更高版本）：https://www.python.org/downloads/ 安装时勾选 “Add Python to PATH”。
2. 打开终端，进入项目目录：

   ```bash
   cd quant_trading_demo
   ```

3. 创建虚拟环境并安装依赖：

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. 启动服务：

   ```bash
   python main.py
   ```

5. 浏览器打开 http://127.0.0.1:8000 ，注册 → 登录 → 进入仪表盘。

---

## 二、部署到 Render.com（免费套餐，手把手教程）

### 第 1 步：注册 Render 账号

1. 浏览器打开 https://render.com 。
2. 点击右上角 **Sign Up**。
3. 选择 **Continue with GitHub**，用你的 GitHub 账号授权登录（没有 GitHub 账号就先注册一个：https://github.com/signup ）。

### 第 2 步：把项目推送到 GitHub

1. 打开 GitHub 网站，点击右上角 **+ → New repository**。
2. Repository name 填 `qilinhui`，选 **Private**（私有）或 **Public**（公开）都可以，**不要勾选** “Add a README file”（避免产生冲突），然后点 **Create repository**。
3. 在你电脑的项目文件夹打开终端（Windows 可在文件夹地址栏输入 `cmd` 回车），依次执行：

   ```bash
   cd quant_trading_demo

   git init
   git add .
   git commit -m "first commit"
   git branch -M main
   git remote add origin https://github.com/你的GitHub用户名/qilinhui.git
   git push -u origin main
   ```

   > 把命令里的 `你的GitHub用户名` 换成你自己的。首次推送如果提示登录，按提示用 GitHub 账号授权即可。

### 第 3 步：在 Render 上创建 Web Service

1. 登录 Render 后进入 **Dashboard**。
2. 点击右上角 **New +**，选择 **Web Service**。
3. 选择 **Connect a repository**，找到并连接你的 `qilinhui` 仓库（若没有出现，先点击 “Configure account” 授权 GitHub，再刷新）。
4. 在配置页面按下面填写：

   | 配置项 | 填写内容 |
   | --- | --- |
   | Name | `qilinhui`（这决定访问前缀，即最终网址是 `qilinhui.onrender.com`） |
   | Region | 选 Singapore 或 Ohio 均可（离国内近可选 Singapore） |
   | Branch | `main` |
   | Runtime | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
   | Instance Type | 保持 **Free** 即可（每月 750 小时免费额度） |

5. 点击页面底部 **Create Web Service**。

> 仓库里的 `.python-version` 文件（内容 `3.10.12`）会让 Render 自动使用 Python 3.10；如果构建时报版本不支持，把它改成 `3.12` 或 `3.13` 再推送即可（本项目兼容更高版本）。

### 第 4 步：等待部署并访问

1. 部署过程需要 1~5 分钟，可在服务页面的 **Events** 标签页看实时进度。
2. 看到 “Your service is live 🎉” 后，打开 **https://qilinhui.onrender.com** 即可访问。
3. 点击注册 → 登录 → 进入仪表盘。

> 🌙 **免费实例会休眠**：免费套餐的实例约 15 分钟无人访问会自动休眠，下次访问时需要等待 30~60 秒“唤醒”，这是正常现象，无需处理。

### 第 5 步：常见问题排错

| 现象 | 解决办法 |
| --- | --- |
| 页面打不开 / 一直转圈 | 打开该服务，点击顶部 **Logs** 标签页查看日志，能看到具体报错 |
| `ModuleNotFoundError: No module named 'xxx'` | 说明 `requirements.txt` 缺少该依赖：在本地 `pip install xxx` 后把包名和版本追加进 `requirements.txt`，然后 `git add . && git commit -m "add dep" && git push`，Render 检测到新提交会自动重新部署 |
| 改完代码想立即重新部署 | 打开服务 → 右上角 **Manual Deploy → Deploy latest commit** |
| 注册后重启数据没了 | 正常现象，免费版无持久化磁盘（见开头 Demo 说明） |
| 端口相关报错 `address already in use` | 确认 Start Command 用的是 `--port $PORT`（Render 会把端口注入环境变量），不要写死 8000 |
| 构建失败提示 Python 版本不支持 | 修改 `.python-version` 中的版本号（如 `3.12`），再重新推送触发部署 |

---

## 三、进阶设置（可选但推荐）

### 1. 设置 SESSION_SECRET 环境变量

默认使用固定密钥签名 Cookie（仅适合 Demo）。上线前建议改成随机值：

1. 在 Render 服务页面进入 **Environment** 标签。
2. 点击 **Add Environment Variable**。
3. Key 填 `SESSION_SECRET`，Value 填一串随机字符串（可用 https://randomkeygen.com 生成，选 32 位以上）。
4. 保存后点击 **Manual Deploy → Deploy latest commit** 生效。

### 2. 以后更新代码

```bash
cd quant_trading_demo
# ...修改代码...
git add .
git commit -m "update"
git push
```

Render 会自动拉取新代码并重新部署，无需手动操作。

### 3. 后续接入量化交易引擎

把同事的工具逻辑放进 `app/`（或新目录），在 `app/auth.py` 中新增路由，并更新 `templates/dashboard.html` 的占位卡片即可；登录保护逻辑可以直接复用 `get_current_user`。

---

## 四、安全说明

- 密码使用 bcrypt 加盐哈希存储，数据库里不保存明文。
- 登录失败不区分“用户不存在”和“密码错误”，统一提示“用户名或密码错误”，防止枚举有效账号。
- Session Cookie 设置了 `HttpOnly` 与 `SameSite=Lax`，值经过签名，用户无法伪造。
- 本项目的目标是公网可访问的 Demo，请勿存放真实交易密钥、真实密码或敏感数据。