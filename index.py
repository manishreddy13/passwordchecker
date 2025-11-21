from flask import Flask, render_template_string, request, jsonify
import random, string

app = Flask(__name__)

def check_strength(pw):
    if not pw:
        return {"score": 0, "level": "Empty"}
    
    score = len(pw) * 5
    if any(c.isupper() for c in pw): score += 15
    if any(c.islower() for c in pw): score += 15
    if any(c.isdigit() for c in pw): score += 15
    if any(c in "!@#$%^&*()" for c in pw): score += 20
    
    score = min(100, score)
    return {"score": score, "level": ["Very Weak", "Weak", "Medium", "Strong", "Very Strong"][min(4, score // 25)]}

def ai_response(msg):
    msg = msg.lower()
    if "generate" in msg or "create" in msg:
        return "Try clicking the Generate button to create a strong password!"
    if "strong" in msg or "good" in msg:
        return "Great! Your password is strong. Keep it safe!"
    if "weak" in msg or "bad" in msg:
        return "Add more characters, numbers, and special symbols to strengthen it!"
    return "I can help with password security. Ask me anything!"

@app.route('/')
def home():
    return render_template_string(HOME_HTML)

@app.route('/checker')
def checker():
    return render_template_string(CHECKER_HTML)

@app.route('/check', methods=['POST'])
def check():
    pw = request.json.get('password', '')
    return jsonify(check_strength(pw))

@app.route('/generate', methods=['POST'])
def generate():
    chars = string.ascii_letters + string.digits + "!@#$%^&*()"
    pw = ''.join(random.choice(chars) for _ in range(16))
    return jsonify({"password": pw})

@app.route('/chat', methods=['POST'])
def chat():
    msg = request.json.get('message', '')
    return jsonify({"reply": ai_response(msg)})

HOME_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Welcome</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { text-align: center; background: white; padding: 60px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        h1 { font-size: 3rem; color: #333; margin-bottom: 30px; }
        .go-btn { background: #667eea; color: white; padding: 15px 50px; font-size: 1.2rem; border: none; border-radius: 8px; cursor: pointer; transition: 0.3s; }
        .go-btn:hover { background: #764ba2; transform: scale(1.05); }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to the Website</h1>
        <button class="go-btn" onclick="window.location.href='/checker'">Go</button>
    </div>
</body>
</html>"""

CHECKER_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Password Checker</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        .main { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        .chat { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); display: flex; flex-direction: column; }
        h1 { color: #333; margin-bottom: 20px; }
        .input-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; color: #333; }
        input[type="password"], input[type="text"] { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 1rem; }
        input:focus { outline: none; border-color: #667eea; }
        .meter { background: #ddd; height: 20px; border-radius: 10px; overflow: hidden; margin-top: 10px; }
        .meter-fill { height: 100%; width: 0%; background: #667eea; transition: 0.3s; }
        .score { font-size: 1.5rem; font-weight: bold; color: #667eea; margin-top: 10px; }
        .buttons { display: flex; gap: 10px; margin-top: 20px; }
        button { flex: 1; padding: 12px; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: bold; transition: 0.3s; }
        .btn-generate { background: #26de81; color: white; }
        .btn-generate:hover { background: #20c997; }
        .btn-home { background: #3498db; color: white; }
        .btn-home:hover { background: #2980b9; }
        .chat-header { background: #667eea; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; font-weight: bold; }
        .messages { flex: 1; overflow-y: auto; margin-bottom: 10px; padding: 10px; background: #f5f5f5; border-radius: 8px; max-height: 300px; }
        .msg { margin: 8px 0; padding: 10px; border-radius: 6px; }
        .msg.user { background: #667eea; color: white; text-align: right; }
        .msg.ai { background: #ddd; color: #333; }
        .chat-input { display: flex; gap: 8px; }
        .chat-input input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }
        .chat-input button { width: 50px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; }
        @media(max-width: 768px) { .container { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="main">
            <h1>Password Strength Checker</h1>
            <div class="input-group">
                <label>Enter Password:</label>
                <input type="password" id="pw" placeholder="Type your password...">
                <div class="meter"><div class="meter-fill" id="fill"></div></div>
                <div class="score">Strength: <span id="score">0%</span> - <span id="level">Empty</span></div>
            </div>
            <div class="buttons">
                <button class="btn-generate" onclick="generatePassword()">Generate New Password</button>
                <button class="btn-home" onclick="window.location.href='/'">Home</button>
            </div>
        </div>
        
        <div class="chat">
            <div class="chat-header">AI Chat</div>
            <div class="messages" id="messages"></div>
            <div class="chat-input">
                <input type="text" id="msg" placeholder="Ask me..." onkeypress="if(event.key==='Enter')sendMsg()">
                <button onclick="sendMsg()">Send</button>
            </div>
        </div>
    </div>

    <script>
        const pw = document.getElementById('pw');
        const fill = document.getElementById('fill');
        const score = document.getElementById('score');
        const level = document.getElementById('level');
        const messages = document.getElementById('messages');
        const msg = document.getElementById('msg');

        pw.addEventListener('input', () => {
            fetch('/check', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: pw.value})
            })
            .then(r => r.json())
            .then(d => {
                score.textContent = d.score + '%';
                level.textContent = d.level;
                fill.style.width = d.score + '%';
                fill.style.background = ['#ff4757', '#ffa502', '#ffc107', '#26de81', '#20c997'][Math.min(4, Math.floor(d.score / 25))];
            });
        });

        function generatePassword() {
            fetch('/generate', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'})
            .then(r => r.json())
            .then(d => {
                pw.value = d.password;
                pw.type = 'text';
                pw.dispatchEvent(new Event('input'));
            });
        }

        function sendMsg() {
            const text = msg.value.trim();
            if (!text) return;
            
            const userDiv = document.createElement('div');
            userDiv.className = 'msg user';
            userDiv.textContent = text;
            messages.appendChild(userDiv);
            msg.value = '';
            
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: text})
            })
            .then(r => r.json())
            .then(d => {
                const aiDiv = document.createElement('div');
                aiDiv.className = 'msg ai';
                aiDiv.textContent = d.reply;
                messages.appendChild(aiDiv);
                messages.scrollTop = messages.scrollHeight;
            });
        }
    </script>
</body>
</html>"""
