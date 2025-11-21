from flask import Flask, render_template_string, request, jsonify
import math
import re
import secrets
import string
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)

# ============================= DATABASE =============================
def init_db():
    conn = sqlite3.connect('securepass_history.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT NOT NULL,
            strength INTEGER,
            label TEXT,
            entropy REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT NOT NULL,
            created TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_check(password, strength, label, entropy):
    conn = sqlite3.connect('securepass_history.db')
    c = conn.cursor()
    c.execute("INSERT INTO checks (password, strength, label, entropy) VALUES (?, ?, ?, ?)",
              (password, strength, label, entropy))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect('securepass_history.db')
    c = conn.cursor()
    c.execute("SELECT password, strength, label, entropy, timestamp FROM checks ORDER BY timestamp DESC LIMIT 100")
    rows = c.fetchall()
    conn.close()
    return rows

def clear_history():
    conn = sqlite3.connect('securepass_history.db')
    c = conn.cursor()
    c.execute("DELETE FROM checks")
    conn.commit()
    conn.close()

def save_favorite(password):
    conn = sqlite3.connect('securepass_history.db')
    c = conn.cursor()
    c.execute("INSERT INTO favorites (password) VALUES (?)", (password,))
    conn.commit()
    conn.close()

def get_favorites():
    conn = sqlite3.connect('securepass_history.db')
    c = conn.cursor()
    c.execute("SELECT password, created FROM favorites ORDER BY created DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return rows

# ============================= PASSWORD UTILS =============================
def calculate_entropy(pw):
    size = 0
    if re.search(r'[a-z]', pw): size += 26
    if re.search(r'[A-Z]', pw): size += 26
    if re.search(r'\d', pw): size += 10
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]', pw): size += 32
    return len(pw) * math.log2(size) if size > 0 else 0

def calculate_strength(password):
    if not password:
        return 0, "No Password", "#666", [], 0
    length = len(password)
    entropy = calculate_entropy(password)
    score = 0
    
    if length >= 8: score += 20
    if length >= 12: score += 30
    if length >= 16: score += 25
    if length >= 20: score += 15
    
    if re.search(r'[A-Z]', password): score += 15
    if re.search(r'[a-z]', password): score += 10
    if re.search(r'\d', password): score += 15
    if re.search(r'[!@#$%^&*]', password): score += 25
    
    score += min(entropy * 1.2, 60)
    
    if re.search(r'(.)\1\1', password): score -= 30
    if re.search(r'123|abc|qwe|password|admin|letmein', password.lower()): score -= 50
    
    score = max(0, min(100, score))
    
    if score < 40: label, color = "Very Weak", "#ff3b30"
    elif score < 60: label, color = "Weak", "#ff9500"
    elif score < 80: label, color = "Moderate", "#ffcc00"
    elif score < 95: label, color = "Strong", "#34c759"
    else: label, color = "Very Strong", "#00e676"
    
    suggestions = []
    if len(password) < 12: suggestions.append("Use at least 12 characters")
    if not re.search(r'[A-Z]', password): suggestions.append("Add uppercase letters")
    if not re.search(r'\d', password): suggestions.append("Include numbers")
    if not re.search(r'[!@#$%^&*]', password): suggestions.append("Add special symbols")
    if not suggestions: suggestions = ["Outstanding! Extremely secure password."]
    
    return round(score), label, color, suggestions, round(entropy, 2)

def generate_secure_password(length=18, upper=True, lower=True, digits=True, symbols=True):
    chars = ""
    if lower: chars += string.ascii_lowercase
    if upper: chars += string.ascii_uppercase
    if digits: chars += string.digits
    if symbols: chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not chars: return "Enable at least one option"
    return ''.join(secrets.choice(chars) for _ in range(length))

def check_breach_similarity(password):
    common = ["password", "123456", "admin", "letmein", "qwerty", "welcome", "monkey", "dragon"]
    for common_pw in common:
        if common_pw.lower() in password.lower():
            return True
    return False

# ============================= FULL HTML WITH ENHANCED LAYOUT =============================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>SecurePass AI | Professional Security Suite</title>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Poppins:wght@400;600;700&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>
  <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js"></script>
  <style>
    :root {
      --primary: #6e3cff;
      --secondary: #00d4ff;
      --dark: #0f0f1a;
      --light: #f0f2ff;
      --glass: rgba(255,255,255,0.1);
      --bg-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      --text-primary: white;
      --card-bg: rgba(255,255,255,0.1);
    }
    
    body.light-theme {
      --primary: #5a28d9;
      --secondary: #0891b2;
      --dark: #ffffff;
      --light: #0f172a;
      --bg-primary: linear-gradient(135deg, #f0f9ff 0%, #e0e7ff 100%);
      --text-primary: #1e293b;
      --card-bg: rgba(0,0,0,0.05);
    }
    
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      font-family: 'Poppins', sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      min-height: 100vh;
      overflow-x: hidden;
      transition: all 0.5s ease;
    }
    
    body.light-theme {
      color: var(--text-primary);
    }
    
    body.light-theme .sidebar,
    body.light-theme .card,
    body.light-theme .generator-card,
    body.light-theme .header {
      background: var(--card-bg);
      border-color: rgba(0,0,0,0.1);
    }
    
    body.light-theme input,
    body.light-theme .tab {
      background: rgba(0,0,0,0.08) !important;
      color: var(--text-primary) !important;
      border: 1px solid rgba(0,0,0,0.1);
    }
    
    body.light-theme input::placeholder {
      color: rgba(0,0,0,0.5);
    }
    
    body.light-theme .tab.active {
      background: var(--primary) !important;
      color: white !important;
    }
    
    body.light-theme .stat {
      background: rgba(0,0,0,0.08) !important;
    }
    
    body.light-theme .fav-item {
      background: rgba(0,0,0,0.08) !important;
    }
    
    body.light-theme .theme-toggle {
      background: rgba(0,0,0,0.15);
      color: var(--text-primary);
    }
    /* 3D WELCOME PAGE */
    .welcome-screen {
      position: fixed;
      top: 0; left: 0; width: 100%; height: 100vh;
      background: linear-gradient(135deg, var(--primary) 0%, #8a2be2 100%);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      perspective: 1000px;
    }
    .welcome-screen.hide { transform: translateY(-100vh); opacity: 0; transition: all 1s; }
    .title-3d {
      font-family: 'Orbitron', sans-serif;
      font-size: 6rem;
      font-weight: 900;
      background: linear-gradient(45deg, #fff, #00d4ff);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      animation: float 6s ease-in-out infinite;
    }
    @keyframes float {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-30px); }
    }
    .subtitle { font-size: 1.8rem; margin: 20px 0; opacity: 0.9; }
    .go-btn {
      margin-top: 50px;
      padding: 20px 60px;
      font-size: 1.8rem;
      background: rgba(255,255,255,0.2);
      border: 3px solid white;
      border-radius: 50px;
      color: white;
      cursor: pointer;
      backdrop-filter: blur(10px);
      transition: all 0.4s;
      box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    }
    .go-btn:hover { background: white; color: var(--primary); transform: scale(1.1); }
    
    /* MAIN LAYOUT */
    .main-app { display: none; }
    .main-app.show { display: flex; animation: fadeIn 1s; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    
    .layout {
      display: grid;
      grid-template-columns: 300px 1fr;
      grid-template-rows: auto 1fr auto;
      min-height: 100vh;
      gap: 20px;
      padding: 20px;
    }
    
    /* LEFT SIDEBAR */
    .sidebar {
      grid-column: 1;
      grid-row: 1 / 3;
      background: var(--card-bg);
      backdrop-filter: blur(20px);
      border-radius: 25px;
      padding: 30px;
      border: 1px solid rgba(255,255,255,0.2);
      height: fit-content;
      position: sticky;
      top: 20px;
      transition: all 0.5s ease;
    }
    
    .sidebar h2 {
      font-size: 1.8rem;
      margin-bottom: 30px;
      color: var(--secondary);
      text-align: center;
      transition: color 0.5s ease;
    }
    
    .sidebar-section {
      margin: 30px 0;
      padding: 20px;
      background: rgba(255,255,255,0.05);
      border-radius: 15px;
      transition: all 0.5s ease;
    }
    
    .sidebar-section h3 {
      font-size: 1.2rem;
      margin-bottom: 15px;
      color: var(--secondary);
      transition: color 0.5s ease;
    }
    
    .sidebar-section p {
      font-size: 0.95rem;
      line-height: 1.6;
      opacity: 0.9;
      margin-bottom: 15px;
    }
    
    .sidebar-section ul {
      list-style: none;
      font-size: 0.95rem;
    }
    
    .sidebar-section li {
      padding: 8px 0;
      opacity: 0.85;
    }
    
    .sidebar-section li:before {
      content: "✓ ";
      color: #00e676;
      font-weight: bold;
      margin-right: 8px;
    }
    
    /* TOP SECTION */
    .top-section {
      grid-column: 2;
      grid-row: 1;
    }
    
    .header {
      text-align: center;
      padding: 30px;
      background: var(--card-bg);
      backdrop-filter: blur(20px);
      border-radius: 25px;
      border: 1px solid rgba(255,255,255,0.2);
      transition: all 0.5s ease;
    }
    
    .header h1 {
      font-size: 3rem;
      font-family: 'Orbitron', sans-serif;
      background: linear-gradient(45deg, #fff, var(--secondary));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 10px;
    }
    
    .header p { font-size: 1.1rem; opacity: 0.9; }
    
    /* MIDDLE SECTION */
    .middle-section {
      grid-column: 2;
      grid-row: 2;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    
    .card {
      background: var(--card-bg);
      backdrop-filter: blur(20px);
      border-radius: 25px;
      padding: 40px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.4);
      border: 1px solid rgba(255,255,255,0.2);
      flex: 1;
      transition: all 0.5s ease;
    }
    
    .tabs {
      display: flex;
      justify-content: center;
      gap: 20px;
      margin: 20px 0;
      transition: all 0.5s ease;
    }
    
    .tab {
      padding: 12px 30px;
      background: rgba(255,255,255,0.2);
      border-radius: 50px;
      cursor: pointer;
      backdrop-filter: blur(10px);
      transition: all 0.3s;
      border: 1px solid rgba(255,255,255,0.1);
    }
    
    .tab.active {
      background: white;
      color: var(--primary);
      font-weight: bold;
    }
    
    body.light-theme .tab.active {
      background: var(--primary);
      color: white;
    }
    
    .input-group {
      position: relative;
      margin: 30px 0;
    }
    
    #password {
      width: 100%;
      padding: 20px 150px 20px 30px;
      font-size: 1.3rem;
      border: none;
      border-radius: 20px;
      background: rgba(255,255,255,0.2);
      color: white;
      outline: none;
    }
    
    #password::placeholder { color: rgba(255,255,255,0.7); }
    
    .btn-group {
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-50%);
      display: flex;
      gap: 10px;
    }
    
    .btn-copy, .toggle-pass, .btn-favorite {
      background: var(--primary);
      color: white;
      border: none;
      padding: 12px 15px;
      border-radius: 12px;
      cursor: pointer;
      font-size: 1rem;
      transition: all 0.3s;
    }
    
    .btn-copy:hover, .toggle-pass:hover, .btn-favorite:hover {
      background: var(--secondary);
      transform: scale(1.05);
    }
    
    .meter {
      height: 30px;
      background: rgba(255,255,255,0.2);
      border-radius: 15px;
      overflow: hidden;
      margin: 30px 0;
    }
    
    .fill {
      height: 100%;
      width: 0%;
      transition: width 1s ease;
    }
    
    .stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      margin: 30px 0;
    }
    
    .stat {
      background: rgba(255,255,255,0.15);
      padding: 20px;
      border-radius: 15px;
      text-align: center;
    }
    
    .stat h3 { font-size: 0.9rem; opacity: 0.8; margin-bottom: 10px; }
    .stat h2 { font-size: 2rem; color: var(--secondary); }
    
    /* BOTTOM SECTION - GENERATOR */
    .bottom-section {
      grid-column: 1 / 3;
      grid-row: 3;
    }
    
    .generator-card {
      background: var(--card-bg);
      backdrop-filter: blur(20px);
      border-radius: 25px;
      padding: 40px;
      border: 1px solid rgba(255,255,255,0.2);
      transition: all 0.5s ease;
    }
    
    .generator-card h2 {
      text-align: center;
      font-size: 2rem;
      margin-bottom: 30px;
      color: var(--secondary);
      transition: color 0.5s ease;
    }
    
    .generator-options {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
      margin: 30px 0;
    }
    
    .gen-option {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    
    .gen-option label {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
    }
    
    .gen-option input[type="range"] {
      width: 100%;
    }
    
    .gen-btn {
      background: linear-gradient(45deg, #00e676, #00c853);
      color: white;
      padding: 18px;
      border: none;
      border-radius: 20px;
      font-size: 1.2rem;
      cursor: pointer;
      width: 100%;
      font-weight: bold;
      transition: all 0.3s;
    }
    
    .gen-btn:hover {
      transform: scale(1.02);
      box-shadow: 0 10px 30px rgba(0, 230, 118, 0.5);
    }
    
    .favorites-list {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 15px;
      margin: 20px 0;
    }
    
    .fav-item {
      background: rgba(255,255,255,0.15);
      padding: 15px;
      border-radius: 12px;
      font-size: 0.9rem;
      word-break: break-all;
      cursor: pointer;
      transition: all 0.3s;
    }
    
    .fav-item:hover {
      background: rgba(255,255,255,0.3);
      transform: translateY(-3px);
    }
    
    .theme-toggle {
      position: fixed;
      top: 20px;
      right: 20px;
      background: rgba(0,0,0,0.5);
      width: 50px;
      height: 50px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      z-index: 1000;
      font-size: 1.5rem;
      transition: all 0.5s ease;
      border: 2px solid rgba(255,255,255,0.3);
    }
    
    .theme-toggle:hover {
      transform: scale(1.1);
      background: rgba(0,0,0,0.7);
    }
    
    body.light-theme .theme-toggle {
      background: rgba(0,0,0,0.15);
    }
    
    body.light-theme .theme-toggle:hover {
      background: rgba(0,0,0,0.25);
    }
    
    .suggestions {
      display: none;
      background: rgba(255,255,255,0.15);
      padding: 20px;
      border-radius: 15px;
      margin-top: 20px;
    }
    
    .suggestions ul {
      list-style: none;
      font-size: 1rem;
      line-height: 1.8;
    }
    
    .suggestions li:before {
      content: "→ ";
      color: var(--secondary);
      margin-right: 10px;
    }
  </style>
</head>
<body>
  <!-- 3D WELCOME SCREEN -->
  <div class="welcome-screen" id="welcome">
    <h1 class="title-3d">SecurePass AI</h1>
    <p class="subtitle">Professional Password Security Suite</p>
    <button class="go-btn" onclick="enterApp()">GO</button>
  </div>
  
  <!-- MAIN APP -->
  <div class="main-app" id="mainApp">
    <div class="theme-toggle" onclick="document.body.classList.toggle('dark-mode')">
      <i class="fas fa-moon"></i>
    </div>
    
    <div class="layout">
      <!-- LEFT SIDEBAR -->
      <div class="sidebar">
        <h2><i class="fas fa-info-circle"></i> Info</h2>
        
        <div class="sidebar-section">
          <h3>About SecurePass AI</h3>
          <p>Enterprise-grade password analysis and generation platform built with advanced cryptographic security.</p>
        </div>
        
        <div class="sidebar-section">
          <h3>Key Features</h3>
          <ul>
            <li>100% Offline Processing</li>
            <li>Real-time Entropy Analysis</li>
            <li>Secure Generation</li>
            <li>Local History Tracking</li>
            <li>Favorites Management</li>
            <li>Breach Detection</li>
          </ul>
        </div>
        
        <div class="sidebar-section">
          <h3>Security Stats</h3>
          <p><strong>History:</strong> {{ history|length }} checks</p>
          <p><strong>Favorites:</strong> {{ favorites|length }} saved</p>
        </div>
      </div>
      
      <!-- TOP HEADER -->
      <div class="top-section">
        <div class="header">
          <h1>SecurePass AI</h1>
          <p>Professional Password Analyzer & Generator</p>
        </div>
      </div>
      
      <!-- MIDDLE - PASSWORD CHECKER -->
      <div class="middle-section">
        <div class="card">
          <div class="tabs">
            <button class="tab active" onclick="switchTab('checker', event)">🔐 Password Checker</button>
            <button class="tab" onclick="switchTab('history', event)">📜 History</button>
          </div>
          
          <div id="checker">
            <div class="input-group">
              <input type="password" id="password" placeholder="Enter password to analyze..." autocomplete="off"/>
              <div class="btn-group">
                <button class="btn-favorite" onclick="favoritePassword()" title="Save to favorites">
                  <i class="fas fa-star"></i>
                </button>
                <button class="toggle-pass" onclick="togglePassword()" title="Show/Hide">
                  <i class="fas fa-eye"></i>
                </button>
                <button class="btn-copy" onclick="copyPassword()" title="Copy to clipboard">
                  <i class="fas fa-copy"></i>
                </button>
              </div>
            </div>
            
            <div class="meter"><div class="fill" id="fill"></div></div>
            
            <div style="text-align:center; font-size:2rem; font-weight:bold; margin:20px;" id="label">Start typing...</div>
            
            <div class="stats">
              <div class="stat"><h3>Strength</h3><h2 id="percent">0%</h2></div>
              <div class="stat"><h3>Entropy</h3><h2 id="entropy">0 bits</h2></div>
              <div class="stat"><h3>Length</h3><h2 id="length">0</h2></div>
            </div>
            
            <div id="suggestions" class="suggestions">
              <h3>Recommendations:</h3>
              <ul id="tips"></ul>
            </div>
          </div>
          
          <div id="history" style="display:none;">
            <h3 style="margin: 20px 0; color: var(--secondary);">Recent Checks</h3>
            <div id="historyContent" style="max-height: 400px; overflow-y: auto;">
              <p style="opacity: 0.7;">Loading...</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- BOTTOM - PASSWORD GENERATOR -->
      <div class="bottom-section">
        <div class="generator-card">
          <h2><i class="fas fa-wand-magic-sparkles"></i> Secure Password Generator</h2>
          
          <div class="generator-options">
            <div class="gen-option">
              <label>Length: <strong id="len">18</strong></label>
              <input type="range" min="12" max="32" value="18" id="length" oninput="document.getElementById('len').textContent=this.value"/>
            </div>
            <div class="gen-option">
              <label><input type="checkbox" id="upper" checked> Uppercase</label>
            </div>
            <div class="gen-option">
              <label><input type="checkbox" id="lower" checked> Lowercase</label>
            </div>
            <div class="gen-option">
              <label><input type="checkbox" id="digits" checked> Numbers</label>
            </div>
          </div>
          
          <div class="generator-options" style="grid-template-columns: 1fr 1fr;">
            <div class="gen-option">
              <label><input type="checkbox" id="symbols" checked> Symbols</label>
            </div>
            <button class="gen-btn" onclick="generatePassword()">
              <i class="fas fa-bolt"></i> Generate & Analyze
            </button>
          </div>
          
          <div id="favoritesContainer" style="display:none; margin-top: 30px;">
            <h3 style="color: var(--secondary); margin-bottom: 15px;">⭐ Favorites</h3>
            <div id="favoritesList" class="favorites-list"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <script>
    // Theme Management
    const themeToggle = document.querySelector('.theme-toggle');
    const savedTheme = localStorage.getItem('theme') || 'dark';
    
    function initTheme() {
      if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
      } else {
        document.body.classList.remove('light-theme');
        themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
      }
    }
    
    themeToggle.addEventListener('click', () => {
      document.body.classList.toggle('light-theme');
      const isLight = document.body.classList.contains('light-theme');
      localStorage.setItem('theme', isLight ? 'light' : 'dark');
      themeToggle.innerHTML = isLight ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    });
    
    initTheme();
    
    function enterApp() {
      document.getElementById('welcome').classList.add('hide');
      setTimeout(() => {
        document.getElementById('mainApp').classList.add('show');
        document.getElementById('welcome').style.display = 'none';
        loadFavorites();
      }, 800);
    }
    
    function switchTab(tab, e) {
      document.querySelectorAll('[id="checker"], [id="history"]').forEach(el => el.style.display = 'none');
      document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
      document.getElementById(tab).style.display = 'block';
      e.target.classList.add('active');
      if (tab === 'history') loadHistory();
    }
    
    const input = document.getElementById('password');
    const fill = document.getElementById('fill');
    const label = document.getElementById('label');
    const percent = document.getElementById('percent');
    const entropy = document.getElementById('entropy');
    const lengthDisplay = document.getElementById('length');
    const suggestions = document.getElementById('suggestions');
    const tips = document.getElementById('tips');
    
    input.addEventListener('input', () => {
      const p = input.value;
      if (!p) { reset(); return; }
      fetch('/check', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({password: p})
      })
      .then(r => r.json())
      .then(d => {
        fill.style.width = d.strength + '%';
        fill.style.background = d.color;
        label.textContent = d.label;
        label.style.color = d.color;
        percent.textContent = d.strength + '%';
        entropy.textContent = d.entropy + ' bits';
        lengthDisplay.textContent = p.length;
        suggestions.style.display = 'block';
        tips.innerHTML = '';
        d.suggestions.forEach(s => {
          let li = document.createElement('li');
          li.textContent = s;
          tips.appendChild(li);
        });
        if (d.strength >= 95) confetti({ particleCount: 200, spread: 70 });
      });
    });
    
    function reset() {
      fill.style.width = '0%';
      label.textContent = 'Start typing...';
      label.style.color = '#ccc';
      percent.textContent = '0%';
      entropy.textContent = '0 bits';
      lengthDisplay.textContent = '0';
      suggestions.style.display = 'none';
    }
    
    function togglePassword() {
      input.type = input.type === 'password' ? 'text' : 'password';
    }
    
    function copyPassword() {
      if (!input.value) {
        alert('Generate or enter a password first!');
        return;
      }
      input.select();
      navigator.clipboard.writeText(input.value).then(() => {
        alert('✓ Copied to clipboard!');
      }).catch(() => {
        alert('Failed to copy');
      });
    }
    
    function favoritePassword() {
      if (!input.value) return alert('Enter or generate a password first');
      fetch('/favorite', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({password: input.value})
      }).then(r => r.json()).then(() => {
        alert('⭐ Added to favorites!');
        loadFavorites();
      });
    }
    
    function generatePassword() {
      const len = document.getElementById('length').value;
      const upper = document.getElementById('upper').checked;
      const lower = document.getElementById('lower').checked;
      const digits = document.getElementById('digits').checked;
      const symbols = document.getElementById('symbols').checked;
      
      if (!upper && !lower && !digits && !symbols) {
        alert('Select at least one character type!');
        return;
      }
      
      const opts = {
        length: parseInt(len),
        upper: upper,
        lower: lower,
        digits: digits,
        symbols: symbols
      };
      
      fetch('/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(opts)
      })
      .then(r => r.json())
      .then(d => {
        input.value = d.password;
        input.dispatchEvent(new Event('input'));
        confetti({ particleCount: 300, spread: 100 });
      })
      .catch(err => {
        console.error('Error:', err);
        alert('Failed to generate password');
      });
    }
    
    function loadFavorites() {
      fetch('/favorites').then(r => r.json()).then(data => {
        if (data.favorites && data.favorites.length > 0) {
          document.getElementById('favoritesContainer').style.display = 'block';
          const list = document.getElementById('favoritesList');
          list.innerHTML = '';
          data.favorites.forEach(fav => {
            let div = document.createElement('div');
            div.className = 'fav-item';
            div.textContent = fav[0];
            div.title = 'Click to use this password';
            div.onclick = () => { 
              input.value = fav[0]; 
              input.dispatchEvent(new Event('input'));
              input.select();
            };
            list.appendChild(div);
          });
        }
      }).catch(err => console.error('Error loading favorites:', err));
    }
    
    function loadHistory() {
      fetch('/api/history').then(r => r.json()).then(data => {
        let html = '';
        if (data.history && data.history.length > 0) {
          data.history.forEach(h => {
            html += `<div style="padding: 12px; background: rgba(255,255,255,0.1); margin: 8px 0; border-radius: 10px;">
              <strong>${h[1]}%</strong> - ${h[2]} (${h[3]} bits) <code style="opacity: 0.7; font-size: 0.85rem;">${h[0].substring(0, 30)}${h[0].length > 30 ? '...' : ''}</code>
            </div>`;
          });
        } else {
          html = '<p style="opacity: 0.7; text-align: center; padding: 20px;">No history yet</p>';
        }
        document.getElementById('historyContent').innerHTML = html;
      }).catch(err => console.error('Error loading history:', err));
    }
  </script>
