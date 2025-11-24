from langchain.chat_models import ChatOpenAI
from interaction_memory import InteractionMemoryAgent  # 导入记忆智能体

class MemoryEnhancedModel:
    def __init__(self):
        self.model = ChatOpenAI(
            model_name="ft:LoRA/Qwen/Qwen2.5-7B-Instruct:d3m6b0p719ns7391s6i0:lingshuwujing_v1:hfbdqgmcwfkwkmnlcias", 
            openai_api_key="sk-xtlpxfyxxbnxkvpmjtgfutsuhpvjcxsuylintjldvaqtmdmy",        
            openai_api_base="https://api.siliconflow.cn/v1",
            temperature=0.7 
        )
        # 初始化记忆智能体（自动加载历史记忆）
        self.memory_agent = InteractionMemoryAgent()

    def generate_response(self, user_query: str) -> str:
        """结合记忆生成连贯回答"""
        # 1. 获取历史上下文
        context = self.memory_agent.get_context(user_query)
        
        # 2. 构建带上下文的提示词
        prompt = f"""
        请结合以下历史对话，回答用户的新问题：
        {context}
        现在用户的问题是：{user_query}
        回答需连贯、自然，符合上下文逻辑。
        """
        
        # 3. 调用大模型生成回答
        response = self.model.predict(prompt)
        
        # 4. 保存本轮对话到记忆（包含用户问题和AI回答）
        self.memory_agent.save_conversation(user_query, response)
        
        return response