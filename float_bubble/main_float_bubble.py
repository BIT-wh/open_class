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

@app.post("/login_auth")
async def login_auth(data: LoginData):
    if data.role == "student":
        if len(data.id_code) == 4 and data.id_code.isdigit():
            return {"status": "success", "role": "student"}
        return {"status": "fail", "msg": "请输入4位数字学号"}
    
    if data.role == "teacher":
        if data.username == "gxl" and data.password == "gxl135944":
            return {"status": "success", "role": "teacher"}
        return {"status": "fail", "msg": "老师账号或密码错误"}
    return {"status": "fail"}

# ================= 1. 业务逻辑与配置 =================
COLOR_MAP = {
    "1": "#60a5fa", "2": "#34d399", "3": "#f87171", "4": "#fbbf24",
    "5": "#a78bfa", "6": "#f472b6", "7": "#94a3b8"
}
KNOWLEDGE_MAP = {
    "1": {
        "title": "🌫️ 雾霾的主要成分 (PM2.5)", 
        "content": (
            "【基本概念】\n"
            "雾霾是雾(Fog)和霾(Haze)的合称，现代城市雾霾核心是人为排放物在大气中发生复杂化学反应生成的复合污染体系。\n\n"
            "【核心构成 · 占比分析】\n\n"
            "📊 二次无机气溶胶 (40%—60%)\n"
            "   这是造成能见度下降和健康危害的关键成分：\n"
            "   ▹ 硝酸盐：10%—30% (主要来自机动车/工业)\n"
            "   ▹ 硫酸盐：10%—25% (主要来自燃煤/重油)\n"
            "   ▹ 铵  盐：5%—15% (主要来自农业氨气)\n\n"
            "🧪 其他主要物质：\n"
            "   ▹ 有机物 (20%—40%)：尾气、燃煤及生物质燃烧\n"
            "   ▹ 元素碳 (5%—15%)：不完全燃烧产物，吸光性强\n"
            "   ▹ 地壳物质 (5%—15%)：建筑及道路扬尘\n"
            "   ▹ 重金属 (<5%)：铅、砷等有毒微粒\n"
            "------------------------------------------\n\n"
            "💡 专家解读：雾霾并非单纯的“灰尘”，其关键在于人为排放的前体物在大气中发生的二次转化。"
        )
    },
    "2": {
        "title": "⚙️ 雾霾产生的机理", 
        "content": (
            "【核心来源：五大污染源解析】\n"
            "----------------------------\n"
            "■ 工业源 (30%—50%) 🏭\n"
            "   [主要排放：SO₂、NOₓ、粉尘]\n"
            "   重点关注燃煤电厂、钢铁及化工厂。\n\n"
            "■ 移动源 (20%—45%) 🚗\n"
            "   [主要排放：NOₓ、VOCs]\n"
            "   大城市首要来源，尤其是柴油车尾气。\n\n"
            "■ 农业源 (15%—30%) 🌾\n"
            "   [主要排放：氨气 NH₃]\n"
            "   来自化肥及畜禽养殖，是生成硝酸铵的关键。\n\n"
            "■ 扬尘源 (10%—20%) 🏗️\n"
            "   [主要来源：工地、道路、裸露地面]\n\n"
            "■ 生活源 🍳\n"
            "   [主要来源：散煤取暖、餐饮油烟]\n"
            "----------------------------\n"
            "⚠️ 【爆发诱因】\n"
            "当排放物遇到“静稳、高湿、逆温”天气时，会迅速发生化学转化，形成持续性雾霾。"
        )
    },
    "3": {
        "title": "💰 雾霾治理的成本与回报", 
        "content": (
            "【投入：国家行动】\n"
            "· 2013-2020年全国大气治理投入约 1.85万亿元。\n"
            "· 年均投入超过 3000亿元。\n"
            "· 仅北京一地十年治霾就投入了 7600亿元。\n\n"
            "【回报：健康与经济】\n"
            "· 浓度下降：PM2.5年均浓度从72降至29.3 μg/m³。\n"
            "· 经济效益：每投入1元治霾，可产生2—8元的综合回报(包含医疗支出减少、生产率提升)。\n\n"
            "🌟 总结：治理虽然昂贵，但不治理导致的健康和福利损失代价远超投入。"
        )
    },
    "4": {
        "title": "🧪 化学方法改善雾霾", 
        "content": (
            "👨‍🏫 老师有话说：\n\n"
            "“想要知道化学是如何改善空气质量的吗？\n"
            " 这个问题我们将在化学课堂里一起探索~\n"
            " 认真听课，千万不要走神哦！”"
        )
    },
    "5": {
        "title": "🌱 我们作为学生能做什么？", 
        "content": (
            "守护蓝天，从改变生活习惯开始：\n\n"
            "1. 🚲 绿色出行：多步行、骑车或乘坐公交。\n"
            "2. 💡 节约能源：随手关灯，合理使用空调。\n"
            "3. 🚫 杜绝焚烧：不烧垃圾、落叶，少放烟花。\n"
            "4. ✏️ 环保用品：选用低挥发性的文具和胶水。\n"
            "5. 📢 积极宣传：向家人普及成因，参与监督投诉。\n\n"
            "✨ 你的每一个微小选择，都在减少空气中形成颗粒物的前体物质。"
        )
    },
    "6": {
        "title": "🏙️ 城市与农村雾霾的区别", 
        "content": (
            "城市与农村雾霾在成因上有显著差异：\n\n"
            "【城市雾霾特征】\n"
            "· 来源：本地机动车尾气、工地扬尘、餐饮。\n"
            "· 成分：硝酸盐、黑碳比例较高。\n"
            "· 规律：随早晚交通高峰变化明显。\n\n"
            "【农村/非城市特征】\n"
            "· 来源：区域传输、农业氨气、冬季燃煤。\n"
            "· 成分：硫酸盐、铵盐比例更高。\n"
            "· 规律：日变化平缓，季节性极强。\n\n"
            "⚖️ 治理：必须采取“区域联防联控”，城乡协同减排。"
        )
    },
    "7": {
        "title": "🔍 更多奥秘探索", 
        "content": (
            "【你可能还想知道...】\n"
            "----------------------------\n"
            "● 🛰️ 卫星是如何在太空中“看穿”雾霾的？\n"
            "● 🧬 雾霾中的微生物会对生态系统产生影响吗？\n"
            "● 🌬️ 为什么有时候“等风来”是治霾最快的方法？\n"
            "● 🧪 未来的“人造雨”技术能彻底清除雾霾吗？\n\n"
            "----------------------------\n"
            "✨ 大气科学的世界还有很多未解之谜。\n"
            "保持你的好奇心，科学的进步往往始于一个意外的提问。让我们期待下一次的知识碰撞吧！"
        )
    },
}

