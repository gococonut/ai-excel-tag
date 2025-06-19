#!/bin/bash

# AI Excel 标注助手 - 快速启动脚本

echo "🚀 正在启动 AI Excel 标注助手..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "⚙️ 激活虚拟环境..."
source venv/bin/activate

# 检查依赖
echo "📋 检查并安装依赖..."
pip install -r requirements.txt

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "⚠️ 警告：未找到.env文件"
    echo "请创建.env文件并设置OPENAI_API_KEY"
    echo "或在侧边栏手动输入API密钥"
fi

# 启动应用
echo "🎉 启动应用..."
echo "应用将在 http://localhost:8501 运行"
echo "按 Ctrl+C 停止应用"

streamlit run app.py

echo "👋 应用已停止" 