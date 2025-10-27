from moviepy.editor import VideoFileClip, AudioFileClip
import os

def add_audio_to_single_video(video_path, audio_path, output_path, 
                             audio_volume=1.0, replace_original_audio=True):
    """
    为单个视频添加音轨
    
    参数:
    video_path (str): 输入视频文件的路径
    audio_path (str): 音频文件的路径
    output_path (str): 输出视频文件的路径
    audio_volume (float): 音频音量，1.0为原始音量
    replace_original_audio (bool): 是否替换原始音频，True则替换，False则混合
    """
    
    print(f"开始处理视频: {video_path}")
    print(f"使用音频: {audio_path}")
    
    try:
        # 检查文件是否存在
        if not os.path.exists(video_path):
            print(f"错误: 视频文件不存在 - {video_path}")
            return False
            
        if not os.path.exists(audio_path):
            print(f"错误: 音频文件不存在 - {audio_path}")
            return False
        
        # 加载视频文件
        print("正在加载视频...")
        video_clip = VideoFileClip(video_path)
        
        # 加载音频文件
        print("正在加载音频...")
        audio_clip = AudioFileClip(audio_path)
        
        # 调整音频音量
        if audio_volume != 1.0:
            print(f"调整音频音量到: {audio_volume}")
            audio_clip = audio_clip.volumex(audio_volume)
        
        # 确保音频长度与视频匹配
        video_duration = video_clip.duration
        audio_duration = audio_clip.duration
        
        print(f"视频时长: {video_duration:.2f}秒")
        print(f"音频时长: {audio_duration:.2f}秒")
        
        if audio_duration > video_duration:
            # 如果音频比视频长，截取音频并给出提醒
            print("⚠️  提醒: 音频比视频长，将截断音频以匹配视频长度")
            print("正在截取音频...")
            audio_clip = audio_clip.subclip(0, video_duration)
        elif audio_duration < video_duration:
            # 如果音频比视频短，直接使用原始音频长度（不循环）
            print("⚠️  提醒: 音频比视频短，音频结束后视频将无声")
        
        # 设置音频到视频
        if replace_original_audio:
            print("正在替换原始音频...")
            final_clip = video_clip.set_audio(audio_clip)
        else:
            print("正在混合音频...")
            original_audio = video_clip.audio
            if original_audio is not None:
                # 如果原始视频有音频，混合两个音频
                from moviepy.audio.AudioClip import CompositeAudioClip
                mixed_audio = CompositeAudioClip([original_audio, audio_clip])
                final_clip = video_clip.set_audio(mixed_audio)
            else:
                # 如果原始视频没有音频，直接设置新音频
                final_clip = video_clip.set_audio(audio_clip)
        
        # 导出视频
        print("正在导出视频...")
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        # 清理资源
        video_clip.close()
        audio_clip.close()
        final_clip.close()
        
        print(f"✓ 成功为视频添加音轨！")
        print(f"✓ 输出文件: {output_path}")
        
        # 验证输出文件
        if os.path.exists(output_path):
            output_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"✓ 文件大小: {output_size:.2f} MB")
            return True
        else:
            print("✗ 错误: 输出文件未生成")
            return False
        
    except Exception as e:
        print(f"✗ 处理过程中出现错误: {str(e)}")
        return False

# 使用示例
if __name__ == "__main__":
    # 设置文件路径
    video_file = "D:/Edge下载/Video_description_generation_and_automatic_dubbing-master/Video_description_generation_and_automatic_dubbing-master/myaudio.mp4"  # 替换为你的视频文件路径
    audio_file = "D:/Edge下载/Video_description_generation_and_automatic_dubbing-master/Video_description_generation_and_automatic_dubbing-master/fuck.mp3"  # 替换为你的音频文件路径
    output_file = "D:/Edge下载/Video_description_generation_and_automatic_dubbing-master/Video_description_generation_and_automatic_dubbing-master/testaudio.mp4"  # 输出文件路径
    
    # 添加音轨（替换原始音频）
    success = add_audio_to_single_video(
        video_path=video_file,
        audio_path=audio_file,
        output_path=output_file,
        audio_volume=0.8,  # 80%音量
        replace_original_audio=True  # 是否替换原始音频
    )
    
    if success:
        print("处理完成！")
    else:
        print("处理失败！")