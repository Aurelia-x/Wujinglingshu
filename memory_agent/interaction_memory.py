from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
import json
import os
from dotenv import load_dotenv

# 加载环境变量（从.env文件读取API密钥）
load_dotenv()

class InteractionMemoryAgent:
    def __init__(self, memory_file="chat_memory.json"):
        # 初始化LangChain的对话记忆对象
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True  # 以消息对象形式存储，方便区分用户和AI
        )
        # 记忆文件路径（用于持久化）
        self.memory_file = memory_file
        # 启动时加载历史记忆
        self._load_memory_from_file()

    def _load_memory_from_file(self):
        """从JSON文件加载历史对话（重启服务后恢复记忆）"""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r", encoding="utf-8") as f:
                history = json.load(f)
                # 循环重建记忆（每2条为一轮：用户消息+AI消息）
                for i in range(0, len(history), 2):
                    user_msg = history[i].get("content", "")  # 第1、3、5...条是用户消息
                    # 第2、4、6...条是AI消息（防止索引越界）
                    ai_msg = history[i+1].get("content", "") if i+1 < len(history) else ""
                    # 存入记忆对象
                    self.memory.save_context(
                        inputs={"input": user_msg},
                        outputs={"output": ai_msg}
                    )

    def save_conversation(self, user_query: str, ai_response: str):
        """保存本轮对话到记忆，并持久化到文件"""
        # 先存入内存中的记忆对象
        self.memory.save_context(
            inputs={"input": user_query},
            outputs={"output": ai_response}
        )
        # 再写入文件（持久化）
        self._save_memory_to_file()

    def _save_memory_to_file(self):
        """将内存中的记忆写入JSON文件"""
        # 从记忆对象中获取所有历史对话
        history = self.memory.load_memory_variables({})["chat_history"]
        # 转换为可JSON序列化的格式（提取类型和内容）
        serializable_history = [
            {
                "type": "user" if isinstance(msg, HumanMessage) else "ai",
                "content": msg.content
            }
            for msg in history
        ]
        # 写入文件
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(serializable_history, f, ensure_ascii=False, indent=2)

    def get_context(self, new_query: str) -> str:
        """生成与新问题相关的历史上下文"""
        # 从记忆中加载相关历史
        history = self.memory.load_memory_variables({"input": new_query})["chat_history"]
        # 格式化上下文字符串
        context = "以下是与当前问题相关的历史对话：\n"
        for msg in history:
            if isinstance(msg, HumanMessage):
                context += f"用户：{msg.content}\n"
            elif isinstance(msg, AIMessage):
                context += f"助手：{msg.content}\n"
        return context