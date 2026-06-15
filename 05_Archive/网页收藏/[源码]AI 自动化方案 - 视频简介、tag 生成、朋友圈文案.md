---
url: https://articles.zsxq.com/id_doxgre8wzzfc.html
title: [源码]AI 自动化方案 - 视频简介、tag 生成、朋友圈文案
author: articles.zsxq.com
aliases: 
 - 
date: 2026-05-13 16:54:56
tags:

banner: "https://images.zsxq.com/FgeCV35RBepPB0Ub9Fq4icHAAyqA?e=2127196800&token=q6iZ0sQtf9U7s1qz0r4yMawNq3-u2w6lbnai6y2J:AoJZ9VINr-qkJk0CIgR84nxb2r8="
banner_icon: 🔖
---
# [源码]AI 自动化方案 - 视频简介、tag 生成、朋友圈文案

[来自： 雷哥 AI 解决方案](https://wx.zsxq.com/group/28882285418421)

![](https://images.zsxq.com/FgeCV35RBepPB0Ub9Fq4icHAAyqA?e=2127196800&token=q6iZ0sQtf9U7s1qz0r4yMawNq3-u2w6lbnai6y2J:AoJZ9VINr-qkJk0CIgR84nxb2r8=)

雷哥

2026 年 03 月 25 日 10:38

我是一个 AI 科技博主，日常产出的内容形式是短视频（抖音、微信视频号等）。视频录完剪好之后，发布时还需要手工写：

*   **抖音文案**：口语化、有观点、有互动引导
    

*   **抖音 Tag**：30 个精准标签
    

*   **微信朋友圈文案**：精炼版，2-3 句话
    

这一套内容每次都要重新写，耗时且重复。

### 痛点

视频拍完之后，我自己其实已经把观点说清楚了——视频本身就是最完整的内容素材。但发布前还需要把这些口语内容 "翻译" 成各平台需要的文案格式，这个工作完全是重复劳动。

### 解决方案

写一个命令行脚本 `video_create_info.py`，一行命令完成全流程：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
python3 video_create_info.py 视频.mp4


```

流程如下：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
MP4 → faster-whisper 语音转文字 → DeepSeek 生成三段内容 → 控制台输出


```

### 执行效果如下

![](https://article-images.zsxq.com/FpeMPH-NGRuHci9-kusoZWEyo08k)

  

### 对我的价值

*   **省时**：从 "剪完视频到发布" 这一步，原本需要 10-20 分钟手写文案，现在约 1-2 分钟自动完成
    

*   **一致性**：同一套 Prompt 保证风格稳定，不会因状态不好写出质量差的文案
    

*   **可扩展**：后续可以继续在字幕基础上加工，比如生成视频标题、YouTube 描述、Newsletter 摘要等
    

### 技术选型理由

<table><tbody><tr><th><p>组件</p></th><th><p>选型</p></th><th><p>理由</p></th></tr><tr><td><p>语音识别</p></td><td><p>faster-whisper (small)</p></td><td><p>中文效果好，本地运行，Apple Silicon 兼容</p></td></tr><tr><td><p>LLM</p></td><td><p>DeepSeek (deepseek-chat)</p></td><td><p>中文能力强，价格低，已有 API Key</p></td></tr><tr><td><p>运行方式</p></td><td><p>纯命令行 Python 脚本</p></td><td><p>简单直接，无需 UI，无依赖服务</p></td></tr></tbody></table>

* * *

# faster-whisper 技术笔记 (有兴趣可以读读)

## 1. Whisper vs faster-whisper

**Whisper** 是 OpenAI 开源的语音识别模型（2022 年），基于 PyTorch 实现，效果好但推理较慢。

**faster-whisper** 是第三方对 Whisper 的重新实现，模型权重相同（来自 OpenAI），只是换了更高效的推理引擎 CTranslate2。

<table><tbody><tr><th><p>维度</p></th><th><p>Whisper</p></th><th><p>faster-whisper</p></th></tr><tr><td><p>底层框架</p></td><td><p>PyTorch</p></td><td><p>CTranslate2（C++）</p></td></tr><tr><td><p>速度</p></td><td><p>1x</p></td><td><p><strong>约 4x</strong></p></td></tr><tr><td><p>内存占用</p></td><td><p>较高</p></td><td><p>低约 50%</p></td></tr><tr><td><p>模型权重</p></td><td><p>OpenAI 原版</p></td><td><p>相同，转换格式</p></td></tr><tr><td><p>VAD 静音过滤</p></td><td><p>无</p></td><td><p>内置</p></td></tr></tbody></table>

* * *

## 2. 为什么 CTranslate2 更高效

PyTorch 是训练框架，包含大量训练期开销（动态图、autograd 等），推理时完全用不上。

CTranslate2 专为**纯推理**设计，核心优化：

*   **算子融合**：把多个小计算合并成一个，减少内存读写（主要加速来源）
    

*   **INT8 量化**：FP32 → INT8，计算量和内存直接减半，精度损失极小
    

*   **内存复用**：严格管理中间 tensor 的生命周期，减少 GC 压力
    

*   **多线程 CPU**：用 OpenMP + BLAS 充分利用所有 CPU 核心
    

* * *

## 3. Apple Silicon 的优化方式

针对 M 系列芯片有多条路线，各有取舍：

<table><tbody><tr><th><p>方式</p></th><th><p>工具</p></th><th><p>利用硬件</p></th><th><p>说明</p></th></tr><tr><td><p>CPU + INT8 量化</p></td><td><p>faster-whisper</p></td><td><p>CPU（P 核 + E 核）</p></td><td><p>简单稳定，我们使用的方案</p></td></tr><tr><td><p>MLX</p></td><td><p>mlx-whisper</p></td><td><p>CPU + GPU（统一内存）</p></td><td><p>Apple 官方框架，速度再快 2-3x</p></td></tr><tr><td><p>CoreML / ANE</p></td><td><p>whisper.cpp / WhisperKit</p></td><td><p>Neural Engine</p></td><td><p>最快，配置复杂</p></td></tr><tr><td><p>MPS（Metal）</p></td><td><p>PyTorch MPS backend</p></td><td><p>GPU</p></td><td><p>效果一般</p></td></tr></tbody></table>

我们选 CPU+INT8：兼容性最好，零额外配置，在 M 系列上已足够快。  
追求极致速度可换 `mlx-whisper`。

* * *

## 4. 直接处理 MP4，无需转换

faster-whisper 安装时会附带 `av` 库（FFmpeg 的 Python 绑定），可以直接解码视频文件中的音频流，**不需要先转成 MP3/WAV 等中间格式**。

整个过程在内存中完成，磁盘上不产生任何临时文件：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
MP4 → av（内部调用 FFmpeg 解码）→ 提取音频流 → Whisper 模型


```

代码直接传 MP4 路径即可：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
model.transcribe("video.mp4", language="zh")



```

~

# 源码

通过网盘分享的文件：AI 自动化方案 - 视频简介、tag 生成、朋友圈文案源码. zip  
链接: [https://pan.baidu.com/s/1EOPM5GsvUhFBNnkwfY4p9A](https://pan.baidu.com/s/1EOPM5GsvUhFBNnkwfY4p9A) 提取码: jh3c  
-- 来自百度网盘超级会员 v5 的分享

我是一个 AI 科技博主，日常产出的内容形式是短视频（抖音、微信视频号等）。视频录完剪好之后，发布时还需要手工写：

*   **抖音文案**：口语化、有观点、有互动引导
    

*   **抖音 Tag**：30 个精准标签
    

*   **微信朋友圈文案**：精炼版，2-3 句话
    

这一套内容每次都要重新写，耗时且重复。

### 痛点

视频拍完之后，我自己其实已经把观点说清楚了——视频本身就是最完整的内容素材。但发布前还需要把这些口语内容 "翻译" 成各平台需要的文案格式，这个工作完全是重复劳动。

### 解决方案

写一个命令行脚本 `video_create_info.py`，一行命令完成全流程：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
python3 video_create_info.py 视频.mp4



```

流程如下：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
MP4 → faster-whisper 语音转文字 → DeepSeek 生成三段内容 → 控制台输出



```

### 执行效果如下

![](https://article-images.zsxq.com/FpeMPH-NGRuHci9-kusoZWEyo08k)

  

### 对我的价值

*   **省时**：从 "剪完视频到发布" 这一步，原本需要 10-20 分钟手写文案，现在约 1-2 分钟自动完成
    

*   **一致性**：同一套 Prompt 保证风格稳定，不会因状态不好写出质量差的文案
    

*   **可扩展**：后续可以继续在字幕基础上加工，比如生成视频标题、YouTube 描述、Newsletter 摘要等
    

### 技术选型理由

<table><tbody><tr><th><p>组件</p></th><th><p>选型</p></th><th><p>理由</p></th></tr><tr><td><p>语音识别</p></td><td><p>faster-whisper (small)</p></td><td><p>中文效果好，本地运行，Apple Silicon 兼容</p></td></tr><tr><td><p>LLM</p></td><td><p>DeepSeek (deepseek-chat)</p></td><td><p>中文能力强，价格低，已有 API Key</p></td></tr><tr><td><p>运行方式</p></td><td><p>纯命令行 Python 脚本</p></td><td><p>简单直接，无需 UI，无依赖服务</p></td></tr></tbody></table>

* * *

# faster-whisper 技术笔记 (有兴趣可以读读)

## 1. Whisper vs faster-whisper

**Whisper** 是 OpenAI 开源的语音识别模型（2022 年），基于 PyTorch 实现，效果好但推理较慢。

**faster-whisper** 是第三方对 Whisper 的重新实现，模型权重相同（来自 OpenAI），只是换了更高效的推理引擎 CTranslate2。

<table><tbody><tr><th><p>维度</p></th><th><p>Whisper</p></th><th><p>faster-whisper</p></th></tr><tr><td><p>底层框架</p></td><td><p>PyTorch</p></td><td><p>CTranslate2（C++）</p></td></tr><tr><td><p>速度</p></td><td><p>1x</p></td><td><p><strong>约 4x</strong></p></td></tr><tr><td><p>内存占用</p></td><td><p>较高</p></td><td><p>低约 50%</p></td></tr><tr><td><p>模型权重</p></td><td><p>OpenAI 原版</p></td><td><p>相同，转换格式</p></td></tr><tr><td><p>VAD 静音过滤</p></td><td><p>无</p></td><td><p>内置</p></td></tr></tbody></table>

* * *

## 2. 为什么 CTranslate2 更高效

PyTorch 是训练框架，包含大量训练期开销（动态图、autograd 等），推理时完全用不上。

CTranslate2 专为**纯推理**设计，核心优化：

*   **算子融合**：把多个小计算合并成一个，减少内存读写（主要加速来源）
    

*   **INT8 量化**：FP32 → INT8，计算量和内存直接减半，精度损失极小
    

*   **内存复用**：严格管理中间 tensor 的生命周期，减少 GC 压力
    

*   **多线程 CPU**：用 OpenMP + BLAS 充分利用所有 CPU 核心
    

* * *

## 3. Apple Silicon 的优化方式

针对 M 系列芯片有多条路线，各有取舍：

<table><tbody><tr><th><p>方式</p></th><th><p>工具</p></th><th><p>利用硬件</p></th><th><p>说明</p></th></tr><tr><td><p>CPU + INT8 量化</p></td><td><p>faster-whisper</p></td><td><p>CPU（P 核 + E 核）</p></td><td><p>简单稳定，我们使用的方案</p></td></tr><tr><td><p>MLX</p></td><td><p>mlx-whisper</p></td><td><p>CPU + GPU（统一内存）</p></td><td><p>Apple 官方框架，速度再快 2-3x</p></td></tr><tr><td><p>CoreML / ANE</p></td><td><p>whisper.cpp / WhisperKit</p></td><td><p>Neural Engine</p></td><td><p>最快，配置复杂</p></td></tr><tr><td><p>MPS（Metal）</p></td><td><p>PyTorch MPS backend</p></td><td><p>GPU</p></td><td><p>效果一般</p></td></tr></tbody></table>

我们选 CPU+INT8：兼容性最好，零额外配置，在 M 系列上已足够快。  
追求极致速度可换 `mlx-whisper`。

* * *

## 4. 直接处理 MP4，无需转换

faster-whisper 安装时会附带 `av` 库（FFmpeg 的 Python 绑定），可以直接解码视频文件中的音频流，**不需要先转成 MP3/WAV 等中间格式**。

整个过程在内存中完成，磁盘上不产生任何临时文件：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
MP4 → av（内部调用 FFmpeg 解码）→ 提取音频流 → Whisper 模型



```

代码直接传 MP4 路径即可：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
model.transcribe("video.mp4", language="zh")




```

~

# 源码

通过网盘分享的文件：AI 自动化方案 - 视频简介、tag 生成、朋友圈文案源码. zip  
链接: [https://pan.baidu.com/s/1EOPM5GsvUhFBNnkwfY4p9A](https://pan.baidu.com/s/1EOPM5GsvUhFBNnkwfY4p9A) 提取码: jh3c  
-- 来自百度网盘超级会员 v5 的分享

我是一个 AI 科技博主，日常产出的内容形式是短视频（抖音、微信视频号等）。视频录完剪好之后，发布时还需要手工写：

*   **抖音文案**：口语化、有观点、有互动引导
    

*   **抖音 Tag**：30 个精准标签
    

*   **微信朋友圈文案**：精炼版，2-3 句话
    

这一套内容每次都要重新写，耗时且重复。

### 痛点

视频拍完之后，我自己其实已经把观点说清楚了——视频本身就是最完整的内容素材。但发布前还需要把这些口语内容 "翻译" 成各平台需要的文案格式，这个工作完全是重复劳动。

### 解决方案

写一个命令行脚本 `video_create_info.py`，一行命令完成全流程：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
python3 video_create_info.py 视频.mp4


```

流程如下：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
MP4 → faster-whisper 语音转文字 → DeepSeek 生成三段内容 → 控制台输出


```

### 执行效果如下

![](https://article-images.zsxq.com/FpeMPH-NGRuHci9-kusoZWEyo08k)

  

### 对我的价值

*   **省时**：从 "剪完视频到发布" 这一步，原本需要 10-20 分钟手写文案，现在约 1-2 分钟自动完成
    

*   **一致性**：同一套 Prompt 保证风格稳定，不会因状态不好写出质量差的文案
    

*   **可扩展**：后续可以继续在字幕基础上加工，比如生成视频标题、YouTube 描述、Newsletter 摘要等
    

### 技术选型理由

<table><tbody><tr><th><p>组件</p></th><th><p>选型</p></th><th><p>理由</p></th></tr><tr><td><p>语音识别</p></td><td><p>faster-whisper (small)</p></td><td><p>中文效果好，本地运行，Apple Silicon 兼容</p></td></tr><tr><td><p>LLM</p></td><td><p>DeepSeek (deepseek-chat)</p></td><td><p>中文能力强，价格低，已有 API Key</p></td></tr><tr><td><p>运行方式</p></td><td><p>纯命令行 Python 脚本</p></td><td><p>简单直接，无需 UI，无依赖服务</p></td></tr></tbody></table>

* * *

# faster-whisper 技术笔记 (有兴趣可以读读)

## 1. Whisper vs faster-whisper

**Whisper** 是 OpenAI 开源的语音识别模型（2022 年），基于 PyTorch 实现，效果好但推理较慢。

**faster-whisper** 是第三方对 Whisper 的重新实现，模型权重相同（来自 OpenAI），只是换了更高效的推理引擎 CTranslate2。

<table><tbody><tr><th><p>维度</p></th><th><p>Whisper</p></th><th><p>faster-whisper</p></th></tr><tr><td><p>底层框架</p></td><td><p>PyTorch</p></td><td><p>CTranslate2（C++）</p></td></tr><tr><td><p>速度</p></td><td><p>1x</p></td><td><p><strong>约 4x</strong></p></td></tr><tr><td><p>内存占用</p></td><td><p>较高</p></td><td><p>低约 50%</p></td></tr><tr><td><p>模型权重</p></td><td><p>OpenAI 原版</p></td><td><p>相同，转换格式</p></td></tr><tr><td><p>VAD 静音过滤</p></td><td><p>无</p></td><td><p>内置</p></td></tr></tbody></table>

* * *

## 2. 为什么 CTranslate2 更高效

PyTorch 是训练框架，包含大量训练期开销（动态图、autograd 等），推理时完全用不上。

CTranslate2 专为**纯推理**设计，核心优化：

*   **算子融合**：把多个小计算合并成一个，减少内存读写（主要加速来源）
    

*   **INT8 量化**：FP32 → INT8，计算量和内存直接减半，精度损失极小
    

*   **内存复用**：严格管理中间 tensor 的生命周期，减少 GC 压力
    

*   **多线程 CPU**：用 OpenMP + BLAS 充分利用所有 CPU 核心
    

* * *

## 3. Apple Silicon 的优化方式

针对 M 系列芯片有多条路线，各有取舍：

<table><tbody><tr><th><p>方式</p></th><th><p>工具</p></th><th><p>利用硬件</p></th><th><p>说明</p></th></tr><tr><td><p>CPU + INT8 量化</p></td><td><p>faster-whisper</p></td><td><p>CPU（P 核 + E 核）</p></td><td><p>简单稳定，我们使用的方案</p></td></tr><tr><td><p>MLX</p></td><td><p>mlx-whisper</p></td><td><p>CPU + GPU（统一内存）</p></td><td><p>Apple 官方框架，速度再快 2-3x</p></td></tr><tr><td><p>CoreML / ANE</p></td><td><p>whisper.cpp / WhisperKit</p></td><td><p>Neural Engine</p></td><td><p>最快，配置复杂</p></td></tr><tr><td><p>MPS（Metal）</p></td><td><p>PyTorch MPS backend</p></td><td><p>GPU</p></td><td><p>效果一般</p></td></tr></tbody></table>

我们选 CPU+INT8：兼容性最好，零额外配置，在 M 系列上已足够快。  
追求极致速度可换 `mlx-whisper`。

* * *

## 4. 直接处理 MP4，无需转换

faster-whisper 安装时会附带 `av` 库（FFmpeg 的 Python 绑定），可以直接解码视频文件中的音频流，**不需要先转成 MP3/WAV 等中间格式**。

整个过程在内存中完成，磁盘上不产生任何临时文件：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
MP4 → av（内部调用 FFmpeg 解码）→ 提取音频流 → Whisper 模型


```

代码直接传 MP4 路径即可：

textjavascripttypescriptcsshtmlbashjsonmarkdownpythonjavaccpprubygorustphpsqlyaml Copy

```
model.transcribe("video.mp4", language="zh")



```

~

# 源码

通过网盘分享的文件：AI 自动化方案 - 视频简介、tag 生成、朋友圈文案源码. zip  
链接: [https://pan.baidu.com/s/1EOPM5GsvUhFBNnkwfY4p9A](https://pan.baidu.com/s/1EOPM5GsvUhFBNnkwfY4p9A) 提取码: jh3c  
-- 来自百度网盘超级会员 v5 的分享

![](https://articles.zsxq.com/assets_dweb/logo@2x.png)

知识星球

![](data:image/png;base64,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)

扫码加入星球

查看更多优质内容

https://wx.zsxq.com/mweb/views/joingroup/join_group.html?group_id=28882285418421