DB_FILE = "submissions.json"
ADMIN_PASSWORD = "gxl135944"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump([], f)

def classify_text(text: str) -> str:
    # 1. 预处理：统一转为小写，避免英文大小写导致的漏判（如 SCR, PM2.5）
    text = text.lower()
    
    # 2. 定义关键词库：针对新的7类问题进行特征词提取
    # 权重设计：越独特的词（如"脱硝"、"学生"）越靠前，越通用的词越靠后
    keywords_map = {
        "6": ["区别", "不同", "差异", "城市", "农村", "乡下", "郊区", "对比", "分辨", "雾霾"],  # 城市vs非城市
        "3": ["成本", "钱", "费用", "资金", "经济", "价格", "花费", "代价", "预算", "亿", "雾霾"], # 成本
        "5": ["学生", "我们", "预防", "个人", "力所能及", "做什么", "措施", "倡议", "自身", "能做", "雾霾", "解决", "低碳"], # 学生做的
        "4": ["化学", "反应", "方程式", "催化", "脱硫", "脱硝", "scr", "转化", "氧化", "还原", "试剂", "原理", "雾霾", "解决", "改善"], # 化学方法
        "2": ["产生", "形成", "来源", "怎么来", "哪里来", "原因", "机理", "为什么", "燃烧", "排放", "生成", "雾霾", "尾气", "汽车", "车"], # 怎么产生的
        "1": ["是什么", "定义", "含义", "概念", "成分", "构成", "物质", "pm2.5", "颗粒物", "组成", "雾霾"], # 是什么
    }

    # 3. 计分逻辑：计算每个类别的匹配得分
    scores = {cid: 0 for cid in keywords_map}
    
    for cid, kws in keywords_map.items():
        for kw in kws:
            if kw in text:
                # 命中一次关键词加1分
                scores[cid] += 1
    
    # 4. 决策逻辑：找出得分最高的类别
    # max函数结合key参数，可以找出value最大的那个key
    best_category = max(scores, key=scores.get)
    
    # 如果最高分为0，说明没有任何匹配，归为第7类（其他）
    if scores[best_category] == 0:
        return "7"
        
    return best_category

