import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS  # 解决前端跨域请求问题
from match import calculate_skeleton_similarity, load_skeletons_from_dir  # 复用现有匹配算法
from chat import client  # 复用现有AI模型客户端（避免重复配置）
# 动作比较智能体核心类（调度+逻辑处理）
class ActionAgent:
    def __init__(self):
        # 初始化状态变量
        self.sample_skeletons = []  # 存储加载的样本骨架（格式：[(样本名, 骨架数据), ...]）
        self.match_threshold = 0.15  # 匹配阈值（越小越严格，可后续调整）

    def load_samples(self, sample_dir="./test_files/video_output"):
        """第一步：加载样本骨架库（从posemesh.py生成的文件夹中读取）"""
        # 调用match.py的现成函数，加载所有样本骨架
        self.sample_skeletons = load_skeletons_from_dir(sample_dir)
        print(f"✅ 成功加载 {len(self.sample_skeletons)} 个样本骨架")
        return len(self.sample_skeletons)  # 返回样本数量，用于前端验证

    def compare_skeleton(self, input_skel):
        """第二步：比对输入骨架与样本库，返回最佳匹配结果"""
        # 先检查样本库是否为空
        if not self.sample_skeletons:
            return None, "❌ 样本库为空，请先加载样本"
        
        best_score = float('inf')  # 初始最佳分数（越小越匹配）
        best_sample_name = None    # 最佳匹配的样本名

        # 遍历所有样本，找到与输入骨架最匹配的
        for sample_name, sample_skel in self.sample_skeletons:
            # 调用match.py的相似度计算函数（核心算法复用）
            similarity_score = calculate_skeleton_similarity(input_skel, sample_skel)
            
            # 更新最佳匹配（分数更小=更匹配）
            if similarity_score < best_score:
                best_score = similarity_score
                best_sample_name = sample_name

        # 判断是否匹配成功（分数 < 阈值）
        is_match_success = best_score < self.match_threshold

        # 返回结构化的比对结果
        return {
            "样本名称": best_sample_name,
            "相似度分数": round(best_score, 4),
            "是否匹配成功": is_match_success,
            "匹配阈值": self.match_threshold
        }, None  # 第二个返回值为错误信息，无错误则为None

    def generate_feedback(self, match_result):
        """第三步：根据比对结果，调用AI生成自然语言反馈"""
        if not match_result:
            return "❌ 未完成动作比对，请先上传动作数据"

        # 构造AI提示词（让反馈更精准，贴合太极教学场景）
        prompt = f"""
        你是太极动作教学助手，根据以下动作比对结果，生成简洁易懂的反馈：
        1. 比对结果：用户动作与「{match_result['样本名称']}」的相似度分数为{match_result['相似度分数']}（阈值{match_result['匹配阈值']}）
        2. 匹配状态：{"成功" if match_result['是否匹配成功'] else "失败"}
        3. 反馈要求：
           - 匹配成功：鼓励用户，并提示下一步动作（如“请继续练习下一个动作‘弓步’”）
           - 匹配失败：指出可能的偏差关节（如左膝、右肩），给出1条具体修正建议（避免专业术语）
           - 语气亲切，符合教学场景，不超过2句话
        """

        # 调用chat.py的AI客户端（复用已配置的微调模型）
        response = client.chat.completions.create(
            model="ft:LoRA/Qwen/Qwen2.5-7B-Instruct:d3m6b0p719ns7391s6i0:lingshuwujing_v1:hfbdqgmcwfkwkmnlcias",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150  # 限制反馈长度，避免冗余
        )

        # 提取AI反馈内容并返回
        return response.choices[0].message.content.strip()
    # 初始化Flask服务（供前端调用）
app = Flask(__name__)
CORS(app)  # 允许跨域请求（前端和后端端口不同时必需）

# 初始化动作比较智能体实例
action_agent = ActionAgent()

# 接口1：加载样本骨架库（前端可主动调用，验证样本是否加载成功）
@app.route('/api/load-samples', methods=['GET'])
def api_load_samples():
    sample_count = action_agent.load_samples()
    return jsonify({
        "状态": "成功",
        "加载样本数量": sample_count,
        "提示": f"已从 test_files/video_output 加载 {sample_count} 个样本骨架"
    })

# 接口2：核心接口——接收前端骨架数据，返回比对结果+AI反馈
@app.route('/api/compare-action', methods=['POST'])
def api_compare_action():
    # 1. 接收前端发送的骨架数据（JSON格式）
    request_data = request.get_json()
    input_skeleton = request_data.get('skeleton')  # 前端传入的用户骨架数据

    # 2. 检查是否收到骨架数据
    if not input_skeleton:
        return jsonify({"状态": "失败", "错误信息": "未收到骨架数据，请上传动作"}), 400

    # 3. 调用智能体的比对功能
    match_result, error_msg = action_agent.compare_skeleton(input_skeleton)
    if error_msg:
        return jsonify({"状态": "失败", "错误信息": error_msg}), 400

    # 4. 调用智能体的AI反馈功能
    ai_feedback = action_agent.generate_feedback(match_result)

    # 5. 返回最终结果给前端
    return jsonify({
        "状态": "成功",
        "比对结果": match_result,
        "AI动作反馈": ai_feedback
    })

# 接口3：测试服务是否正常运行
@app.route('/api/test', methods=['GET'])
def api_test():
    return jsonify({"状态": "成功", "提示": "动作比较智能体服务已启动"})
if __name__ == "__main__":
    # 启动时自动加载样本骨架（无需手动调用接口）
    action_agent.load_samples()
    # 启动Flask服务（端口5001，避免与chat.py的5000端口冲突）
    app.run(host='0.0.0.0', port=5001, debug=True)
    print("🚀 动作比较智能体服务已启动，端口：5001")