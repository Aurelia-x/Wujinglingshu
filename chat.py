from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from openai import OpenAI
import json

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化OpenAI客户端
client = OpenAI(
    api_key="sk-xtlpxfyxxbnxkvpmjtgfutsuhpvjcxsuylintjldvaqtmdmy",
    base_url="https://api.siliconflow.cn/v1"
)

# 存储对话历史（在实际应用中应该使用数据库）
conversation_history = {}

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        user_id = data.get('user_id', 'default')  # 简单的用户标识
        
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
        return jsonify({"error": str(e)}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """清空对话历史"""
    try:
        data = request.json
        user_id = data.get('user_id', 'default')
        
        if user_id in conversation_history:
            conversation_history[user_id] = []
        
        return jsonify({"status": "success", "message": "对话历史已清空"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "healthy", "message": "服务运行正常"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)