# ================= 2. 路由接口 =================

@app.get("/", response_class=HTMLResponse)
async def index(): return template_html

@app.get("/check_submitted")
async def check_submitted(request: Request):
    client_ip = request.client.host
    with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        has_submitted = any(d['ip'] == client_ip for d in data)
    return {"submitted": has_submitted}

@app.post("/submit")
async def submit(
    request: Request,
    student_id: str = Form(""),
    q1: str = Form(""),
    q2: str = Form(""),
    q3: str = Form(""),
    q4: str = Form("")
):
    client_ip = request.client.host
    with open(DB_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        if any(d['ip'] == client_ip for d in data): return {"status": "already_submitted"}
        added = False
        for ans in [q1, q2, q3, q4]:
            if ans.strip():
                data.append({
                "ip": client_ip,
                "student_id": student_id,
                "text": ans,
                "cid": classify_text(ans),
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
                added = True
        if not added: return {"status": "empty"}
        f.seek(0); json.dump(data, f, ensure_ascii=False, indent=2); f.truncate()
    return {"status": "success"}

@app.get("/stats")
async def get_stats():
    with open(DB_FILE, "r", encoding="utf-8") as f: data = json.load(f)
    counts = {cid: 0 for cid in KNOWLEDGE_MAP}
    unique_ips = set()
    for d in data: 
        counts[d['cid']] += 1
        unique_ips.add(d['ip'])
    return {
        "bubbles": [{"id": cid, "name": info["title"], "value": counts[cid], "content": info["content"], "color": COLOR_MAP[cid]} for cid, info in KNOWLEDGE_MAP.items()],
        "submitted_count": len(unique_ips)
    }

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

        #modal { display:none; position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); width:700px; background:white; padding:30px; border-radius:24px; box-shadow:0 25px 50px -12px rgba(0,0,0,0.25); z-index:100; }
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
        <h1>AI赋能化学课堂：城市雾霾治理问题探究</h1>
        <p>高一化学第三章 硫氮复习课</p>
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
            <h3 style="margin-top:0; text-align:center;">假设你是环境治理工程师，要帮助城市改善雾霾问题，你需要获得哪些资料来帮助你解决这个实际问题？</h3>
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
        <p id="mc" style="
            line-height:1.6;
            color:#475569;
            font-size:14px;
            white-space: pre-wrap;
        "></p>

        <button class="btn" style="padding:10px;" onclick="closeModal()">确定</button>
    </div>
    
<script>
    let currentUserRole = "";

    // 打字机效果函数
    let typingTimer = null;
    function typeWriter(text, element, speed = 10) {
        // 清除之前的定时器
        if (typingTimer) {
            clearInterval(typingTimer);
        }
        
        element.textContent = '';
        let index = 0;
        
        typingTimer = setInterval(() => {
            if (index < text.length) {
                element.textContent += text.charAt(index);
                index++;
            } else {
                clearInterval(typingTimer);
                typingTimer = null;
            }
        }, speed);
    }

    function doSubmit() {
        const p = new URLSearchParams();

        const values = ['q1','q2','q3','q4'].map(id => {
            const v = document.getElementById(id).value;
            p.append(id, v);
            return v.trim();
        });

        if (values.every(v => !v)) {
            alert("请至少填写一项内容");
            return;
        }

        p.append("student_id", sessionStorage.getItem("student_id") || "");

        axios.post('/submit', p).then(res => {
            if(res.data.status==='success' || res.data.status==='already_submitted'){
                if(res.data.status==='already_submitted')
                    alert("该学号已提交过，直接进入查看。");

                document.getElementById('form-view').style.display='none';
                document.getElementById('bubble-view').style.display='block';
                setTimeout(() => { initCanvas(); sync(); }, 100);
            } else {
                alert("提交失败，请检查输入");
            }
        });
    }


    function switchTab(role) {
        const isStd = role === 'student';
        document.getElementById('form-student').style.display = isStd ? 'block' : 'none';
        document.getElementById('form-teacher').style.display = isStd ? 'none' : 'block';
        document.getElementById('tab-std').style.background = isStd ? '#3b82f6' : '#94a3b8';
        document.getElementById('tab-tch').style.background = isStd ? '#94a3b8' : '#8b5cf6';
    }

    function doLogin(role) {
    const data = { role: role };
    if (role === 'student') {
        data.id_code = document.getElementById('std_id').value;
    } else {
        data.username = document.getElementById('tch_user').value;
        data.password = document.getElementById('tch_pwd').value;
    }

    axios.post('/login_auth', data).then(res => {
        if (res.data.status === 'success') {
            currentUserRole = res.data.role;
            if (role === 'student') {
                sessionStorage.setItem("student_id", data.id_code);
            }

            document.getElementById('login-view').style.display = 'none';
            
            if (currentUserRole === 'student') {
                // 学生登录后检查是否已提交
                axios.get('/check_submitted').then(checkRes => {
                    if (checkRes.data.submitted) {
                        // 已提交，直接跳转到气泡图
                        document.getElementById('form-view').style.display = 'none';
                        document.getElementById('bubble-view').style.display = 'block';
                        setTimeout(() => { initCanvas(); sync(); }, 100);
                    } else {
                        // 未提交，显示表单
                        document.getElementById('form-view').style.display = 'block';
                        document.getElementById('bubble-view').style.display = 'none';
                    }
                });
            } else {
                // 教师直接进入气泡图
                document.getElementById('form-view').style.display = 'none';
                document.getElementById('bubble-view').style.display = 'block';
                setTimeout(() => { initCanvas(); sync(); }, 100); 
            }
        } else { alert(res.data.msg); }
    });
}

    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    let bubbles = [];
    let w, h, dpr;
    let mx = -1000, my = -1000;
    let currentSubmittedCount = 0;

    function initCanvas() {
        dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        w = rect.width; h = rect.height;
        canvas.width = w * dpr; canvas.height = h * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    class Bubble {
        constructor(obj) {
            // --- 必须手动补全这些丢失的属性 ---
            this.id = obj.id;
            this.name = obj.name;
            this.content = obj.content;
            this.color = obj.color;
            this.targetVal = obj.value;
            this.currVal = 0;
            this.r = 40;
            this.isHover = false;
            
            // 确保出生点在内部
            this.x = 60 + Math.random() * (w - 120 || 600); 
            this.y = 60 + Math.random() * (h - 120 || 300);
            this.vx = (Math.random() - 0.5) * 0.8; 
            this.vy = (Math.random() - 0.5) * 0.8;
        }

        update() {
            const dist = Math.sqrt((this.x - mx)**2 + (this.y - my)**2);
            this.isHover = dist < this.r;

            // --- 1. 设定目标半径逻辑 ---
            if (this.id === "7") {
                this.targetR = this.isHover ? 55 : 50;
            } else {
                // 其他气泡随 targetVal (数量) 动态增长
                this.targetR = (55 + (this.targetVal * 8)) * (this.isHover ? 1.15 : 1);
            }
            
            if (!this.isHover) { 
                this.x += this.vx; 
                this.y += this.vy; 
            }
            
            // --- 2. 修正半径演化逻辑 ---
            if (this.id === "7") {
                // ID为7时，currVal不参与半径计算，直接平滑向固定 targetR 过渡
                this.r += (this.targetR - this.r) * 0.1;
                this.currVal = this.targetVal; // 仅用于文字显示数量
            } else {
                // 其他气泡原有的增长动画逻辑
                this.currVal += (this.targetVal - this.currVal) * 0.05;
                let dynamicR = (55 + (this.currVal * 8)) * (this.isHover ? 1.15 : 1);
                this.r += (dynamicR - this.r) * 0.1;
            }

            // 边界反弹
            if (this.x - this.r < 0) { this.x = this.r; this.vx *= -1; }
            if (this.x + this.r > w) { this.x = w - this.r; this.vx *= -1; }
            if (this.y - this.r < 0) { this.y = this.r; this.vy *= -1; }
            if (this.y + this.r > h) { this.y = h - this.r; this.vy *= -1; }
        }

        draw() {
            // 如果该分类没有数据且还未完成出现动画，则不绘制
            if (this.targetVal === 0 && this.currVal < 0.1) return;
            
            ctx.save();
            ctx.beginPath(); 
            ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
            
            // 设定气泡颜色：悬停时完全不透明(FF)，平时带有透明度(AA)
            ctx.fillStyle = this.color + (this.isHover ? 'FF' : 'AA');
            ctx.fill();
            
            ctx.fillStyle = "white"; 
            ctx.textAlign = 'center'; 
            ctx.textBaseline = 'middle';

            // --- 1. 动态计算字号 ---
            // 标题字号随半径缩放，并设定最小值确保可读性
            const titleFontSize = Math.max(12, this.targetR / 5);

            ctx.font = `bold ${titleFontSize}px "PingFang SC"`;
            
            // 处理文字换行
            const lines = this.wrap(this.name, this.targetR * 1.6);
            
            // --- 2. 计算整体垂直居中偏移 ---
            // 总高度 = 标题行数 * 行高 + 数量行高
            const countFontSize = Math.max(10, titleFontSize * 0.8);
            const lineHeight = titleFontSize * 1.2;
            const totalTextHeight = (lines.length * lineHeight) + countFontSize;
            
            // 文本起始 Y 坐标
            let currentY = this.y - (totalTextHeight / 2) + (titleFontSize / 2);

            // --- 3. 绘制标题 ---
            lines.forEach((line, i) => {
                ctx.fillText(line, this.x, currentY + i * lineHeight);
            });

            // --- 4. 绘制数量 (新增) ---
            ctx.font = `normal ${countFontSize}px "PingFang SC"`;
            // 使用 Math.round 让数字在增长动画中显示为整数
            const countText = `(${Math.round(this.currVal)} 次)`;
            // 在标题下方增加 8px 的间距后绘制
            ctx.fillText(countText, this.x, currentY + (lines.length * lineHeight) + 2);
            
            ctx.restore();
        }

        wrap(text, maxW) {
            let res = [], line = "";
            for (let c of text) {
                if (ctx.measureText(line + c).width > maxW) { res.push(line); line = c; }
                else line += c;
            }
            res.push(line); return res;
        }
    }

    function render() {
        if (w && h) {
            ctx.clearRect(0,0,w,h);
            bubbles.forEach(b => { b.update(); b.draw(); });
        }
        requestAnimationFrame(render);
    }

    function sync() {
        axios.get('/stats').then(res => {
            currentSubmittedCount = res.data.submitted_count;
            document.getElementById('prog-val').innerText = `${currentSubmittedCount} / 8`;
            document.getElementById('bar-fill').style.width = (currentSubmittedCount / 8 * 100) + '%';
            res.data.bubbles.forEach(d => {
                let b = bubbles.find(x => x.id === d.id);
                if(!b) bubbles.push(new Bubble(d)); 
                else b.targetVal = d.value;
            });
        });
    }
    
    function adminResetFlow() {
        if (currentSubmittedCount > 0) {
            const saveConfirm = confirm("检测到已有数据！是否先下载CSV备份？");
            if (saveConfirm) { 
                adminExport(); 
                return; 
            }
        }
        const pwd = prompt("管理员密码：");
        if(pwd) {
            axios.get(`/admin/reset?pwd=${pwd}`).then(res => {
                if(res.data.status==='success') { 
                    alert("重置成功！");
                    location.reload(); 
                } 
                else { alert("密码错误"); }
            }).catch(err => {
                alert("重置失败：" + err.message);
            });
        }
    }

    function adminExport() {
        const pwd = prompt("管理员密码：");
        if(pwd) {
            window.location.href = `/admin/export?pwd=${pwd}`;
        }
    }

    canvas.onmousemove = e => { 
        const r = canvas.getBoundingClientRect(); 
        mx = e.clientX - r.left; 
        my = e.clientY - r.top; 
    };
    canvas.onclick = () => {
        bubbles.forEach(b => {
            if(Math.sqrt((mx-b.x)**2 + (my-b.y)**2) < b.r) {
                document.getElementById('mt').innerText = b.name;
                
                // 使用打字机效果显示内容
                const contentElement = document.getElementById('mc');
                typeWriter(b.content, contentElement, 10);
                
                document.getElementById('modal').style.display='block';
                document.getElementById('overlay').style.display='block';
            }
        });
    };
    function closeModal() {
        // 停止打字机效果
        if (typingTimer) {
            clearInterval(typingTimer);
            typingTimer = null;
        }
        
        document.getElementById('modal').style.display='none'; 
        document.getElementById('overlay').style.display='none'; 
    }
    
    // 启动渲染循环
    render();
    // 自动刷新频率
    setInterval(() => { if(document.getElementById('bubble-view').style.display !== 'none') sync(); }, 4000);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)