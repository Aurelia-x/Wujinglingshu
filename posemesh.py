#从test_files读wushu.mp4，没15帧截取一次，将截取的图像处理为对应的图片以及json骨架文件保存到./test_files/video_output
import cv2
import mediapipe as mp
import numpy as np
import json
import os
from datetime import timedelta

# 初始化MediaPipe组件
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

LANDMARK_NAMES = {
    0: "nose",               # 鼻子（作为头部关键点）
    1: "left_eye_inner",     # 左眼内侧
    2: "left_eye",           # 左眼
    3: "left_eye_outer",     # 左眼外侧
    4: "right_eye_inner",    # 右眼内侧
    5: "right_eye",          # 右眼
    6: "right_eye_outer",    # 右眼外侧
    7: "left_ear",           # 左耳
    8: "right_ear",          # 右耳
    11: "left_shoulder",     # 左肩
    12: "right_shoulder",    # 右肩
    13: "left_elbow",        # 左肘
    14: "right_elbow",       # 右肘
    15: "left_wrist",        # 左腕
    16: "right_wrist",       # 右腕
    23: "left_hip",          # 左髋
    24: "right_hip",         # 右髋
    25: "left_knee",         # 左膝
    26: "right_knee",        # 右膝
    27: "left_ankle",        # 左踝
    28: "right_ankle",       # 右踝
    29: "left_heel",         # 左脚跟
    30: "right_heel",        # 右脚跟
    31: "left_foot_index",   # 左足食指
    32: "right_foot_index"   # 右足食指
}

# 定义需要保留的关键点ID
KEEP_LANDMARKS = {
    11, 12, 13, 14, 15, 16,  # 肩、肘、腕
    23, 24, 25, 26, 27, 28,  # 髋、膝、踝
    29, 30, 31, 32           # 脚
}

# 定义精简后的骨骼连接关系（使用原始ID）
REDUCED_CONNECTIONS = [
    (0, 1),    # 头顶-下巴
    (11, 12),  # 左肩-右肩
    (11, 13),  # 左肩-左肘
    (13, 15),  # 左肘-左手腕
    (12, 14),  # 右肩-右肘
    (14, 16),  # 右肘-右手腕
    (11, 23),  # 左肩-左髋
    (12, 24),  # 右肩-右髋
    (23, 24),  # 左髋-右髋
    (23, 25),  # 左髋-左膝
    (25, 27),  # 左膝-左脚踝
    (27, 29),  # 左脚踝-左脚趾
    (27, 31),  # 左脚踝-左 heel
    (24, 26),  # 右髋-右膝
    (26, 28),  # 右膝-右脚踝
    (28, 30),  # 右脚踝-右脚趾
    (28, 32)   # 右脚踝-右 heel
]

def draw_filtered_landmarks(image, landmarks, connections):
    """手动绘制过滤后的关键点和连接"""
    image_height, image_width, _ = image.shape
    
    # 存储要保留的关键点坐标
    landmark_coords = {}
    
    # 绘制关键点
    for idx, landmark in enumerate(landmarks.landmark):
        if idx in KEEP_LANDMARKS:
            # 将归一化坐标转换为像素坐标
            x = int(landmark.x * image_width)
            y = int(landmark.y * image_height)
            landmark_coords[idx] = (x, y)
            
            # 绘制关键点
            cv2.circle(image, (x, y), 5, (245, 117, 66), -1)
    
    # 绘制连接
    for connection in connections:
        start_idx, end_idx = connection
        if start_idx in landmark_coords and end_idx in landmark_coords:
            cv2.line(image, 
                     landmark_coords[start_idx], 
                     landmark_coords[end_idx], 
                     (245, 66, 230), 2)
    
    return image

def detect_pose_with_reduced_head(image, output_path=None):
    """处理图像，使用精简后的头部节点"""
    if image is None:
        print("无效的图像数据")
        return False, None
    
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=0.5) as pose:
        
        results = pose.process(image_rgb)
        
        if results.pose_landmarks:
            # 绘制过滤后的骨架
            image = draw_filtered_landmarks(
                image, 
                results.pose_landmarks, 
                REDUCED_CONNECTIONS
            )
        
        if output_path:
            cv2.imwrite(output_path, image)
            print(f"处理后的图像已保存至: {output_path}")
            return True, results.pose_landmarks
        else:
            return True, results.pose_landmarks

