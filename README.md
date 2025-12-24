# Web 漏洞攻防演练平台 (Web Vulnerability & Defense Range)

这是一个基于 **Python Flask** 开发的轻量级 Web 安全教学靶场。本项目旨在帮助安全研究人员、开发人员和学生理解常见 Web 漏洞的产生原理，并学习如何编写安全的代码（Secure Coding）。

系统内置了 10 种典型的 Web 高危漏洞，并为每一个漏洞提供了对应的**修复版路由**，实现了“攻击复现”与“防御实战”的闭环演示。

## ⚠️ 严正声明 (Disclaimer)

**请在下载或使用本项目前仔细阅读以下条款：**

1. **仅供教育用途**：本项目仅用于网络安全教学、漏洞原理研究和内部攻防演练。
    
2. **严禁非法使用**：严禁将本项目中的代码或技术用于非法攻击、入侵他人系统或进行任何未经授权的测试。
    
3. **风险自负**：由于本项目包含真实的漏洞逻辑（如 RCE、SQL 注入），**请勿将其部署在公网服务器或生产环境中**。作者不对因使用本项目造成的任何直接或间接损失承担责任。
    
4. **合规性**：使用者需遵守当地法律法规（如《中华人民共和国网络安全法》）。
    

## 🎯 包含的漏洞类型 (Vulnerabilities)

本项目包含以下 10 个模块，每个模块均包含 `Vulnerable`（漏洞版）和 `Repaired`（修复版）两个入口：

|ID|漏洞名称|漏洞原理|修复方案演示|
|---|---|---|---|
|1|**SQL Injection** (SQL 注入)|字符串直接拼接 SQL 语句|参数化查询 (Prepared Statements)|
|2|**Reflected XSS** (反射型 XSS)|未过滤的用户输入直接渲染|模板引擎自动转义 (Auto-escaping)|
|3|**RCE** (远程命令执行)|`os.popen` 拼接 Shell 命令|正则校验 + `subprocess` 列表传参|
|4|**LFI** (本地文件包含)|任意路径读取 (`open()`)|`basename` 过滤 + 目录限定|
|5|**File Upload** (任意文件上传)|未校验后缀名/文件头|白名单校验 + 文件重命名|
|6|**XXE** (XML 外部实体注入)|开启外部实体解析 (`resolve_entities`)|显式禁用 DTD/Entity 解析|
|7|**Insecure Deserialization**|不安全的 `pickle` 反序列化|使用安全的 JSON 格式|
|8|**SSRF** (服务端请求伪造)|任意 URL 请求发起|URL 白名单限制|
|9|**Directory Traversal**|路径穿越 (`../`)|`secure_filename` 过滤|
|10|**CSRF** (跨站请求伪造)|无 Token/Referer 校验|Referer 来源检查演示|

## 🚀 快速开始 (Quick Start)

推荐使用 Docker 进行部署，以确保环境隔离和安全性。

### 方式一：使用 Docker (推荐)

1. **构建镜像**：
    
    ```
    docker build -t vuln-app .
    ```
    
2. **启动容器**：
    
    ```
    docker run -d -p 5000:5000 --name vuln-container vuln-app
    ```
    
3. **访问靶场**： 打开浏览器访问 `http://localhost:5000`
    

### 方式二：本地 Python 运行

确保本地已安装 Python 3.x。

1. **安装依赖**：
    
    ```
    pip install -r requirements.txt
    ```
    
2. **运行应用**：
    
    ```
    python app.py
    ```
    

## 🛡️ 安全性说明 (Security Note)

由于本项目是**故意设计为不安全 (Vulnerable-by-Design)** 的应用，请务必遵守以下安全准则：

- **网络隔离**：建议在虚拟机 (VM) 或受限的 Docker 容器网络中运行。
    
- **不要暴露端口**：切勿将 5000 端口映射到公网 IP，否则极易被黑客利用（特别是 RCE 漏洞）。
    
- **数据清理**：测试结束后，建议通过 `docker rm -f vuln-container` 删除容器，以清除可能产生的恶意文件。
    

## 📂 项目结构

```
.
├── app.py              # 核心源码（包含漏洞与修复逻辑）
├── Dockerfile          # 容器构建文件
├── requirements.txt    # 依赖库
├── uploads/            # 上传文件存储目录
└── templates/          # 前端页面
    ├── index.html      # 漏洞演示主页
    ├── repaired.html   # 修复演示主页
    └── ...
```

## 🤝 贡献

欢迎提交 Issue 或 Pull Request 来改进代码或增加新的漏洞类型。请确保提交的代码符合教育目的。

## 📜 License

MIT License