    #对骨架文件进行配对，输入在./caminput文件夹，样本在./test_files/video_output文件夹（之后可能再改动来提高精度）对于智能语言播报，可以选取每一个动作的结束动作与摄像头输入进行配对，配对成功则自动播报下一项动作的语音
import json
import math
import os
from typing import Dict, List, Tuple

def load_skeleton(file_path: str) -> Dict:
    """加载单个骨架数据文件"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件 {file_path} 失败: {e}")
        return None

def load_skeletons_from_dir(dir_path: str) -> List[Dict]:
    """从文件夹加载所有骨架数据（仅处理.json文件）"""
    skeletons = []
    if not os.path.exists(dir_path):
        print(f"文件夹 {dir_path} 不存在")
        return skeletons
    
    for filename in os.listdir(dir_path):
        if filename.endswith('.json'):
            file_path = os.path.join(dir_path, filename)
            skel = load_skeleton(file_path)
            if skel:
                skeletons.append((filename, skel))  # 保留文件名用于结果输出
    return skeletons

def calculate_point_distance(point1: Dict, point2: Dict) -> float:
    """计算两个3D关键点之间的加权欧氏距离"""
    # 可见度低的点权重降低（可见度0-1之间）
    visibility_weight = 0.5 + 0.5 * min(point1['visibility'], point2['visibility'])
    distance = math.sqrt(
        (point1['x'] - point2['x'])**2 +
        (point1['y'] - point2['y'])** 2 +
        (point1['z'] - point2['z'])**2
    )
    return distance * visibility_weight  # 可见度越高，权重越大

def calculate_skeleton_similarity(input_skel: Dict, sample_skel: Dict) -> float:
    """计算两个骨架的相似度（值越小越相似）"""
    # 定义需要比较的关键点列表（与输入文件中的关键点对应）
    key_points = [
        'left_shoulder', 'right_shoulder',
        'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist',
        'left_hip', 'right_hip',
        'left_knee', 'right_knee',
        'left_ankle', 'right_ankle',
        'left_heel', 'right_heel',
        'left_foot_index', 'right_foot_index'
    ]
    
    total_distance = 0.0
    valid_points = 0
    
    # 计算每个对应关键点的距离
    for point in key_points:
        if point in input_skel and point in sample_skel:
            total_distance += calculate_point_distance(input_skel[point], sample_skel[point])
            valid_points += 1
    
    # 返回平均距离作为相似度评分（越小越相似）
    return total_distance / valid_points if valid_points > 0 else float('inf')

def find_best_match(input_skel: Dict, sample_skels: List[Tuple[str, Dict]]) -> Tuple[str, float]:
    """在样本骨架列表中找到与输入骨架最匹配的样本（返回文件名和评分）"""
    best_filename = None
    best_score = float('inf')
    
    for sample_filename, sample_skel in sample_skels:
        score = calculate_skeleton_similarity(input_skel, sample_skel)
        if score < best_score:
            best_score = score
            best_filename = sample_filename
    
    return best_filename, best_score

def main():
    # 配置文件夹路径
    input_dir = "./caminput"
    sample_dir = "./test_files/video_output"
    
    # 加载所有输入骨架和样本骨架
    print(f"正在加载输入骨架（{input_dir}）...")
    input_skeletons = load_skeletons_from_dir(input_dir)
    print(f"共加载 {len(input_skeletons)} 个输入骨架")
    
    print(f"\n正在加载样本骨架（{sample_dir}）...")
    sample_skeletons = load_skeletons_from_dir(sample_dir)
    print(f"共加载 {len(sample_skeletons)} 个样本骨架")
    
    if not sample_skeletons:
        print("没有找到样本骨架，程序退出")
        return
    
    # 设置匹配阈值（可根据实际数据调整）
    match_threshold = 0.15  # 评分低于此值视为有效匹配
    
    # 批量处理每个输入骨架
    print("\n开始匹配...")
    for input_filename, input_skel in input_skeletons:
        best_sample, best_score = find_best_match(input_skel, sample_skeletons)
        print(f"\n输入文件: {input_filename}")
        print(f"最佳匹配样本: {best_sample}")
        print(f"匹配评分: {best_score:.6f}")
        print("匹配结果: " + ("成功" if best_score < match_threshold else "失败"))

if __name__ == "__main__":

    main()
