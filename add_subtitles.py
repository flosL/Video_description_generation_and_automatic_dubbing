import os
import textwrap
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def find_windows_chinese_font():
    """自动检测常见中文字体"""
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/simsun.ttc",  # 宋体
        "C:/Windows/Fonts/arialuni.ttf" # Arial Unicode
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def render_text_to_image(
    text, width, font_path=None, font_size=40,
    padding=8, line_spacing=6, bg=(0,0,0,0),
    fill=(255,255,255,255), stroke_fill=(0,0,0,255), stroke_width=2
):
    """用 Pillow 渲染文字为图像"""
    lines = text.splitlines()
    wrapper = textwrap.TextWrapper(width=40)
    if len(lines) == 1:
        lines = wrapper.wrap(text)

    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()

    tmp_img = Image.new("RGBA", (width, 10))
    draw = ImageDraw.Draw(tmp_img)
    line_heights = []
    max_w = 0
    
    # 使用textbbox替代废弃的textsize方法
    for line in lines:
        try:
            # 新版本PIL使用textbbox
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
        except AttributeError:
            # 兼容旧版本PIL
            w, h = draw.textsize(line, font=font, stroke_width=stroke_width)
        line_heights.append(h)
        if w > max_w:
            max_w = w

    total_h = sum(line_heights) + (len(lines)-1)*line_spacing + 2*padding
    img_w = int(width)
    img_h = int(total_h)
    img = Image.new("RGBA", (img_w, img_h), bg)
    draw = ImageDraw.Draw(img)
    y = padding
    
    for i, line in enumerate(lines):
        try:
            # 新版本PIL使用textbbox
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
            w = bbox[2] - bbox[0]
        except AttributeError:
            # 兼容旧版本PIL
            w, _ = draw.textsize(line, font=font, stroke_width=stroke_width)
        h = line_heights[i]
        x = (img_w - w) // 2
        draw.text((x, y), line, font=font, fill=fill, stroke_fill=stroke_fill, stroke_width=stroke_width)
        y += h + line_spacing
    return np.array(img)


def make_text_clip(text, start, duration, video_w, video_h, font_size=None):
    """生成单个字幕片段（优化版，防止字体被裁切 & 更好位置）"""
    font_path = find_windows_chinese_font()
    
    # 根据视频宽度动态计算字体大小，避免字幕越界
    if font_size is None:
        # 基础字体大小为视频宽度的3-5%，根据视频宽度自动调整
        base_font_size = int(video_w * 0.04)  # 4%的宽度作为基础字体大小
        # 限制最大和最小字体大小范围
        font_size = max(24, min(base_font_size, 60))  # 最小24px，最大60px
    try:
        # 尝试不同版本的moviepy参数格式
        try:
            # 新版本moviepy参数格式
            txt = TextClip(
                text,
                font=font_path,
                fontsize=font_size,
                color='white',
                stroke_color='black',
                stroke_width=3,
                method='caption',
                size=(int(video_w * 0.9), None)
            )
            # 设置时间属性（兼容不同moviepy版本）
            try:
                txt = txt.with_start(start).with_duration(duration)
            except AttributeError:
                txt = txt.set_start(start).set_duration(duration)
        except TypeError:
            # 旧版本moviepy参数格式
            txt = TextClip(
                text=text,
                font=font_path,
                font_size=font_size,
                color='white',
                stroke_color='black',
                stroke_width=3,
                method='caption',
                size=(int(video_w * 0.9), None)
            )
            # 设置时间属性（兼容不同moviepy版本）
            try:
                txt = txt.with_start(start).with_duration(duration)
            except AttributeError:
                txt = txt.set_start(start).set_duration(duration)
    except Exception as e:
            print(f"⚠️ TextClip失败({e})，回退到Pillow渲染")
            # 调整Pillow渲染时的字体大小，比TextClip稍小一些以确保更好的显示效果
            pillow_font_size = max(16, int(font_size * 0.9))  # 比TextClip小10%
            img_arr = render_text_to_image(
                text=text,
                width=int(video_w * 0.9),
                font_path=font_path,
                font_size=pillow_font_size
            )
            txt = ImageClip(img_arr)
            # 为ImageClip设置时间属性（兼容不同moviepy版本）
            try:
                # 尝试使用with_start和with_duration方法
                txt = txt.with_start(start).with_duration(duration)
            except AttributeError:
                # 某些moviepy版本可能使用不同的方法
                txt = txt.set_start(start).set_duration(duration)

    # 🎯 字幕位置调整：
    # 上移以确保字幕完全可见，防止被底部遮挡
    # y_pos 越小字幕越靠上
    y_pos = int(video_h * 0.75)  # 更靠上的位置，确保字幕完全可见

    # 为字幕设置位置（兼容不同moviepy版本）
    try:
        # 尝试使用with_position方法
        txt = txt.with_position(("center", y_pos))
    except AttributeError:
        # 某些moviepy版本可能使用set_position方法
        txt = txt.set_position(("center", y_pos))

    return txt




def add_timed_subtitles(video_path, subtitles, output_path="output_timed.mp4"):
    """
    给视频添加多条定时字幕。
    subtitles: list[dict] = [{'text': '内容', 'start': 秒, 'duration': 秒}, ...]
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"未找到视频: {video_path}")

    video = VideoFileClip(video_path)
    subtitle_clips = []

    for s in subtitles:
        clip = make_text_clip(
            text=s["text"],
            start=s["start"],
            duration=s["duration"],
            video_w=video.w,
            video_h=video.h,
        )
        subtitle_clips.append(clip)

    result = CompositeVideoClip([video, *subtitle_clips])
    result.write_videofile(output_path, fps=video.fps, codec="libx264", audio_codec="aac")
    print(f"✅ 已生成带时间字幕的视频: {output_path}")


if __name__ == "__main__":
    video_file = "input.mp4"
    
    subtitles = [
        {"text": "一群人在轮滑玩！", "start": 0, "duration": 2},
        {"text": "他们配合得真好。", "start": 2.5, "duration": 2},
        {"text": "这镜头太有动感了！", "start": 4.6, "duration": 1}
    ]
    add_timed_subtitles(video_file, subtitles)
