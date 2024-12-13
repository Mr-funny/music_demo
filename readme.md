# 🎵 AI Music Generator

基于 Minimax API 和suno的音乐链接，remix音乐的的智能音乐生成工具
复制粘贴suno的播放详情链接和歌词，点击生成即可
生成歌曲自带语义停顿效果，不会一直都是阿卡贝拉连读的的状态

## ✨ 特性

- 📝 智能歌词节奏润色
- 🎹 AI 音乐生成
- 🎧 支持 Suno AI 音频处理

## 🚀 快速开始

### 前置要求

- Python 3.8+
- Minimax API 密钥
- Minimax Group ID

### 安装步骤

1. 克隆项目
bash
git clone https://github.com/your-username/ai-music-generator.git
cd ai-music-generator

2. 安装依赖
bash
pip install -r requirements.txt


3. 配置环境变量
bash
cp .env.example .env

编辑 .env 文件，填入你的 Minimax API key 和 Group ID
4. 运行项目

bash
python music.py


## 🎯 使用说明

1. 启动服务后访问 http://localhost:5000
2. 上传音频文件或提供 Suno URL
3. 输入歌词文本
4. 点击生成按钮开始处理

## 📚 API 文档

### 生成音乐 API
- 端点：`POST /api/generate`
- 请求体：
json
{
"suno_url": "https://suno.ai/song/xxx",
"lyrics": "你的歌词"
}

- 响应：
json
{
"success": true,
"audio_url": "/audio/generated_music_xxx.mp3",
"polished_lyrics": "润色后的歌词"
}


## 🛠️ 项目结构
music_DEMO/
├── music.py # 主程序文件
├── requirements.txt # 项目依赖
├── .env # 环境变量（不提交）
├── .env.example # 环境变量示例
├── static/ # 静态文件
├── downloads/ # 下载文件目录
└── logs/ # 日志目录


## ⚠️ 注意事项

- 需要有效的 Minimax API key
- 确保有足够的磁盘空间存储生成的音频文件
- 建议使用 Python 3.8 或更高版本

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📧 联系方式

你的名字 - [@你的推特](https://x.com/7cnKSdFv66650A7)

项目链接: [https://github.com/Mr-funny/music_demo]


一点代码都不会的产品经理的第一个小项目，很有成就感。
