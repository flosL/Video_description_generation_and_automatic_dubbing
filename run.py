"""
整合运行脚本，直接跑
"""

import os
import json
import argparse
import torch
import numpy as np
import cv2
from pathlib import Path
from contextlib import contextmanager
import io
import sys

# 检查moviepy是否可用
try:
    from moviepy.editor import VideoFileClip
    HAVE_MOVIEPY = True
    # 导入add_subtitles.py中的字幕生成函数
    from add_subtitles import add_timed_subtitles
    # 导入add_audio.py中的音频添加函数
    from add_audio import add_audio_to_single_video
except ImportError:
    HAVE_MOVIEPY = False

# 导入predict_video.py中的必要函数和类
from predict_video import predict
from utils import configure_hardware, Config


def get_video_duration(video_path):
    """
    获取视频时长（秒）
    """
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        return duration
    except Exception as e:
        print(f"获取视频时长失败: {e}")
        return 0


@contextmanager
def capture_stdout():
    """
    捕获标准上下文输出
    """
    old_stdout = sys.stdout
    captured_output = io.StringIO()
    try:
        sys.stdout = captured_output
        yield captured_output
    finally:
        sys.stdout = old_stdout


def extract_description_from_output(output):
    """
    从输出中提取描述文本
    """
    for line in output.splitlines():
        if '\t:' in line:
            parts = line.split('\t:', 1)
            if len(parts) > 1:
                return parts[1].strip()
    return None

def main():
    # 模型路径
    DEFAULT_CONFIG_PATH = "configs\\caption-task_baseline_modal_clip4clip_msvd_config.json"
    DEFAULT_MODEL_PATH = "checkpoint\\clip4clip_msvd.pth"
    # 输入文件路径
    DEFAULT_VIDEO_PATH = "input/test.mp4"
    DEFAULT_AUDIO_PATH = "input/test.wav"
    DEFAULT_SUBTITLES_PATH = None  # 推理时请设置为None，避免默认加载现有字幕

    # 命令行参数解析
    parser = argparse.ArgumentParser(description='视频描述生成与字幕保存')
    parser.add_argument("-c", "--config", default=DEFAULT_CONFIG_PATH, 
                        help="配置文件路径")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL_PATH, 
                        help="模型权重文件路径")
    parser.add_argument("-v", "--video", default=DEFAULT_VIDEO_PATH, 
                        help="输入视频文件路径")
    parser.add_argument("--feat_type", nargs='+', default=["CLIP4CLIP-ViT-B-32"], 
                        choices=["CLIP", "I3D", "CLIP4CLIP-ViT-B-32"],
                        help="特征提取器类型")
    parser.add_argument("--ext_type", default="uni_12", 
                        help="视频帧提取方式")
    parser.add_argument("--cpu", action="store_true", default=True, 
                        help="使用CPU进行推理")
    parser.add_argument("--greedy", action="store_true", default=True, 
                        help="使用贪婪解码")
    parser.add_argument("-o", "--output_dir", default="output", 
                        help="输出目录")
    # 音频相关参数
    parser.add_argument("--audio", default=DEFAULT_AUDIO_PATH, 
                        help="要添加的音频文件路径")
    parser.add_argument("--audio_volume", type=float, default=0.8,
                        help="音频音量 (0.0-1.0)")
    parser.add_argument("--replace_audio", action="store_true", default=True, 
                        help="是否替换原始音频")
    #简单化              
    parser.add_argument("-ce", "--caption_existing", action="store_true", default=False, 
                        help="跳过推理，直接使用现有的字幕JSON文件")
    parser.add_argument("-cs", "--caption_source", type=str, default=DEFAULT_SUBTITLES_PATH,
                        help="指定字幕文件路径，使用此参数时自动启用 --caption_existing")
    
    args = parser.parse_args()
    
    # 配置硬件
    args = configure_hardware(args)
    
    # 加载配置
    cfg = Config(args.config)
    
    # 获取视频时长
    video_duration = get_video_duration(args.video)
    print(f"视频时长: {video_duration:.2f}秒")
    
    # 设置predict函数需要的属性
    args.features = None
    args.vis_attn = False  
    
    # 视频ID
    video_id = Path(args.video).stem
    
    subtitle_data = None
    
    if not HAVE_MOVIEPY:
        print("警告: moviepy未安装，无法生成带字幕的视频")
    
    # 设置字幕文件路径
    if args.caption_source:
        args.caption_existing = True
        json_output_path = args.caption_source
    else:
        # 默认字幕路径
        json_output_path = os.path.join(args.output_dir, f"{video_id}_subtitles.json")
    
    if args.caption_existing:
        # 如果指定了使用现有字幕，直接读取JSON文件
        if os.path.exists(json_output_path):
            try:
                with open(json_output_path, 'r', encoding='utf-8') as f:
                    subtitle_data = json.load(f)
                print(f"已加载现有字幕文件: {json_output_path}")
                print(f"字幕内容: {subtitle_data['text']}")
            except Exception as e:
                print(f"读取字幕文件失败: {e}")
        else:
            print(f"错误: 字幕文件不存在 - {json_output_path}")
    else:
        # 正常进行推理时使用上下文管理器捕获predict函数的输出
        with capture_stdout() as captured:
            predict(cfg.data, args)
        
        # 提取生成的描述
        description = extract_description_from_output(captured.getvalue())
        
        if description:
            print(f"\n生成的视频描述: {description}")
            
            # 构建字幕数据
            subtitle_data = {
                "text": description,
                "start": 0,
                "duration": video_duration
            }
            
            # 保存为JSON文件到output\
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(subtitle_data, f, ensure_ascii=False, indent=2)
            
            print(f"字幕数据已保存到: {json_output_path}")
        else:
            print("未能捕获到生成的描述")

    # 生成带字幕的视频
    if HAVE_MOVIEPY and subtitle_data:
        try:
            subtitles = [subtitle_data]  # 使用字幕数据
            output_video_path = os.path.join(args.output_dir, f"{video_id}_with_subtitles.mp4")
            add_timed_subtitles(args.video, subtitles, output_video_path)
            
            # 如果提供了音频文件，添加音频
            if args.audio:
                audio_output_path = os.path.join(args.output_dir, f"{video_id}_with_subtitles_audio.mp4")
                print(f"正在添加音频到视频...")
                success = add_audio_to_single_video(
                    video_path=output_video_path,
                    audio_path=args.audio,
                    output_path=audio_output_path,
                    audio_volume=args.audio_volume,
                    replace_original_audio=args.replace_audio
                )
                if success:
                    print(f"音频已成功添加到视频: {audio_output_path}")
        except Exception as e:
            print(f"生成带字幕视频或添加音频时出错: {e}")

    else:
        if not subtitle_data:
            print("未找到字幕数据，无法生成带字幕的视频")
        elif not HAVE_MOVIEPY:
            print("moviepy不可用，无法生成带字幕的视频")


if __name__ == "__main__":
    main()