import json
import math
import os
from typing import Dict, List, Tuple

# ----------------------
# 1. 计算骨架整体法向量
# ----------------------
def calculate_skeleton_normal(skel: Dict) -> Tuple[float, float, float]:
    """
    计算骨架的整体法向量（基于躯干平面）
    躯干平面由左肩、右肩、右髋三点确定（稳定且能反映整体朝向）
    """
    # 关键躯干点（确保存在且可见性高）
    required_points = ['left_shoulder', 'right_shoulder', 'right_hip']
    for p in required_points:
        if p not in skel or skel[p]['visibility'] < 0.6:
            # 若关键躯干点缺失，返回默认向量（降低权重）
            return (0.0, 1.0, 0.0)  # 假设默认向上
    
    # 提取三点坐标
    A = (skel['left_shoulder']['x'], skel['left_shoulder']['y'], skel['left_shoulder']['z'])
    B = (skel['right_shoulder']['x'], skel['right_shoulder']['y'], skel['right_shoulder']['z'])
    C = (skel['right_hip']['x'], skel['right_hip']['y'], skel['right_hip']['z'])
    
    # 计算平面向量 AB 和 AC
    AB = (B[0]-A[0], B[1]-A[1], B[2]-A[2])
    AC = (C[0]-A[0], C[1]-A[1], C[2]-A[2])
    
    # 叉乘求法向量（垂直于躯干平面，反映朝向）
    normal = (
        AB[1]*AC[2] - AB[2]*AC[1],
        AB[2]*AC[0] - AB[0]*AC[2],
        AB[0]*AC[1] - AB[1]*AC[0]
    )
    
    # 归一化法向量
    norm = math.sqrt(normal[0]**2 + normal[1]** 2 + normal[2]**2)
    if norm < 1e-6:
        return (0.0, 1.0, 0.0)  # 避免零向量
    return (normal[0]/norm, normal[1]/norm, normal[2]/norm)

# ----------------------
# 2. 计算法向量夹角（反映朝向差异）
# ----------------------
def calculate_normal_angle(normal1: Tuple[float, float, float], normal2: Tuple[float, float, float]) -> float:
    """计算两个法向量的夹角（弧度），范围[0, π]，值越大朝向差异越大"""
    dot_product = sum(a*b for a, b in zip(normal1, normal2))
    # 防止数值溢出导致的精度问题
    dot_product = max(min(dot_product, 1.0), -1.0)
    return math.acos(dot_product)

# ----------------------
# 3. 融合多特征的相似度评分
# ----------------------
def calculate_skeleton_similarity(input_skel: Dict, sample_skel: Dict) -> float:
    """
    综合评分 = 关键点距离权重 + 法向量夹角权重
    值越小，相似度越高（位置接近且朝向一致）
    """
    # （1）计算关键点距离（同之前逻辑，增加权重区分关键部位）
    key_points = {
        # 躯干关键点（权重高，稳定性强）
        'left_shoulder': 1.5, 'right_shoulder': 1.5,
        'left_hip': 1.5, 'right_hip': 1.5,
        # 四肢关键点（权重中等）
        'left_elbow': 1.0, 'right_elbow': 1.0,
        'left_knee': 1.0, 'right_knee': 1.0,
        # 末端关键点（权重低，易抖动）
        'left_wrist': 0.8, 'right_wrist': 0.8,
        'left_ankle': 0.8, 'right_ankle': 0.8
    }
    
    total_distance = 0.0
    total_weight = 0.0
    
    for point, weight in key_points.items():
        if point in input_skel and point in sample_skel:
            # 可见度加权
            vis_weight = 0.5 + 0.5 * min(input_skel[point]['visibility'], sample_skel[point]['visibility'])
            # 3D距离
            dx = input_skel[point]['x'] - sample_skel[point]['x']
            dy = input_skel[point]['y'] - sample_skel[point]['y']
            dz = input_skel[point]['z'] - sample_skel[point]['z']
            dist = math.sqrt(dx**2 + dy**2 + dz**2)
            # 累加带权重的距离
            total_distance += dist * weight * vis_weight
            total_weight += weight * vis_weight
    
    avg_distance = total_distance / total_weight if total_weight > 0 else float('inf')
    
    # （2）计算法向量夹角（朝向差异）
    normal_input = calculate_skeleton_normal(input_skel)
    normal_sample = calculate_skeleton_normal(sample_skel)
    angle = calculate_normal_angle(normal_input, normal_sample)  # 弧度，范围[0, π]
    
    # （3）融合评分：距离占比60%，朝向夹角占比40%（可调整）
    # 夹角转换为与距离同量级的评分（例如π弧度≈3.14，乘以系数0.1缩放）
    angle_score = angle * 0.1
    final_score = 0.6 * avg_distance + 0.4 * angle_score
    
    return final_score

# ----------------------
# 4. 其他辅助函数（文件夹加载、匹配逻辑）
# ----------------------
def load_skeleton(file_path: str) -> Dict:
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载文件 {file_path} 失败: {e}")
        return None

def load_skeletons_from_dir(dir_path: str) -> List[Tuple[str, Dict]]:
    skeletons = []
    if not os.path.exists(dir_path):
        print(f"文件夹 {dir_path} 不存在")
        return skeletons
    
    for filename in os.listdir(dir_path):
        if filename.endswith('.json'):
            file_path = os.path.join(dir_path, filename)
            skel = load_skeleton(file_path)
            if skel:
                skeletons.append((filename, skel))
    return skeletons

def find_best_match(input_skel: Dict, sample_skels: List[Tuple[str, Dict]]) -> Tuple[str, float]:
    best_filename = None
    best_score = float('inf')
    for sample_filename, sample_skel in sample_skels:
        score = calculate_skeleton_similarity(input_skel, sample_skel)
        if score < best_score:
            best_score = score
            best_filename = sample_filename
    return best_filename, best_score


def motion_match_or_not(keymotion_path:str,input_file:str) -> bool:
        score = calculate_skeleton_similarity(load_skeleton(input_file),load_skeleton(keymotion_path))
        if score<0.25:
            return True
        else:
            return False




# ----------------------
# 主函数
# ----------------------
def main():
    input_dir = "./caminput"
    sample_dir = "./test_files/video_output"
    
    input_skeletons = load_skeletons_from_dir(input_dir)
    sample_skeletons = load_skeletons_from_dir(sample_dir)
    
    if not sample_skeletons:
        print("没有找到样本骨架，程序退出")
        return
    
    # 阈值根据实际数据调整（值越小匹配越严格）
    match_threshold = 0.2
    
    print("开始匹配...")
    for input_filename, input_skel in input_skeletons:
        best_sample, best_score = find_best_match(input_skel, sample_skeletons)
        print(f"\n输入文件: {input_filename}")
        print(f"最佳匹配样本: {best_sample}")
        print(f"综合匹配评分: {best_score:.6f}")
        print("匹配结果: " + ("成功" if best_score < match_threshold else "失败"))

if __name__ == "__main__":
    main()