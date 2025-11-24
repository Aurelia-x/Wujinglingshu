from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import threading
import time
import os
import sys
import requests

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 设置默认目录为当前目录
        super().__init__(*args, directory=os.getcwd(), **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # 简化日志输出，避免过多信息
        pass

def start_http_server():
    port = 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    
    print("=" * 60)
    print("🚀 网页系统启动成功!")
    print("=" * 60)
    print(f"📁 服务目录: {os.getcwd()}")
    print(f"🌐 前端地址: http://localhost:{port}")
    print(f"🔧 后端地址: http://localhost:5000")
    print("=" * 60)
    print("📋 可用页面:")
    print(f"   • 主页面: http://localhost:{port}/index.html")
    print(f"   • 骨架识别: http://localhost:{port}/pose_fixed.html") 
    print(f"   • AI对话: http://localhost:{port}/chat.html")
    print("=" * 60)
    print("💡 提示: 确保后端服务器也在运行: python test_server.py")
    print("⏹️  按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    httpd.serve_forever()

def check_backend_server():
    """检查后端服务器是否运行"""
    
    try:
        response = requests.get('http://localhost:5000/api/test', timeout=2)
        if response.status_code == 200:
            print("✅ 后端服务器连接正常")
            return True
    except:
        print("❌ 后端服务器未运行或连接失败")
        print("   请运行: python test_server.py")
        return False

def create_missing_files():
    """检查并创建必要的文件"""
    required_files = {
        'index.html': '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>骨架识别与AI对话系统</title>
    <link href="https://unpkg.com/material-components-web@latest/dist/material-components-web.min.css" rel="stylesheet">
    <style>
        body { font-family: roboto, sans-serif; margin: 2em; color: #3d3d3d; }
        .container { max-width: 800px; margin: 0 auto; text-align: center; }
        .card { margin: 2em 0; padding: 1.5em; border: 1px solid #e0e0e0; border-radius: 8px; }
        h1 { margin-bottom: 1em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>骨架识别与AI对话系统</h1>
        
        <div class="card">
            <h2>实时骨架识别</h2>
            <p>使用摄像头实时检测和追踪人体骨架关键点</p>
            <button onclick="window.location.href='pose_fixed.html'" class="mdc-button mdc-button--raised">
                <span class="mdc-button__label">进入骨架识别</span>
            </button>
        </div>
        
        <div class="card">
            <h2>AI对话助手</h2>
            <p>与智能AI助手进行自然对话</p>
            <button onclick="window.location.href='chat.html'" class="mdc-button mdc-button--raised">
                <span class="mdc-button__label">进入AI对话</span>
            </button>
        </div>
    </div>
</body>
</html>''',
        
        'script_fixed.js': '''// 简化的骨架识别脚本，用于测试
console.log("脚本加载成功 - 请确保使用完整的 script_fixed.js 文件");

class PoseDetector {
    constructor() {
        console.log("PoseDetector 初始化");
        this.setupWebcam();
    }
    
    setupWebcam() {
        const enableWebcamButton = document.getElementById("webcamButton");
        enableWebcamButton.addEventListener("click", () => this.enableCam());
    }
    
    async enableCam() {
        const button = document.getElementById("webcamButton");
        if (button.innerText === "开启摄像头") {
            button.innerText = "停止摄像头";
            document.getElementById('cameraStatus').textContent = '模拟运行中';
            document.getElementById('backendStatus').textContent = '模拟连接';
        } else {
            button.innerText = "开启摄像头";
            document.getElementById('cameraStatus').textContent = '已停止';
        }
    }
}

new PoseDetector();'''
    }
    
    for filename, content in required_files.items():
        if not os.path.exists(filename):
            print(f"📄 创建缺失文件: {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

if __name__ == '__main__':
    # 检查必要文件
    create_missing_files()
    
    # 检查后端服务器
    check_backend_server()
    
    # 启动HTTP服务器
    server_thread = threading.Thread(target=start_http_server)
    server_thread.daemon = True
    server_thread.start()
    
    # 等待服务器启动
    time.sleep(1)
    
    # 自动打开主页面
    webbrowser.open(f'http://localhost:8000/index.html')
    
    try:
        # 保持服务器运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 服务器已停止")
        sys.exit(0)