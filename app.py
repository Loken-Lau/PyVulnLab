import os
import sqlite3
import pickle
import base64
import requests
import re
import json
import subprocess
from flask import Flask, request, render_template, render_template_string, send_from_directory, send_file, redirect, url_for
from lxml import etree
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static_files', exist_ok=True) # 用于修复 LFI 的安全目录

# 初始化数据库
def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER, username TEXT, password TEXT)')
    conn.execute("INSERT OR IGNORE INTO users VALUES (1, 'admin', 'password123')")
    conn.execute("INSERT OR IGNORE INTO users VALUES (2, 'guest', 'guestpass')")
    conn.commit()
    conn.close()

# --- 首页路由 ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/repaired')
def repaired_index():
    return render_template('repaired.html')

# ======================================================
# 1. 漏洞版路由 (Vulnerable Routes)
# ======================================================

# 1. SQL 注入
# 修改 app.py 中的 sqli 函数
@app.route('/sqli')
def sqli():
    user_id = request.args.get('id')
    if not user_id:
        return "<h3>请在 URL 后添加 ?id=1 测试</h3>"
    
    conn = sqlite3.connect('database.db')
    try:
        # 【修改点在此】：给 {user_id} 外面加上了单引号 ''
        # 这样你的 payload: 1' OR '1'='1 就会变成：
        # SELECT ... WHERE id = '1' OR '1'='1'  <-- 这是一个合法的 SQL 语句
        query = f"SELECT username FROM users WHERE id = '{user_id}'"
        
        cur = conn.execute(query)
        result = cur.fetchall() # 使用 fetchall 可以看到注入出的所有数据
        
        if result:
            return f"<h3>漏洞版 SQLi 结果:</h3> {result}"
        else:
            return "<h3>未查询到结果</h3>"
            
    except Exception as e:
        # 打印具体报错，方便调试，而不是直接显示 500
        return f"<h3>数据库报错 (这是注入失败导致的):</h3> {e}"

# 2. XSS (反射型)
@app.route('/xss')
def xss():
    name = request.args.get('name', 'Guest')
    # 漏洞：无过滤直接渲染
    return render_template_string(f"<h1>Hello, {name}</h1>")

# 3. 命令执行 (RCE)
@app.route('/ping')
def ping():
    ip = request.args.get('ip')
    if not ip: return "请输入 ?ip=127.0.0.1"
    # 漏洞：拼接系统命令
    cmd = f"ping -c 1 {ip}"
    try:
        result = os.popen(cmd).read()
        return f"<pre>{result}</pre>"
    except: return "执行出错"

# 4. 文件包含 (LFI)
@app.route('/read')
def read_file():
    filename = request.args.get('file')
    if not filename: return "请输入 ?file=/etc/passwd"
    try:
        with open(filename, 'r') as f:
            return f"<pre>{f.read()}</pre>"
    except: return "文件未找到"

# 5. 文件上传
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        # 漏洞：无任何检查
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))
        return f"文件 {file.filename} 上传成功! 路径: /uploads/{file.filename}"
    return '<form method=post enctype=multipart/form-data><p>漏洞版上传:</p><input type=file name=file><input type=submit></form>'

# 6. XXE
@app.route('/xxe', methods=['POST'])
def xxe():
    try:
        # 漏洞：允许外部实体
        parser = etree.XMLParser(resolve_entities=True)
        root = etree.fromstring(request.data, parser=parser)
        return f"XXE 解析结果: {etree.tostring(root).decode()}"
    except Exception as e: return f"Error: {e}"

# 7. 反序列化
@app.route('/unserialize')
def unserialize():
    data = request.args.get('data')
    if not data: return "请输入Base64编码的Pickle数据"
    try:
        # 漏洞：pickle.loads
        pickle.loads(base64.b64decode(data))
        return "反序列化执行完毕"
    except: return "反序列化出错"

# 8. SSRF
@app.route('/ssrf')
def ssrf():
    url = request.args.get('url')
    if not url: return "请输入 ?url=http://..."
    try:
        # 漏洞：任意 URL 请求
        resp = requests.get(url, timeout=2)
        return f"<pre>{resp.text[:500]}</pre>"
    except: return "请求失败"