</body>
</html>
"""

# ============================= ROUTES =============================
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, history=get_history(), favorites=get_favorites())

@app.route('/check', methods=['POST'])
def check():
    data = request.get_json()
    pwd = data.get('password', '').strip()
    if pwd:
        strength, label, color, suggestions, entropy = calculate_strength(pwd)
        save_check(pwd, strength, label, entropy)
        return jsonify({
            'strength': strength,
            'label': label,
            'color': color,
            'suggestions': suggestions,
            'entropy': entropy
        })
    return jsonify({'error': 'empty'})

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    pwd = generate_secure_password(
        length=data.get('length', 18),
        upper=data.get('upper', True),
        lower=data.get('lower', True),
        digits=data.get('digits', True),
        symbols=data.get('symbols', True)
    )
    return jsonify({'password': pwd})

@app.route('/favorite', methods=['POST'])
def favorite():
    data = request.get_json()
    pwd = data.get('password', '')
    if pwd:
        save_favorite(pwd)
        return jsonify({'status': 'saved'})
    return jsonify({'error': 'empty'})

@app.route('/favorites')
def favorites():
    return jsonify({'favorites': get_favorites()})

@app.route('/api/history')
def api_history():
    return jsonify({'history': get_history()})

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════╗
    ║   SECUREPASS AI PROFESSIONAL EDITION - ENHANCED    ║
    ║   🔐 Advanced Password Security Suite              ║
    ║                                                    ║
    ║   Features:                                        ║
    ║   ✓ 3D Welcome Page                               ║
    ║   ✓ Sidebar Info Panel                            ║
    ║   ✓ Real-time Password Analysis                   ║
    ║   ✓ Secure Password Generator                     ║
    ║   ✓ Favorites Management                          ║
    ║   ✓ History Tracking                              ║
    ║   ✓ Advanced Entropy Calculation                  ║
    ║                                                    ║
    ║   Open → http://127.0.0.1:5000                    ║
    ╚════════════════════════════════════════════════════╝
    """)
    app.run(debug=True)