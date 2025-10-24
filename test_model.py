from openai import OpenAI

# 初始化客户端
client = OpenAI(
    api_key="sk-fd6c61fe94e94f4988737f7ffbc4c51e",
    base_url="https://api.siliconflow.cn/v1"
)

def chat_with_model():
    """
    在终端中与微调模型进行对话
    """
    print("🤖 微调模型对话测试开始！")
    print("输入 'quit' 或 'exit' 退出对话")
    print("-" * 50)
    
    # 初始化对话历史
    conversation_history = []
    
    while True:
        # 获取用户输入
        user_input = input("\n👤 你: ").strip()
        
        # 检查退出条件
        if user_input.lower() in ['quit', 'exit', '退出']:
            print("👋 再见！")
            break
            
        if not user_input:
            print("⚠️  请输入有效内容")
            continue
        
        # 将用户输入添加到对话历史
        conversation_history.append({"role": "user", "content": user_input})
        
        try:
            print("\n🤖 模型: ", end="", flush=True)
            
            # 调用模型（流式输出）
            response = client.chat.completions.create(
                model="ft:LoRA/Qwen/Qwen2.5-7B-Instruct:d3m6b0p719ns7391s6i0:KungFu1:ntuipfrergnoesxiccss-ckpt_step_68",
                messages=conversation_history,
                stream=True,
                max_tokens=4096,
                temperature=0.7  # 可以调整创造性程度
            )
            
            # 收集模型回复
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    print(content, end='', flush=True)
                    full_response += content
            
            # 将模型回复添加到对话历史
            if full_response:
                conversation_history.append({"role": "assistant", "content": full_response})
            
            print()  # 换行
            
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            # 移除最后一条用户消息，因为模型没有成功回复
            if conversation_history and conversation_history[-1]["role"] == "user":
                conversation_history.pop()

if __name__ == "__main__":
    chat_with_model()