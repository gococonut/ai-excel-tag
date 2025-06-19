# 🎯 AI Excel 智能标注

简单易用的AI数据标注工具，支持Excel/CSV文件智能标注。

## ✨ 主要功能

* 📁 **文件上传** - 支持CSV、Excel格式
* 🤖 **AI标注** - 支持OpenAI、Gemini等API
* 📊 **批量处理** - 高效处理大量数据
* 💾 **结果导出** - 多格式下载
* 🔐 **登录验证** - 安全访问控制

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置环境变量（可选）

```bash
export OPENAI_API_KEY="your_api_key"
export DEFAULT_MODEL="gpt-4o"
export LOGIN_USERNAME="admin"
export LOGIN_PASSWORD="your_password"
```

### 3. 启动应用

```bash
streamlit run app.py
```

访问 `http://localhost:8501` 开始使用！

## 📖 使用说明

### 基本流程

1. **登录** - 默认用户名/密码: `admin`/`admin123`
2. **配置API** - 输入OpenAI API密钥或Gemini API
3. **上传文件** - 拖拽或选择CSV/Excel文件
4. **选择列** - 选择需要标注的数据列
5. **设置标注** - 描述标注要求和选项
6. **开始标注** - AI自动批量处理
7. **下载结果** - 获取标注后的文件

### API 配置示例

```bash
# OpenAI API
export OPENAI_API_KEY="sk-xxx"

# Gemini API  
export OPENAI_API_KEY="your_gemini_key"
export OPENAI_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
export DEFAULT_MODEL="gemini-2.5-flash"
```

## 🔧 环境变量配置

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `OPENAI_API_KEY` | API密钥 | `sk-xxx` |
| `OPENAI_BASE_URL` | API地址（可选） | `https://api.openai.com/v1` |
| `DEFAULT_MODEL` | 默认模型 | `gpt-4o` , `gemini-2.5-flash` |
| `LOGIN_USERNAME` | 登录用户名 | `admin` |
| `LOGIN_PASSWORD` | 登录密码 | `your_password` |

## 💡 使用技巧

* **标注要求** - 描述要清晰具体，包含判断标准
* **批次大小** - 大文件建议使用小批次（5-10）
* **模型选择** - Gemini对中文友好，OpenAI稳定性好
* **结果验证** - 可先小批量测试再全量处理

## ⚠️ 注意事项

* API调用产生费用，请控制用量
* 大文件处理需要较长时间
* 建议定期保存标注结果

---

**简单高效的AI数据标注解决方案** 🎯 
