# Video description generation and automatic dubbing
# 视频描述生成和自动配音项目
迁移原作者仓库说明：[VDG_README.md（Kamino666：视频描述生成部分）](VDG_README.md)

## 介绍
本项目基于 [Video-Captioning-Transformer](https://github.com/Kamino666/Video-Captioning-Transformer)项目魔改，在视频描述生成的基础上添加了TTS自动配音和添加字幕的功能。
# ！！！使用前需要完成的事情
- 配置腾讯云APIkey，在.env文件中配置TENCENT_SECRET_ID和TENCENT_SECRET_KEY。如下：
```
TENCENT_SECRET_ID = ""
TENCENT_SECRET_KEY = ""
```
- 下载已有的或自己训练模型，将模型文件放入checkpoint文件夹中。分别是
  - clip4clip_msrvtt.pth
  - clip4clip_msvd.pth
  默认使用msrvtt模型，若要使用msvd模型，需在run.py中指定model和config文件。
## 整合运行脚本run：
指定视频：
```
python run.py -v input/your_video.mp4
```
可自行在run.py 中修改其他参数，请见main函数下的参数解析。

## 使用predict：
参数如下：
```
python predict_video.py -c configs/caption-task_baseline_modal_clip4clip_config.json -m checkpoint/clip4clip_msrvtt.pth -v input/test.mp4 --feat_type CLIP4CLIP-ViT-B-32 --ext_type uni_12 --greedy --cpu
```

