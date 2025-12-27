import pandas as pd
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
import json
import os
import datetime
import io

app = FastAPI()

from pydantic import BaseModel

class LoginData(BaseModel):
    role: str  # "student" 或 "teacher"
    id_code: str = "" # 学号
    username: str = ""
    password: str = ""

# 修改登录验证接口
@app.post("/login_auth")
async def login_auth(data: LoginData):
    if data.role == "student":
        if len(data.id_code) == 4 and data.id_code.isdigit():
            # 检查是否已提交
            has_submitted = False
            short_id = data.id_code[-2:]
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    submissions = json.load(f)
                    # 如果该学号已提交过任何观点
                    if any(d.get('student_id') == short_id for d in submissions):
                        has_submitted = True
            
            return {"status": "success", "role": "student", "has_submitted": has_submitted}
        return {"status": "fail", "msg": "请输入4位数字学号"}
    
    if data.role == "teacher":
        if data.username == "gxl" and data.password == "gxl135944":
            return {"status": "success", "role": "teacher"}
        return {"status": "fail", "msg": "老师账号或密码错误"}
    return {"status": "fail"}

# ================= 1. 业务逻辑与配置 =================
COLOR_MAP = {
    "1": "#60a5fa", "2": "#34d399", "3": "#f87171", "4": "#fbbf24",
    "5": "#a78bfa", "6": "#f472b6", "7": "#2dd4bf", "8": "#94a3b8"
}

KNOWLEDGE_MAP = {
    "1": {"title": "柴油汽车尾气的成分", "content": "主要由氮氧化物（NOx）、颗粒物（PM）、一氧化碳等组成。"},
    "2": {"title": "柴油汽车尾气的产生机理", "content": "NOx产生于高温富氧环境，颗粒物是燃烧不完全的产物。"},
    "3": {"title": "柴油汽车尾气导致雾霾的原因", "content": "NOx进入大气转化为硝酸盐，是PM2.5的重要来源。"},
    "4": {"title": "雾霾的主要成分", "content": "主要包含硝酸铵、硫酸铵等无机盐颗粒。"},
    "5": {"title": "柴油尾气的治理/处理方法", "content": "包含机内净化和后处理技术（SCR、DPF）。"},
    "6": {"title": "治理尾气的装置与原理", "content": "SCR利用尿素作为还原剂，将NOx还原为N2。"},
    "7": {"title": "治理尾气的成本问题", "content": "涉及催化剂贵金属及尿素液的日常消耗。"},
    "8": {"title": "其他", "content": "其他关于环境与化学的奇思妙想。"}
}

DB_FILE = "submissions.json"
ADMIN_PASSWORD = "gxl135944"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump([], f)

def classify_text(text: str) -> str:
    keywords = {
        "1": ["成分", "物质", "构成"], "2": ["机理", "产生", "形成", "燃烧"],
        "3": ["原因", "雾霾", "导致"], "4": ["硝酸", "硫酸", "铵盐"],
        "5": ["治理", "处理", "净化", "减排"], "6": ["装置", "原理", "SCR", "尿素"],
        "7": ["成本", "价格", "钱", "贵"],
    }
    for cid, kws in keywords.items():
        if any(kw in text for kw in kws): return cid
    return "8"

# ================= 2. 路由接口 =================