def get_universal_skeleton_coords(landmarks):
    """从landmarks获取人体骨架的通用标准化坐标"""
    if not landmarks:
        print("未检测到人体姿态")
        return None
    
    # 提取并标准化关键点坐标
    skeleton_data = {}
    for idx, landmark in enumerate(landmarks.landmark):
        if idx in KEEP_LANDMARKS:
            # 坐标已经是标准化的（0-1范围）
            skeleton_data[LANDMARK_NAMES[idx]] = {
                "x": round(landmark.x, 6),
                "y": round(landmark.y, 6),
                "z": round(landmark.z, 6),
                "visibility": round(landmark.visibility, 6)
            }
    
    return skeleton_data

def add_tag_to_json_data(file_path, tags):
    """在JSON数据中添加多个标签字段"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 添加标签字段
        for key, value in tags.items():
            data[key] = value
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"已成功添加标签字段: {tags}")
        
    except Exception as e:
        print(f"操作失败：{str(e)}")

def save_skeleton_data(skeleton_data, output_path):
    """将骨架坐标数据保存为JSON文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(skeleton_data, f, ensure_ascii=False, indent=4)
    print(f"骨架坐标数据已保存至: {output_path}")

def process_video(video_path, output_folder, interval=15):
    """
    处理视频文件，每interval帧截取一次动作
    video_path: 输入视频路径
    output_folder: 输出文件夹
    interval: 截取间隔（帧数）
    """
    # 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"已创建输出文件夹: {output_folder}")
    
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频文件: {video_path}")
        return
    
    # 获取视频基本信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    print(f"视频信息: FPS={fps:.2f}, 总帧数={total_frames}, 时长={duration:.2f}秒")
    
    frame_count = 0
    extract_count = 0
    
    with mp_pose.Pose(
        static_image_mode=False,  # 视频模式
        model_complexity=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as pose:
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break  # 视频读取完毕
            
            # 每interval帧处理一次
            if frame_count % interval == 0:
                extract_count += 1
                # 生成输出文件名
                img_filename = f"frame_{extract_count:04d}.jpg"
                img_path = os.path.join(output_folder, img_filename)
                json_path = os.path.join(output_folder, f"frame_{extract_count:04d}.json")
                
                # 计算当前帧在视频中的时间（秒）
                frame_time = frame_count / fps
                # 转换为时分秒格式
                time_str = str(timedelta(seconds=frame_time))
                
                print(f"\n处理第{extract_count}个截取帧 (帧号: {frame_count}, 时间: {time_str})")
                
                # 处理帧并检测姿态
                success, landmarks = detect_pose_with_reduced_head(frame.copy(), img_path)
                if success and landmarks:
                    # 获取骨架数据
                    skeleton_data = get_universal_skeleton_coords(landmarks)
                    if skeleton_data:
                        # 保存骨架数据
                        save_skeleton_data(skeleton_data, json_path)
                        # 添加标签（包括时间信息）
                        add_tag_to_json_data(json_path, {
                            "type": "video_frame",
                            "frame_number": frame_count,
                            "time_seconds": round(frame_time, 3),
                            "time_format": time_str
                        })
            
            frame_count += 1
            # 显示进度
            if frame_count % 100 == 0:
                progress = (frame_count / total_frames) * 100
                print(f"处理进度: {progress:.1f}%")
    
    cap.release()
    print(f"\n视频处理完成，共截取 {extract_count} 帧")
    print(f"结果保存至: {output_folder}")

if __name__ == "__main__":
    # 视频路径和输出文件夹
    video_path = "./test_files/wushu.mp4"  # 输入视频文件
    output_folder = "./test_files/video_output"  # 输出文件夹
    
    # 处理视频，每15帧截取一次
    process_video(video_path, output_folder, interval=15)