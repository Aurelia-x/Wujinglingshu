import json
import math
import os
import posemesh
import match


if __name__ == "__main__":
    posemesh.process_camera("./caminput/example.jpg","./caminput/processed.json")
    
    input_dir = "./caminput"
    sample_dir = "./test_files/video_output"
    
    input_skeletons = load_skeletons_from_dir(input_dir)
    sample_skeletons = load_skeletons_from_dir(sample_dir)
    
    match_threshold = 0.2
    
    print("开始匹配...")
    for input_filename, input_skel in input_skeletons:
        best_sample, best_score = find_best_match(input_skel, sample_skeletons)
        print(f"\n输入文件: {input_filename}")
        print(f"最佳匹配样本: {best_sample}")
        print(f"综合匹配评分: {best_score:.6f}")
        print("匹配结果: " + ("成功" if best_score < match_threshold else "失败"))