# 9. 目录遍历
@app.route('/download')
def download():
    path = request.args.get('path')
    if not path: return "请输入 ?path=app.py"
    # 漏洞：允许 ../
    return send_file(path, as_attachment=True)

# 10. CSRF
@app.route('/update_pass', methods=['POST'])
def update_pass():
    new_pass = request.form.get('pass')
    # 漏洞：无 Token，无 Referer 检查
    return f"<h3>[漏洞版] 密码已强制修改为: {new_pass}</h3>"


# ======================================================
# 2. 修复版路由 (Repaired Routes)
# ======================================================

# 1. 修复 SQLi
@app.route('/repair/sqli')
def repair_sqli():
    user_id = request.args.get('id')
    if not user_id: return "请输入 ?id=1"
    conn = sqlite3.connect('database.db')
    # 修复：参数化查询
    cur = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    result = cur.fetchone()
    return f"<h3>修复版安全结果:</h3> {result}"

# 2. 修复 XSS
@app.route('/repair/xss')
def repair_xss():
    name = request.args.get('name', 'Guest')
    # 修复：使用模板引擎自动转义
    return render_template('repaired_xss.html', name=name)

# 3. 修复 RCE
@app.route('/repair/ping')
def repair_ping():
    ip = request.args.get('ip')
    if not ip: return "请输入 IP"
    # 修复：正则校验 + 列表传参
    if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
        return "非法 IP 格式"
    try:
        res = subprocess.check_output(["ping", "-c", "1", ip]).decode()
        return f"<pre>{res}</pre>"
    except: return "Ping 失败"

# 4. 修复 LFI
@app.route('/repair/read')
def repair_read():
    filename = request.args.get('file')
    if not filename: return "请输入文件名"
    # 修复：basename 只取文件名，不信任路径
    safe_name = os.path.basename(filename)
    try:
        return send_from_directory('static_files', safe_name)
    except: return "文件不存在或禁止访问"

# 5. 修复 文件上传
@app.route('/repair/upload', methods=['POST'])
def repair_upload():
    file = request.files['file']
    # 修复：secure_filename + 后缀白名单
    filename = secure_filename(file.filename)
    if filename.endswith(('.png', '.jpg', '.txt')):
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return "安全上传成功"
    return "非法文件类型", 403

# 6. 修复 XXE
@app.route('/repair/xxe', methods=['POST'])
def repair_xxe():
    # 修复：禁用实体解析
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    try:
        root = etree.fromstring(request.data, parser=parser)
        return f"安全解析: {etree.tostring(root).decode()}"
    except: return "XML 错误"

# 7. 修复 反序列化
@app.route('/repair/unserialize')
def repair_unserialize():
    data = request.args.get('data')
    if not data: return "请输入 JSON Base64"
    try:
        # 修复：改用 JSON
        obj = json.loads(base64.b64decode(data))
        return f"安全加载 JSON: {obj}"
    except: return "数据格式错误"

# 8. 修复 SSRF
@app.route('/repair/ssrf')
def repair_ssrf():
    url = request.args.get('url')
    # 修复：白名单验证
    if url and (url.startswith('http://www.baidu.com') or url.startswith('http://trusted.com')):
        try:
            return requests.get(url, timeout=1).text[:500]
        except: return "请求超时"
    return "禁止访问该域名"

# 9. 修复 目录遍历
@app.route('/repair/download')
def repair_download():
    path = request.args.get('path')
    # 修复：过滤路径符号
    safe_path = secure_filename(path)
    try:
        return send_from_directory(UPLOAD_FOLDER, safe_path)
    except: return "文件未找到"

# 10. 修复 CSRF
@app.route('/repair/update_pass', methods=['POST'])
def repair_update_pass():
    # 修复：Referer 检查 (简易版)
    referer = request.headers.get('Referer')
    if referer and "127.0.0.1:5000" in referer:
        return "<h3>[修复版] 来源合法，密码修改成功</h3>"
    return "<h3>[拦截] CSRF 攻击检测：来源非法</h3>", 403

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)