@app.get("/", response_class=HTMLResponse)
async def index(): return template_html
# 修改 /submit 接口，增加对学号的记录
@app.post("/submit")
async def submit(request: Request, q1: str = Form(""), q2: str = Form(""), q3: str = Form(""), q4: str = Form(""), id_code: str = Form("")):
    client_ip = request.client.host
    with open(DB_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if any(d['ip'] == client_ip for d in data): 
            return {"status": "already_submitted"}
        
        added = False
        # 获取学号后两位
        short_id = id_code[-2:] if len(id_code) >= 2 else "00"
        
        for ans in [q1, q2, q3, q4]:
            if ans.strip():
                data.append({
                    "ip": client_ip, 
                    "text": ans, 
                    "student_id": short_id, # 记录学号
                    "time": datetime.datetime.now().strftime("%H:%M:%S")
                })
                added = True
        if not added: return {"status": "empty"}
        f.seek(0); json.dump(data, f, ensure_ascii=False, indent=2); f.truncate()
    return {"status": "success"}

# 修改 /stats 接口，返回所有独立的小球数据
@app.get("/stats")
async def get_stats():
    with open(DB_FILE, "r", encoding="utf-8") as f: 
        data = json.load(f)
    
    bubbles = []
    for i, d in enumerate(data):
        # 根据学号生成固定但唯一的颜色
        seed = int(d['student_id']) if d['student_id'].isdigit() else i
        color = f"hsl({(seed * 137) % 360}, 70%, 60%)"
        
        bubbles.append({
            "id": i,
            "text": d['text'],
            "label": d['student_id'],
            "color": color
        })
    
    unique_ips = len(set(d['ip'] for d in data))
    return {"bubbles": bubbles, "submitted_count": unique_ips}

@app.get("/admin/reset")
async def reset_data(pwd: str = ""):
    if pwd != ADMIN_PASSWORD: return {"status": "denied"}
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump([], f)
    return {"status": "success"}

@app.get("/admin/export")
async def export_csv(pwd: str = ""):
    if pwd != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Forbidden")
    with open(DB_FILE, "r", encoding="utf-8") as f: data = json.load(f)
    if not data: return HTMLResponse("<html><script>alert('当前没有数据可供下载');window.history.back();</script></html>")
    df = pd.DataFrame(data)
    df['类别'] = df['cid'].apply(lambda x: KNOWLEDGE_MAP.get(x, {}).get('title', '其他'))
    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    return StreamingResponse(io.BytesIO(output.getvalue().encode('utf-8-sig')), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=results.csv"})

# ================= 3. 前端模板 =================
template_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI赋能化学课堂</title>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        :root { --grad: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #d946ef 100%); }
        body { font-family: 'PingFang SC', sans-serif; background: #f8fafc; margin: 0; display: flex; flex-direction: column; align-items: center; overflow-x: hidden; min-height: 100vh; }
        
        .header { 
            width: 90%; max-width: 1000px; background: var(--grad); padding: 30px; 
            margin-top: 30px; border-radius: 24px; color: white; text-align: center; 
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); box-sizing: border-box; 
        }
        .header h1 { margin: 0; font-size: 24px; }
        .header p { margin: 10px 0 0; opacity: 0.8; font-size: 14px; }

        .main-content { width: 90%; max-width: 1000px; margin-top: 20px; flex: 1; }
        .progress-box { background: white; padding: 20px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .bar-bg { background: #e2e8f0; height: 12px; border-radius: 6px; margin-top: 10px; overflow: hidden; }
        .bar-fill { background: var(--grad); height: 100%; width: 0%; transition: width 0.6s ease; }

        .card { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); }
        .input-group input { width: 100%; padding: 15px; margin-bottom: 15px; border: 1px solid #e2e8f0; border-radius: 12px; font-size: 16px; box-sizing: border-box; }
        .btn { width: 100%; padding: 16px; background: #3b82f6; color: white; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 16px; }

        #bubble-view { 
            display: none; 
            width: 100%; 
            height: 600px; 
            background: white; 
            border-radius: 20px; 
            position: relative; 
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); 
            overflow: hidden; 
            border: 1px solid #e2e8f0;
        }
        canvas { width: 100%; height: 100%; }

        .admin-bar { margin: 40px 0 20px; display: flex; gap: 20px; justify-content: center; width: 100%; }
        .admin-bar a { font-size: 12px; color: #94a3b8; text-decoration: none; cursor: pointer; }
        .admin-bar a:hover { color: #3b82f6; }

        #modal { display:none; position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); width:350px; background:white; padding:30px; border-radius:24px; box-shadow:0 25px 50px -12px rgba(0,0,0,0.25); z-index:100; }
        #overlay { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.5); backdrop-filter: blur(4px); z-index:99; }
    </style>
</head>
<body>
    <div id="login-view" style="position:fixed; top:0; left:0; width:100%; height:100%; background:#f1f5f9; z-index:1000; display:flex; align-items:center; justify-content:center;">
        <div class="card" style="width:350px; text-align:center;">
            <h2 style="color:#3b82f6;">课堂互动系统登录</h2>
            
            <div style="margin-bottom:20px; display:flex; gap:10px;">
                <button id="tab-std" class="btn" style="background:#3b82f6;" onclick="switchTab('student')">学生入口</button>
                <button id="tab-tch" class="btn" style="background:#94a3b8;" onclick="switchTab('teacher')">老师入口</button>
            </div>

            <div id="form-student">
                <input id="std_id" type="text" placeholder="请输入4位学号 (如: 0101)" maxlength="4" style="width:100%; padding:12px; margin-bottom:15px; border-radius:8px; border:1px solid #ddd;">
                <button class="btn" onclick="doLogin('student')">进入提问</button>
            </div>

            <div id="form-teacher" style="display:none;">
                <input id="tch_user" type="text" placeholder="账号" style="width:100%; padding:12px; margin-bottom:10px; border-radius:8px; border:1px solid #ddd;">
                <input id="tch_pwd" type="password" placeholder="密码" style="width:100%; padding:12px; margin-bottom:15px; border-radius:8px; border:1px solid #ddd;">
                <button class="btn" style="background:#8b5cf6;" onclick="doLogin('teacher')">进入管理后台</button>
            </div>
        </div>
    </div>
    <div class="header">
        <h1>AI赋能化学课堂：柴油汽车尾气导致雾霾的原因及解决</h1>
        <p>高一化学第三章 硫循环 氮循环 —— 复习课</p>
    </div>

    <div class="main-content">
        <div class="progress-box">
            <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:14px;">
                <span>班级提交进度</span>
                <span id="prog-val">正在加载...</span>
            </div>
            <div class="bar-bg"><div id="bar-fill" class="bar-fill"></div></div>
        </div>

        <div id="form-view" class="card">
            <h3 style="margin-top:0; text-align:center;">关于柴油尾气与环境问题，你最想获取哪些信息？</h3>
            <div class="input-group">
                <input id="q1" placeholder="信息需求点 1..."><input id="q2" placeholder="信息需求点 2...">
                <input id="q3" placeholder="信息需求点 3..."><input id="q4" placeholder="信息需求点 4...">
            </div>
            <button class="btn" onclick="doSubmit()">提交并查看课堂气泡图</button>
        </div>

        <div id="bubble-view">
            <canvas id="canvas"></canvas>
            <button onclick="location.reload()" style="position:absolute; bottom:20px; left:20px; padding:8px 15px; border-radius:8px; border:none; background:#f1f5f9; cursor:pointer; font-size:12px; z-index:10;">← 返回答题</button>
        </div>

        <a onclick="location.reload()" style="font-size:12px; color:#94a3b8; cursor:pointer;">[退出登录]</a>

        <div class="admin-bar">
            <a onclick="adminResetFlow()">[重置系统]</a>
            <a onclick="adminExport()">[导出CSV数据]</a>
        </div>
    </div>

    <div id="overlay" onclick="closeModal()"></div>
    <div id="modal">
        <h3 id="mt" style="color:#3b82f6; margin-top:0;"></h3>
        <p id="mc" style="line-height:1.6; color:#475569; font-size:14px;"></p>
        <button class="btn" style="padding:10px;" onclick="closeModal()">确定</button>
    </div>
<script>
    let currentUserRole = "";
    let studentIdForSubmit = ""; 
    let bubbles = [];
    let w, h, dpr;
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const gravity = 0.25;      
    const friction = 0.98;     
    const bounce = 0.7;       

    function switchTab(role) {
        const isStd = role === 'student';
        document.getElementById('form-student').style.display = isStd ? 'block' : 'none';
        document.getElementById('form-teacher').style.display = isStd ? 'none' : 'block';
        document.getElementById('tab-std').style.background = isStd ? '#3b82f6' : '#94a3b8';
        document.getElementById('tab-tch').style.background = isStd ? '#94a3b8' : '#8b5cf6';
    }

    // 封装一个显示气泡视图的函数，增加延迟确保布局完成
    function showBubbleView() {
        document.getElementById('login-view').style.display = 'none';
        document.getElementById('form-view').style.display = 'none';
        document.getElementById('bubble-view').style.display = 'block';
        
        // 关键：延迟 2000ms 确保 cpolar 加载的布局已渲染，否则 w/h 为 0
        setTimeout(() => {
            initCanvas();
            sync(); 
            console.log("Canvas 渲染启动，当前气泡数:", bubbles.length);
        }, 2000);
    }
function doLogin(role) {
    const data = { role: role };
    if (role === 'student') {
        studentIdForSubmit = document.getElementById('std_id').value;
        data.id_code = studentIdForSubmit;
    } else {
        data.username = document.getElementById('tch_user').value;
        data.password = document.getElementById('tch_pwd').value;
    }

    axios.post('/login_auth', data).then(res => {
        if (res.data.status === 'success') {
            currentUserRole = res.data.role;
            // 先隐藏登录框
            document.getElementById('login-view').style.display = 'none';

            // 修改 doLogin 函数中的教师端部分
                if (currentUserRole === 'teacher') {
                    showBubbleView();
                } else {
                // 学生端逻辑
                if (res.data.has_submitted) {
                    showBubbleView();
                } else {
                    document.getElementById('form-view').style.display = 'block';
                }
            }
        } else {
            alert(res.data.msg);
        }
    }).catch(err => alert("网络连接失败，请检查cpolar状态"));
}

    function initCanvas() {
    dpr = window.devicePixelRatio || 1;
    // 尝试从容器获取宽度
    const container = document.getElementById('bubble-view');
    const rect = container.getBoundingClientRect();
    
    // 逻辑容错：如果 rect 宽高为 0，说明 CSS 尚未渲染完成
    w = rect.width || 800; 
    h = rect.height || 600;

    canvas.width = w * dpr; 
    canvas.height = h * dpr;
    // 显式设置 canvas 的 CSS 宽高，防止拉伸
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

    class Bubble {
        constructor(obj) {
            this.id = obj.id;
            this.text = obj.text;
            this.label = obj.label;
            this.color = obj.color;
            this.r = 35; 
            this.x = Math.random() * (w - 70) + 35;
            this.y = -50; 
            this.vx = (Math.random() - 0.5) * 8;
            this.vy = Math.random() * 5;
        }
        update() {
            this.vy += gravity;
            this.vx *= friction;
            this.vy *= friction;
            this.x += this.vx;
            this.y += this.vy;

            if (this.x + this.r > w) { this.x = w - this.r; this.vx *= -bounce; }
            if (this.x - this.r < 0) { this.x = this.r; this.vx *= -bounce; }
            if (this.y + this.r > h) { this.y = h - this.r; this.vy *= -bounce; }
            if (this.y - this.r < 0) { this.y = this.r; this.vy *= -bounce; }

            bubbles.forEach(other => {
                if (other === this) return;
                let dx = other.x - this.x;
                let dy = other.y - this.y;
                let dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < this.r + other.r) {
                    let angle = Math.atan2(dy, dx);
                    let tx = this.x + Math.cos(angle) * (this.r + other.r);
                    let ty = this.y + Math.sin(angle) * (this.r + other.r);
                    let ax = (tx - other.x) * 0.3;
                    let ay = (ty - other.y) * 0.3;
                    this.vx -= ax; this.vy -= ay;
                    other.vx += ax; other.vy += ay;
                }
            });
        }
        draw() {
            ctx.save();
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.shadowBlur = 10 * dpr;
            ctx.shadowColor = 'rgba(0,0,0,0.15)';
            ctx.fill();
            ctx.fillStyle = "white";
            ctx.font = `bold ${14}px Arial`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(this.label, this.x, this.y);
            ctx.restore();
        }
    }

function sync() {
    axios.get('/stats').then(res => {
        const progVal = document.getElementById('prog-val');
        const barFill = document.getElementById('bar-fill');
        
        // 更新进度条
        if(progVal) progVal.innerText = `${res.data.submitted_count} / 39`;
        if(barFill) barFill.style.width = (res.data.submitted_count / 39 * 100) + '%';
        
        // 增量添加气泡
        res.data.bubbles.forEach(d => {
            // 只有当 ID 不存在时才添加新球，避免教师端重复创建
            if (!bubbles.find(b => b.id === d.id)) {
                let newB = new Bubble(d);
                // 教师端看到的球可以给一个随机的初始垂直速度，让它们“掉下来”
                newB.vy = Math.random() * 5 + 2;
                bubbles.push(newB);
            }
        });
    });
}

    function render() {
        ctx.clearRect(0, 0, w, h);
        bubbles.forEach(b => { b.update(); b.draw(); });
        requestAnimationFrame(render);
    }

    function doSubmit() {
        const p = new URLSearchParams();
        ['q1','q2','q3','q4'].forEach(id => p.append(id, document.getElementById(id).value));
        p.append('id_code', studentIdForSubmit);
        axios.post('/submit', p).then(res => {
            if(res.data.status==='success' || res.data.status==='already_submitted'){
                showBubbleView();
            } else alert("请输入内容");
        });
    }

    canvas.onclick = (e) => {
        const r = canvas.getBoundingClientRect();
        const mx = e.clientX - r.left;
        const my = e.clientY - r.top;
        bubbles.forEach(b => {
            if(Math.sqrt((mx-b.x)**2 + (my-b.y)**2) < b.r) {
                document.getElementById('mt').innerText = `学生 ${b.label} 的观点`;
                document.getElementById('mc').innerText = b.text;
                document.getElementById('modal').style.display='block';
                document.getElementById('overlay').style.display='block';
            }
        });
    };
    
    function closeModal() {
        document.getElementById('modal').style.display='none';
        document.getElementById('overlay').style.display='none';
    }

    // 启动渲染循环
    render();
    // 缩放自适应
    window.onresize = initCanvas;
    // 持续同步
    setInterval(sync, 5000);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)