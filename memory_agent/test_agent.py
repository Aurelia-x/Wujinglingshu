from model_interface import MemoryEnhancedModel  # 导入带记忆的模型

def test_memory_workflow():
    # 初始化智能体（首次启动，无历史记忆）
    agent = MemoryEnhancedModel()
    print("=== 第一轮对话 ===")
    query1 = "太极拳的基本步法有哪些？"
    response1 = agent.generate_response(query1)
    print(f"用户：{query1}")
    print(f"AI：{response1}\n")
    
    # 第二轮对话（依赖第一轮的记忆）
    print("=== 第二轮对话 ===")
    query2 = "刚才说白鹤亮翅怎么练？"  # 提到“刚才说的”，验证上下文关联
    response2 = agent.generate_response(query2)
    print(f"用户：{query2}")
    print(f"AI：{response2}\n")
    
    # 模拟重启服务（重新初始化智能体，验证记忆是否保留）
    print("=== 模拟重启服务后 ===")
    agent_restarted = MemoryEnhancedModel()  # 重新初始化，会加载之前的记忆文件
    query3 = "再说说进步的要点？"  # 继续追问步法，验证记忆是否生效
    response3 = agent_restarted.generate_response(query3)
    print(f"用户：{query3}")
    print(f"AI：{response3}")

if __name__ == "__main__":
    test_memory_workflow()  # 执行测试