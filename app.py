import streamlit as st
import pandas as pd
import io
import base64
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# 加载环境变量
load_dotenv()

# 定义结构化输出模型
class AnnotationResult(BaseModel):
    """标注结果的结构化模型"""
    annotations: List[str]
    
class SingleAnnotation(BaseModel):
    """单个标注的结构化模型"""
    text: str
    label: str
    confidence: Optional[float] = None

# 页面配置
st.set_page_config(
    page_title="AI Excel 智能标注工具",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 登录验证
def check_authentication():
    """检查用户登录状态"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 AI Excel 智能标注工具 - 登录")
        
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); width: 100px; height: 100px; border-radius: 25px; margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);">
                <span style="font-size: 3rem;">🎯</span>
            </div>
            <h2 style="color: #667eea; margin-bottom: 2rem;">请登录以继续使用</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            submitted = st.form_submit_button("登录", use_container_width=True)
            
            if submitted:
                # 从环境变量获取用户名和密码，如果没有则使用默认值
                valid_username = os.getenv("LOGIN_USERNAME", "admin")
                valid_password = os.getenv("LOGIN_PASSWORD", "admin123")
                
                if username == valid_username and password == valid_password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("登录成功！正在跳转...")
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
        
        # 只显示用户名提示
        if not os.getenv("LOGIN_USERNAME"):
            st.info("💡 默认用户名: admin")
        else:
            st.info("🔐 请使用配置的登录凭据")
        return False
    
    return True

# 自定义CSS样式
st.markdown("""
<style>
    /* 全局样式 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* 主体容器宽度限制和响应式设计 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* 响应式设计 */
    @media (max-width: 1400px) {
        .block-container {
            max-width: 1100px;
        }
    }
    
    @media (max-width: 1200px) {
        .block-container {
            max-width: 95%;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    
    @media (max-width: 768px) {
        .block-container {
            max-width: 100%;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
    }
    
    /* 主标题 */
    .main-header {
        font-size: 2.2rem;
        color: #667eea;
        text-align: center;
        margin-bottom: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* 章节标题 */
    .section-header {
        font-size: 1.4rem;
        color: #5b21b6;
        margin-top: 2rem;
        margin-bottom: 1.2rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e5e7eb;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* 移动端章节标题调整 */
    @media (max-width: 768px) {
        .section-header {
            font-size: 1.2rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
    }
    
    /* 信息框 */
    .info-box {
        background-color: #f8fafc;
        padding: 1.2rem;
        border-radius: 0.75rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin: 1.2rem 0;
    }
    
    /* 移动端信息框调整 */
    @media (max-width: 768px) {
        .info-box {
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .info-box h2 {
            font-size: 1.2rem !important;
        }
        
        .info-box p {
            font-size: 0.9rem !important;
        }
    }
    
    /* 成功框 */
    .success-box {
        background-color: #f0fdf4;
        padding: 1.2rem;
        border-radius: 0.75rem;
        border: 1px solid #dcfce7;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin: 1.2rem 0;
    }
    
    /* 警告框 */
    .warning-box {
        background-color: #fffbeb;
        padding: 1.2rem;
        border-radius: 0.75rem;
        border: 1px solid #fef3c7;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin: 1.2rem 0;
    }
    
    /* 卡片样式 */
    .stCard {
        border: none !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        border-radius: 0.75rem !important;
    }
    
    /* 按钮美化 */
    button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 0.5rem !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        color: white !important;
    }
    
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.25) !important;
        transform: translateY(-1px) !important;
    }
    
    /* 普通按钮 */
    button[kind="secondary"] {
        border-radius: 0.5rem !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s ease !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #f8fafc !important;
        color: #475569 !important;
    }
    
    button[kind="secondary"]:hover {
        background-color: #f1f5f9 !important;
        border-color: #cbd5e1 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* 表格优化 */
    [data-testid="stDataFrame"] {
        border-radius: 0.75rem !important;
        overflow: hidden !important;
        font-size: 0.9rem !important;
    }
    
    /* 表格响应式 */
    @media (max-width: 768px) {
        [data-testid="stDataFrame"] {
            font-size: 0.8rem !important;
        }
        
        [data-testid="stDataFrame"] th,
        [data-testid="stDataFrame"] td {
            padding: 0.3rem !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            max-width: 150px !important;
        }
    }
    
    /* 表格行选中样式 */
    [data-testid="stDataFrame"] tbody tr:hover {
        background-color: #eff6ff !important;
    }
    
    [data-testid="stDataFrame"] tbody tr:nth-child(even):hover {
        background-color: #dbeafe !important;
    }
    
    /* 输入框美化 */
    [data-testid="stTextInput"] > div > div, 
    [data-testid="stTextArea"] > div > div,
    [data-testid="stMultiSelect"] > div > div:first-child,
    [data-testid="stSelectbox"] > div > div {
        border-radius: 0.5rem !important;
        border-color: #d1d5db !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stTextInput"] > div > div:focus-within,
    [data-testid="stTextArea"] > div > div:focus-within,
    [data-testid="stMultiSelect"] > div > div:first-child:focus-within,
    [data-testid="stSelectbox"] > div > div:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* 侧边栏美化 */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        padding-top: 1.5rem !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4 {
        margin-top: 1.5rem !important;
        color: #334155 !important;
        font-size: 1.1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }
    
    /* 简化展开器样式 */
    [data-testid="stExpander"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 0.5rem !important;
        margin: 0.5rem 0 !important;
    }
    
    /* 进度条优化 */
    [data-testid="stProgress"] > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* 指标显示优化 */
    [data-testid="stMetricValue"] {
        font-weight: 600 !important;
        color: #334155 !important;
    }
    
    /* 帮助文本美化 */
    .stMarkdown p {
        line-height: 1.6 !important;
    }
    
    /* 文件上传器样式优化 */
    [data-testid="stFileUploader"] {
        border: 2px dashed #d1d5db !important;
        border-radius: 0.75rem !important;
        padding: 2rem !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #667eea !important;
        background-color: #f8fafc !important;
    }
    
    /* 移动端文件上传器优化 */
    @media (max-width: 768px) {
        [data-testid="stFileUploader"] {
            padding: 1rem !important;
        }
    }
    
    /* 移除多余的分隔线 */
    .stApp > div:first-child {
        border: none !important;
    }
    
    /* 选择框样式优化 */
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-radius: 0.25rem !important;
    }
</style>
""", unsafe_allow_html=True)

class AIAnnotator:
    """AI标注器类"""
    
    def __init__(self, api_key: str, base_url: str = None):
        """初始化AI标注器"""
        if not api_key:
            raise ValueError("需要提供OpenAI API密钥")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
    
    def test_connection(self) -> tuple[bool, str, list]:
        """测试API连接并获取可用模型列表"""
        try:
            # 测试连接并获取模型列表
            models_response = self.client.models.list()
            models = []
            
            # 过滤出常用的聊天模型
            chat_models = []
            for model in models_response.data:
                model_id = model.id
                # 筛选常用的聊天模型
                if any(keyword in model_id.lower() for keyword in [
                    'gpt-3.5', 'gpt-4', 'gpt-35', 'claude', 'chat', 'turbo', 'gemini', 'flash'
                ]):
                    chat_models.append(model_id)
                models.append(model_id)
            
            # 如果没有找到聊天模型，使用所有模型
            if not chat_models:
                chat_models = models
            
            # 排序模型列表
            chat_models.sort()
            
            return True, f"连接成功！找到 {len(chat_models)} 个可用的聊天模型", chat_models
            
        except Exception as e:
            return False, f"连接失败: {str(e)}", []
    
    def test_annotation(self, model: str = "gpt-3.5-turbo") -> tuple[bool, str, dict]:
        """测试标注功能"""
        try:
            # 多样化的测试数据
            test_data = [
                "这个产品很棒，我很满意！拍照效果超出预期。",
                "价格太贵了，性价比不高，不推荐购买。", 
                "产品质量还行，有优点也有缺点，总体来说一般般。"
            ]
            test_requirements = "判断用户对产品的情感态度"
            test_options = ["正面", "负面", "中性"]
            
            # 调用标注，使用更大的 max_tokens
            result = self.annotate_batch(
                test_data, 
                test_requirements, 
                test_options, 
                model=model,
                temperature=0.1,
                max_tokens=1000
            )
            
            if result and len(result) > 0 and result[0] != "标注失败":
                test_info = {
                    "test_data": test_data,
                    "requirements": test_requirements,
                    "options": test_options,
                    "results": result
                }
                return True, "测试成功！", test_info
            else:
                return False, "测试失败：未获得有效标注结果", {}
                
        except Exception as e:
            return False, f"测试失败: {str(e)}", {}
    
    def annotate_batch(self, data: List[str], annotation_requirements: str, 
                      annotation_options: List[str], model: str = "gpt-3.5-turbo",
                      temperature: float = 0.1, max_tokens: int = 2000) -> List[str]:
        """批量标注数据 - 优先使用结构化输出"""
        try:
            # 构建提示词
            prompt = f"""
你是一个专业的数据标注助手。请根据以下要求对数据进行标注：

标注要求：{annotation_requirements}

可选标注选项：{', '.join(annotation_options)}

请对以下数据进行标注，为每个数据项选择最合适的标注选项。
如果数据不符合任何选项，请选择最接近的选项或标注为"其他"。

数据：
{json.dumps(data, ensure_ascii=False, indent=2)}

重要要求：
1. 返回的标注数量必须与输入数据数量完全一致
2. 每个标注都必须是提供的选项之一
"""

            # 第一步：尝试结构化输出
            try:
                response = self.client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的数据标注助手，请严格按照要求进行标注。"},
                        {"role": "user", "content": prompt}
                    ],
                    response_format=AnnotationResult,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                if response and response.choices and response.choices[0].message.parsed:
                    parsed_result = response.choices[0].message.parsed
                    annotations = parsed_result.annotations
                    
                    # 验证标注数量
                    if len(annotations) == len(data):
                        return annotations
                    else:
                        st.warning(f"结构化输出标注数量不匹配，回退到普通模式")
                        
            except Exception as e:
                st.warning(f"结构化输出失败: {str(e)}，回退到普通模式")
            
            # 第二步：回退到传统JSON输出
            return self.annotate_batch_fallback(data, annotation_requirements, annotation_options, model, temperature, max_tokens)
                
        except Exception as e:
            st.error(f"AI标注出错：{str(e)}")
            return ["标注失败"] * len(data)
    
    def annotate_batch_fallback(self, data: List[str], annotation_requirements: str, 
                              annotation_options: List[str], model: str = "gpt-3.5-turbo",
                              temperature: float = 0.1, max_tokens: int = 2000) -> List[str]:
        """传统JSON输出模式（回退方案）"""
        try:
            # 构建提示词
            prompt = f"""
你是一个专业的数据标注助手。请根据以下要求对数据进行标注：

标注要求：{annotation_requirements}

可选标注选项：{', '.join(annotation_options)}

请对以下数据进行标注，为每个数据项选择最合适的标注选项。
如果数据不符合任何选项，请选择最接近的选项或标注为"其他"。

数据：
{json.dumps(data, ensure_ascii=False, indent=2)}

请直接返回JSON格式结果，不要使用代码块包裹：
{{"annotations": ["标注1", "标注2", "标注3", ...]}}

重要要求：
1. 只返回纯JSON，不要添加```或其他格式
2. 返回的标注数量必须与输入数据数量完全一致
3. 每个标注都必须是提供的选项之一
"""

            # 准备请求参数（包含安全设置）
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的数据标注助手，请严格按照要求进行标注。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            response = self.client.chat.completions.create(**request_params)
            
            # 检查响应是否为空
            if not response or not response.choices:
                st.error("AI返回空响应，请检查API配置")
                return ["标注失败"] * len(data)
            
            # 解析响应
            choice = response.choices[0]
            
            # 检查消息是否存在
            if not choice.message or not hasattr(choice.message, 'content'):
                st.error("AI响应格式错误，未包含有效内容")
                return ["标注失败"] * len(data)
            
            result_text = choice.message.content
            
            # 检查响应是否被截断
            if choice.finish_reason == 'length':
                st.error(f"AI响应被截断，请增加最大输出长度。当前设置: {max_tokens}")
                return ["标注失败"] * len(data)
            
            if result_text is None or result_text.strip() == "":
                st.error("AI返回空响应内容")
                return ["标注失败"] * len(data)
            
            result_text = result_text.strip()
            
            # 清理响应文本，处理各种可能的格式
            def clean_json_response(text):
                text = text.strip()
                
                # 处理markdown代码块
                if text.startswith('```'):
                    lines = text.split('\n')
                    if len(lines) >= 3:
                        # 去掉第一行和最后一行
                        text = '\n'.join(lines[1:-1]).strip()
                
                # 处理可能的额外文字说明
                if '{' in text and '}' in text:
                    # 提取JSON部分
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    text = text[start:end]
                
                return text.strip()
            
            result_text = clean_json_response(result_text)
            
            # 尝试解析JSON
            try:
                result_json = json.loads(result_text)
                annotations = result_json.get("annotations", [])
                
                # 验证标注数量
                if len(annotations) != len(data):
                    st.error(f"标注数量不匹配：期望 {len(data)}，实际 {len(annotations)}")
                    return ["标注失败"] * len(data)
                
                return annotations
            except json.JSONDecodeError as e:
                st.error(f"AI响应格式错误，无法解析JSON。")
                st.error(f"错误详情: {str(e)}")
                st.error(f"处理后的响应: {result_text[:200]}...")
                return ["标注失败"] * len(data)
                
        except Exception as e:
            st.error(f"AI标注出错：{str(e)}")
            return ["标注失败"] * len(data)

def load_file(uploaded_file) -> Optional[pd.DataFrame]:
    """加载上传的文件"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    return df
                except UnicodeDecodeError:
                    continue
            st.error("无法读取CSV文件，请检查文件编码")
            return None
            
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file, engine='openpyxl' if file_extension == 'xlsx' else 'xlrd')
            return df
        else:
            st.error("不支持的文件格式，请上传CSV或Excel文件")
            return None
            
    except Exception as e:
        st.error(f"文件加载失败：{str(e)}")
        return None

def get_download_link(df: pd.DataFrame, filename: str) -> str:
    """生成下载链接"""
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 下载标注结果</a>'
    return href

def main():
    """主函数"""
    # 检查登录状态
    if not check_authentication():
        return
    
    # 标题和Logo
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2.5rem;">
        <div style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem 3rem; border-radius: 20px; margin-bottom: 1.5rem;
                    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);">
            <div style="display: flex; align-items: center; justify-content: center; gap: 1rem;">
                <div style="background: rgba(255, 255, 255, 0.2); width: 60px; height: 60px; 
                            border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 2rem;">🎯</span>
                </div>
                <div>
                    <div style="font-size: 2.2rem; font-weight: 700; color: white; margin: 0;">
                        AI Excel 智能标注
                    </div>
                    <div style="font-size: 0.9rem; color: rgba(255, 255, 255, 0.8); margin: 0.3rem 0 0 0;">
                        INTELLIGENT ANNOTATION TOOL
                    </div>
                </div>
            </div>
        </div>
        <div style="font-size: 1.1rem; color: #667eea; font-weight: 600;">
            🚀 让AI为您的Excel数据快速添加智能标注，提升工作效率
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 欢迎信息 - 如果没有上传过文件就显示
    if 'df' not in st.session_state or st.session_state.df is None:
        st.markdown("""
        <div class="info-box" style="text-align: center; padding: 2rem;">
            <h2 style="color: #667eea; font-weight: 600; font-size: 1.5rem; margin-bottom: 1rem;">👋 欢迎使用 AI Excel 智能标注工具</h2>
            <p style="color: #334155; margin-bottom: 1rem;">
                一个强大的AI驱动工具，可以帮助您自动标注Excel或CSV数据，节省大量手动工作时间。
            </p>
            <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; margin: 1.5rem 0;">
                <div style="background-color: #f8fafc; padding: 1rem; border-radius: 0.5rem; width: 180px; min-width: 150px; max-width: 200px; text-align: center; flex: 1;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔑</div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">第一步</div>
                    <p style="font-size: 0.9rem; color: #64748b;">在侧边栏配置API并测试连接</p>
                </div>
                <div style="background-color: #f8fafc; padding: 1rem; border-radius: 0.5rem; width: 180px; min-width: 150px; max-width: 200px; text-align: center; flex: 1;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📁</div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">第二步</div>
                    <p style="font-size: 0.9rem; color: #64748b;">上传您的Excel或CSV文件</p>
                </div>
                <div style="background-color: #f8fafc; padding: 1rem; border-radius: 0.5rem; width: 180px; min-width: 150px; max-width: 200px; text-align: center; flex: 1;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎯</div>
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">第三步</div>
                    <p style="font-size: 0.9rem; color: #64748b;">配置标注要求并开始处理</p>
                </div>
            </div>
            <p style="font-size: 0.9rem; color: #64748b; font-style: italic;">
                开始使用前，请确保您已在侧边栏中设置了API密钥
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # 侧边栏配置
    with st.sidebar:
        

        
        st.markdown("### ⚙️ 配置设置")
        
        # API配置
        st.markdown("#### 🔑 API设置")
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="请输入您的OpenAI API密钥"
        )
        
        base_url = st.text_input(
            "API Base URL (可选)",
            value=os.getenv("OPENAI_BASE_URL", ""),
            help="如果使用代理或其他服务，请输入基础URL"
        )
        
        # API连接测试
        if st.button("🔗 测试API连接", use_container_width=True):
            if not api_key:
                st.error("请先输入API密钥")
            else:
                with st.spinner("正在测试连接..."):
                    try:
                        annotator = AIAnnotator(api_key, base_url if base_url else None)
                        success, message, models = annotator.test_connection()
                        
                        if success:
                            st.success(message)
                            st.session_state.available_models = models
                            st.session_state.api_connected = True
                        else:
                            st.error(message)
                            st.session_state.api_connected = False
                    except Exception as e:
                        st.error(f"连接测试失败: {str(e)}")
                        st.session_state.api_connected = False
        
        # 模型选择
        st.markdown("#### 🤖 模型设置")
        
        # 初始化可用模型列表
        if 'available_models' not in st.session_state:
            st.session_state.available_models = [
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k", 
                "gpt-4",
                "gpt-4-turbo-preview",
                "gpt-4o",
                "gpt-4o-mini"
            ]
        
        # 从环境变量获取默认模型
        default_model = os.getenv("DEFAULT_MODEL", "")
        default_index = None
        
        # 如果环境变量中的模型不在列表中，添加到列表顶部
        if default_model and default_model not in st.session_state.available_models:
            st.session_state.available_models.insert(0, default_model)
            default_index = 0
        elif default_model and default_model in st.session_state.available_models:
            default_index = st.session_state.available_models.index(default_model)
        
        selected_model = st.selectbox(
            "选择AI模型",
            options=st.session_state.available_models,
            index=default_index,
            placeholder="请选择模型",
            help="选择用于标注的AI模型，不同模型效果和费用不同。可通过环境变量 DEFAULT_MODEL 设置默认值（支持任何模型名称，如 gemini-2.5-flash）"
        )
        
        # 显示连接状态
        if 'api_connected' in st.session_state:
            if st.session_state.api_connected:
                st.success("✅ API连接正常")
                
                # 显示API类型
                if base_url and "generativelanguage.googleapis.com" in base_url:
                    st.info("🔥 Gemini API - 推荐选择")
                elif base_url and base_url != "":
                    st.info(f"🔗 自定义API: {base_url.split('//')[1].split('/')[0] if '//' in base_url else base_url}")
                else:
                    st.info("🤖 OpenAI官方API")
                
                st.markdown('<small style="color: #6b7280;">✨ 所有API都支持结构化输出和安全设置优化</small>', unsafe_allow_html=True)
                
                # 测试标注功能
                if st.button("🧪 测试标注功能", use_container_width=True):
                    if not selected_model:
                        st.error("请先选择AI模型")
                    else:
                        with st.spinner("正在测试标注..."):
                            try:
                                annotator = AIAnnotator(api_key, base_url if base_url else None)
                                test_success, test_message, test_info = annotator.test_annotation(selected_model)
                                
                                if test_success:
                                    st.success(test_message)
                                    
                                    # 显示测试详情
                                    with st.expander("📋 查看测试详情", expanded=True):
                                        st.markdown("**标注要求：**")
                                        st.write(test_info["requirements"])
                                        
                                        st.markdown("**可选标注选项：**")
                                        st.write(", ".join(test_info["options"]))
                                        
                                        st.markdown("**测试数据和结果：**")
                                        for i, (data, result) in enumerate(zip(test_info["test_data"], test_info["results"])):
                                            col1, col2 = st.columns([3, 1])
                                            with col1:
                                                st.write(f"📝 **数据 {i+1}：** {data}")
                                            with col2:
                                                # 根据标注结果设置不同颜色
                                                if result == "正面":
                                                    st.success(f"✅ {result}")
                                                elif result == "负面":
                                                    st.error(f"❌ {result}")
                                                else:
                                                    st.info(f"🔵 {result}")
                                else:
                                    st.error(test_message)
                            except Exception as e:
                                st.error(f"标注测试失败: {str(e)}")
            else:
                st.warning("⚠️ API连接异常，请检查配置")
        else:
            st.info("💡 建议先测试API连接")
        
        # 批次设置
        st.markdown("#### 📊 处理设置")
        batch_size = st.slider(
            "批次大小",
            min_value=5,
            max_value=20,
            value=10,
            help="每次处理的数据条数。如果每项文本量很大，建议选择较小的批次大小（5-8）以提高稳定性"
        )
        
        if batch_size > 15:
            st.warning("⚠️ 批次较大时，如果单条文本内容很长，可能会导致处理不稳定，建议适当减小批次大小")
        
        # 高级设置
        st.markdown("#### ⚙️ 高级设置")
        with st.expander("展开高级选项", expanded=False):
            st.info("💡 仅适用于有经验的用户")
            
            temperature = st.slider(
                "创造性程度",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.1,
                help="0.0 = 更确定性，1.0 = 更创造性",
                key="advanced_temperature"
            )
            
            max_tokens_value = st.selectbox(
                "最大输出长度",
                options=["不限制", "2000", "4000", "8000"],
                index=0,
                help="限制AI响应的最大长度，选择'不限制'获得最佳效果",
                key="advanced_max_tokens"
            )
        
        # 用户信息和退出登录 - 放在底部
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown(f"""
        <div style="background: #f8fafc; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border: 1px solid #e2e8f0;">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="background: #667eea; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-weight: 600; font-size: 1rem;">
                        {st.session_state.username[0].upper() if st.session_state.username else 'U'}
                    </span>
                </div>
                <div>
                    <div style="color: #64748b; font-size: 0.8rem; margin: 0;">欢迎回来</div>
                    <div style="color: #1e293b; font-weight: 600; font-size: 0.95rem; margin: 0;">
                        {st.session_state.username}
                    </div>
                </div>
                <div style="margin-left: auto;">
                    <div style="width: 10px; height: 10px; background: #10b981; border-radius: 50%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 退出登录", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            if 'username' in st.session_state:
                del st.session_state.username
            st.rerun()
        
        # 版本信息
        st.markdown("""
        <div style="text-align: center; font-size: 0.8rem; color: #94a3b8; padding: 1rem 0;">
            <div style="margin-bottom: 0.5rem;">
                <span style="color: #667eea; font-weight: 600;">AI Excel 智能标注</span> v1.0
            </div>
            <div style="font-size: 0.7rem;">
                🎯 Excel数据智能标注解决方案
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 初始化会话状态
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'annotated_df' not in st.session_state:
        st.session_state.annotated_df = None
    if 'selected_columns' not in st.session_state:
        st.session_state.selected_columns = []
    
    # 文件上传区域
    st.markdown('<div class="section-header">📁 文件上传</div>', unsafe_allow_html=True)
    
    # 简化文件上传区域
    uploaded_file = st.file_uploader(
        "选择CSV或Excel文件",
        type=['csv', 'xlsx', 'xls'],
        help="支持CSV、XLSX、XLS格式"
    )
    
    if not uploaded_file:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; color: #64748b; font-size: 0.9rem;">
            👆 拖放文件到此处或点击选择文件
        </div>
        """, unsafe_allow_html=True)
    
    if uploaded_file is not None:
        # 加载文件
        with st.spinner("正在加载文件..."):
            df = load_file(uploaded_file)
        
        if df is not None:
            st.session_state.df = df
            
            # 文件信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总行数", len(df))
            with col2:
                st.metric("总列数", len(df.columns))
            with col3:
                st.metric("文件大小", f"{uploaded_file.size / 1024:.1f} KB")
    
    # 数据预览和列选择
    if st.session_state.df is not None:
        df = st.session_state.df
        
        st.markdown('<div class="section-header">👀 数据预览</div>', unsafe_allow_html=True)
        
        # 预览选项
        preview_rows = st.selectbox("预览行数", [10, 20, 50, 100], index=1)
        
        # 显示数据
        st.dataframe(df.head(preview_rows), use_container_width=True)
        
        # 列选择
        st.markdown('<div class="section-header">📋 选择标注列</div>', unsafe_allow_html=True)
        
        selected_columns = st.multiselect(
            "选择需要进行AI标注的列",
            options=df.columns.tolist(),
            default=st.session_state.selected_columns,
            help="可以选择多列进行标注"
        )
        st.session_state.selected_columns = selected_columns
        
        if selected_columns:
            # 显示选中列的预览
            st.markdown("**选中列预览：**")
            preview_df = df[selected_columns].head(10)
            st.dataframe(preview_df, use_container_width=True)
            
            # 标注配置
            st.markdown('<div class="section-header">🎯 标注配置</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**标注要求：**")
                annotation_requirements = st.text_area(
                    "请描述标注要求",
                    height=150,
                    placeholder="例如：根据商品描述判断商品类别...",
                    help="详细描述AI应该如何进行标注"
                )
            
            with col2:
                st.markdown("**标注选项：**")
                annotation_options_text = st.text_area(
                    "输入标注选项（每行一个）",
                    height=150,
                    placeholder="选项1\n选项2\n选项3\n其他",
                    help="AI将从这些选项中选择标注结果"
                )
                
                # 解析标注选项
                annotation_options = [opt.strip() for opt in annotation_options_text.split('\n') if opt.strip()]
            
            # 标注列设置
            st.markdown("**结果存储：**")
            annotation_column_name = st.text_input(
                "标注结果列名",
                value="AI_标注",
                help="标注结果将存储在此列中"
            )
            
            # 开始标注
            st.markdown('<div style="margin: 2rem 0;">', unsafe_allow_html=True)
            if st.button("🚀 开始AI标注", type="primary", use_container_width=True):
                if not api_key:
                    st.error("请在侧边栏输入API密钥")
                elif not selected_model:
                    st.error("请在侧边栏选择AI模型")
                elif not annotation_requirements:
                    st.error("请输入标注要求")
                elif not annotation_options:
                    st.error("请输入标注选项")
                else:
                    try:
                        # 初始化AI标注器
                        annotator = AIAnnotator(api_key, base_url if base_url else None)
                        
                        # 准备数据
                        data_to_annotate = []
                        for _, row in df.iterrows():
                            row_data = " | ".join([str(row[col]) for col in selected_columns])
                            data_to_annotate.append(row_data)
                        
                        # 显示进度
                        total_batches = (len(data_to_annotate) + batch_size - 1) // batch_size
                        
                        # 创建进度展示区域
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        all_annotations = []
                        
                        # 批量处理
                        for i in range(0, len(data_to_annotate), batch_size):
                            batch_data = data_to_annotate[i:i + batch_size]
                            batch_num = i // batch_size + 1
                            
                            status_text.text(f"正在处理第 {batch_num}/{total_batches} 批数据...")
                            
                            # 获取高级设置参数
                            temperature = st.session_state.get('advanced_temperature', 0.1)
                            max_tokens_str = st.session_state.get('advanced_max_tokens', '不限制')
                            max_tokens_value = int(max_tokens_str) if max_tokens_str != '不限制' else 8000
                            
                            # 调用AI标注
                            batch_annotations = annotator.annotate_batch(
                                batch_data,
                                annotation_requirements,
                                annotation_options,
                                model=selected_model,
                                temperature=temperature,
                                max_tokens=max_tokens_value
                            )
                            
                            all_annotations.extend(batch_annotations)
                            
                            # 更新进度
                            progress = min(1.0, len(all_annotations) / len(data_to_annotate))
                            progress_bar.progress(progress)
                        
                        # 创建标注后的数据框
                        annotated_df = df.copy()
                        annotated_df[annotation_column_name] = all_annotations
                        st.session_state.annotated_df = annotated_df
                        
                        status_text.text("✅ 标注完成！")
                        st.success(f"成功标注 {len(all_annotations)} 条数据")
                        
                    except Exception as e:
                        st.error(f"标注过程中出现错误：{str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 结果展示和下载
    if st.session_state.annotated_df is not None:
        st.markdown('<div class="section-header">📊 标注结果</div>', unsafe_allow_html=True)
        
        annotated_df = st.session_state.annotated_df
        
        # 结果统计
        annotation_col = [col for col in annotated_df.columns if "标注" in col or "AI_" in col]
        if annotation_col:
            annotation_col = annotation_col[0]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**标注结果预览：**")
                st.dataframe(annotated_df, use_container_width=True)
            
            with col2:
                st.markdown("**标注分布：**")
                annotation_counts = annotated_df[annotation_col].value_counts()
                
                # 饼图
                fig = px.pie(
                    values=annotation_counts.values,
                    names=annotation_counts.index,
                    title="标注分布",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_layout(
                    margin=dict(l=20, r=20, t=40, b=20),
                    legend=dict(orientation="h", y=-0.2)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 统计表
                st.dataframe(annotation_counts.to_frame("数量"), use_container_width=True)
        
        # 下载按钮
        st.markdown('<div class="section-header">📥 下载结果</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # CSV下载
            csv = annotated_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📄 下载CSV文件",
                data=csv,
                file_name=f"标注结果_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Excel下载
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                annotated_df.to_excel(writer, index=False, sheet_name='标注结果')
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📊 下载Excel文件",
                data=excel_data,
                file_name=f"标注结果_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col3:
            # JSON下载
            json_data = annotated_df.to_json(orient='records', force_ascii=False, indent=2)
            st.download_button(
                label="🔧 下载JSON文件",
                data=json_data,
                file_name=f"标注结果_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    # 帮助信息
    st.markdown('<div class="section-header">📖 使用帮助</div>', unsafe_allow_html=True)
    with st.expander("查看使用说明"):
        st.markdown("""
        ### 🚀 快速开始
        
        1. **配置API**：在侧边栏输入您的API密钥和Base URL
        2. **测试连接**：点击"测试API连接"验证配置并获取可用模型
        3. **选择模型**：从下拉列表中选择适合的AI模型
        4. **测试标注**：点击"测试标注功能"验证模型工作正常
        5. **上传文件**：支持CSV、XLSX、XLS格式
        6. **预览数据**：查看文件内容和数据信息
        7. **选择列**：选择需要进行AI标注的列（可多选）
        8. **配置标注**：
           - 编写标注要求：描述AI应该如何判断和分类
           - 设定标注选项：提供具体的分类标签
           - 设置结果列名：指定标注结果存储的列名
        9. **调整参数**：在高级设置中调整创造性程度和输出长度
        10. **执行标注**：点击开始按钮，AI将自动处理数据
        11. **查看结果**：查看标注分布和统计信息
        12. **下载文件**：支持CSV、Excel、JSON格式下载
        
        ### 🔧 API配置示例
        
        #### OpenAI API
        - **API Key**: `sk-...` (OpenAI官方密钥)
        - **Base URL**: 留空或使用代理地址
        - **模型**: gpt-3.5-turbo, gpt-4, gpt-4o等
        
        #### Gemini API (推荐) 🔥
        - **API Key**: 您的Gemini API密钥
        - **Base URL**: `https://generativelanguage.googleapis.com/v1beta/openai/`
        - **模型**: gemini-2.0-flash, gemini-2.5-flash等
        - **优势**: 更好的中文理解能力，推荐使用
        
        ### 💡 使用技巧
        
        - **API配置**：可以设置环境变量 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL` 避免每次输入
        - **模型选择**：
          - **GPT-4**: 质量最高但费用较贵
          - **GPT-3.5**: 速度快，经济实用
          - **Gemini**: 中文友好，**推荐使用**
        - **连接测试**：每次更换API配置后建议重新测试连接
        - **批次大小**：数据量大时建议减小批次大小，提高稳定性
        - **标注要求**：越详细的要求，AI标注效果越好
        - **选项设计**：包含"其他"选项处理边界情况
        - **参数调整**：降低创造性程度可提高一致性，增加可提高灵活性
        
        ### ⚠️ 注意事项
        
        - 确保网络连接稳定
        - 大文件处理可能需要较长时间
        - API调用可能产生费用，请注意用量控制
        - 系统会自动尝试结构化输出以提高准确性
        - 所有API都已优化安全设置，自动处理兼容性
        """)

if __name__ == "__main__":
    main() 