from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from openai import OpenAI
import json
import datetime
import os
import threading

app = Flask(__name__)
CORS(app, origins=["http://localhost:*", "http://127.0.0.1:*", "http://192.168.*"])

# 初始化OpenAI客户端
client = OpenAI(
    api_key="sk-xtlpxfyxxbnxkvpmjtgfutsuhpvjcxsuylintjldvaqtmdmy",
    base_url="https://api.siliconflow.cn/v1"
)

# 存储对话历史
conversation_history = {}

# 姿势数据计数器
request_count = 0

@app.route('/api/pose-data', methods=['POST'])
def receive_pose_data():
    """接收前端发送的姿势数据"""
    global request_count
    request_count += 1
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "没有接收到数据"}), 400
        
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        frame_num = data.get('frame_number', '未知')
        
        # 每50帧输出一次日志，避免过多输出
        if request_count % 50 == 0:
            print(f"✅ 姿势数据 - 已接收 {request_count} 帧, 最新帧: {frame_num}")
        
        # 异步保存调试数据
        def async_save():
            try:
                save_debug_data(data, frame_num)
            except Exception as e:
                pass  # 忽略保存错误
        
        threading.Thread(target=async_save).start()
        
        return jsonify({
            "status": "success",
            "message": f"接收帧 {frame_num}",
            "received_count": request_count,
            "timestamp": current_time
        })
        
    except Exception as e:
        print(f"❌ 处理姿势数据出错: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """处理AI对话请求"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        user_id = data.get('user_id', 'default')
        
        print(f"💬 收到用户消息: {user_message}")
        
        # 获取或初始化用户的对话历史
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        
        # 添加用户消息到历史
        conversation_history[user_id].append({"role": "user", "content": user_message})
        
        # 构建消息列表（包含历史对话）
        messages = conversation_history[user_id]
        
        # 调用大模型
        response = client.chat.completions.create(
            model="ft:LoRA/Qwen/Qwen2.5-7B-Instruct:d3m6b0p719ns7391s6i0:KungFu1:ntuipfrergnoesxiccss-ckpt_step_68",
            messages=messages,
            stream=True,
            max_tokens=4096
        )
        
        # 流式返回响应
        def generate():
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'content': content, 'done': False})}\n\n"
            
            # 添加AI回复到历史记录
            conversation_history[user_id].append({"role": "assistant", "content": full_response})
            
            # 发送结束信号
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
        
        return Response(generate(), mimetype='text/plain')
    
    except Exception as e:
        print(f"❌ 聊天处理出错: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """清空对话历史"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        
        if user_id in conversation_history:
            conversation_history[user_id] = []
            print(f"🗑️  已清空用户 {user_id} 的对话历史")
        
        return jsonify({"status": "success", "message": "对话历史已清空"})
    except Exception as e:
        print(f"❌ 清空历史出错: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_connection():
    """测试连接端点"""
    return jsonify({
        "message": "后端服务器正常运行",
        "total_pose_requests": request_count,
        "active_chat_users": len(conversation_history),
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/reset', methods=['POST'])
def reset_counter():
    """重置姿势数据计数器"""
    global request_count
    request_count = 0
    return jsonify({"message": "姿势数据计数器已重置", "count": request_count})

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy", 
        "message": "服务运行正常",
        "pose_requests": request_count,
        "chat_users": len(conversation_history)
    })

def save_debug_data(data, frame_num):
    """保存调试数据到文件"""
    try:
        # 创建调试目录
        debug_dir = "debug_data"
        os.makedirs(debug_dir, exist_ok=True)
        
        # 保存完整数据
        filename = f"{debug_dir}/frame_{frame_num:04d}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        # 只保存最近10帧的数据，避免文件过多
        if int(frame_num) > 10:
            old_file = f"{debug_dir}/frame_{int(frame_num)-10:04d}.json"
            if os.path.exists(old_file):
                os.remove(old_file)
                
    except Exception as e:
        print(f"保存调试数据失败: {e}")

@app.route('/')
def index():
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>综合后端服务器</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .status {{ padding: 10px; background: #e8f5e8; border-radius: 5px; }}
            .endpoints {{ margin-top: 20px; }}
            .endpoint {{ background: #f5f5f5; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            .section {{ margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>综合后端服务器</h1>
        
        <div class="status">
            <p><strong>服务器状态:</strong> 运行中</p>
            <p><strong>姿势数据请求:</strong> {request_count}</p>
            <p><strong>活跃聊天用户:</strong> {len(conversation_history)}</p>
        </div>
        
        <div class="section">
            <h3>姿势识别端点:</h3>
            <div class="endpoint">
                <strong>POST /api/pose-data</strong> - 接收姿势数据
            </div>
            <div class="endpoint">
                <strong>GET /api/test</strong> - 测试连接
            </div>
            <div class="endpoint">
                <strong>POST /api/reset</strong> - 重置姿势数据计数器
            </div>
        </div>
        
        <div class="section">
            <h3>AI对话端点:</h3>
            <div class="endpoint">
                <strong>POST /chat</strong> - AI对话（流式响应）
            </div>
            <div class="endpoint">
                <strong>POST /clear_history</strong> - 清空对话历史
            </div>
        </div>
        
        <div class="section">
            <h3>系统端点:</h3>
            <div class="endpoint">
                <strong>GET /health</strong> - 健康检查
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("=" * 60)
    print("🤖 综合后端服务器启动中...")
    print("=" * 60)
    print("📊 功能模块:")
    print("   • 姿势识别数据接收")
    print("   • AI对话服务 (基于 Silicon Flow)")
    print("=" * 60)
    print("🌐 访问 http://localhost:5000 查看服务器状态")
    print("📱 前端应访问:")
    print("   • 姿势识别: http://localhost:5000/api/pose-data")
    print("   • AI对话: http://localhost:5000/chat")
    print("=" * 60)
    print("⏹️  按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=False,
        threaded=True
    )