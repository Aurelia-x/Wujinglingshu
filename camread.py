import cv2
import time
import match
import posemesh
import os

def capture_camera_continuously():
    # 打开默认摄像头（通常是0，若有多个摄像头可尝试1、2等）
    cap = cv2.VideoCapture(0)
    #创建关键动作列表，方便顺序比对
    keymotion_path="./test_files/keymotion"
    li=[]
    for items in os.listdir(keymotion_path):
        if items.endswith('.json'):
            li.append( os.path.join(keymotion_path,items))
    motion_number=0

    # 检查摄像头是否成功打开
    if not cap.isOpened():
        print("无法打开摄像头")
        return
    
    try:
        while True:
            # 读取一帧图像
            ret, frame = cap.read()
            
            # 检查是否成功读取帧
            if not ret:
                print("无法获取图像帧")
                break

            
            # 保存图像到根目录，覆盖之前的文件,并处理得到骨架，将骨架与关键动作骨架配对
            cv2.imwrite("./caminput/camera_capture.jpg", frame)
            posemesh.process_camera(frame,"./caminput/processed.json")
            if match.motion_match_or_not(li[motion_number],"./caminput/processed.json"):
                motion_number=motion_number+1
                #print(li[motion_number])
                print(f"匹配成功\033[31m{li[motion_number]}\033[0m")
                

            # 等待0.5秒
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n程序已手动终止")
    finally:
        # 释放摄像头资源
        cap.release()
        print("摄像头已关闭")

if __name__ == "__main__":
    capture_camera_continuously()