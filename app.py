import pandas as pd
from tavily import TavilyClient
from langchain_core.messages import HumanMessage,SystemMessage
from langchain.chat_models import init_chat_model
from datetime import datetime
import streamlit as st
import io


# 页面配置
st.set_page_config(page_title="AI 行业新闻分析助手", page_icon="🤖", layout="wide")
st.title("🤖 AI行业实时新闻深研工具")

# 侧边栏配置 Key
with st.sidebar:
    st.header("密钥配置")
    st.markdown("请填入 API Key 以开始运行。")
    deepseek_key = st.text_input("DeepSeek API Key", type="password", help="在此填入 DeepSeek-V3 的 Key")
    tavily_key = st.text_input("Tavily API Key", type="password", help="在此填入 Tavily 的搜索 Key")
    st.divider()
    st.info("💡 提示：搜索结果将基于过去 24 小时的全网数据。")


# 核心搜索分析函数
def run_research(t_key, d_key):
    try:
        model = init_chat_model("deepseek-chat", api_key=d_key, temperature=0)
        tavily_client = TavilyClient(api_key=t_key)
    except Exception as e:
        st.error(f"初始化失败，请检查 Key 是否正确: {e}")
        return None
     
    query = "最新实时的AI新闻"
    
    with st.status("🔍 正在检索并分析新闻...", expanded=True) as status:
        search_result = tavily_client.search(
            query,
            search_depth="advanced",
            max_results=15, 
            time_range="day")
        system_prompt = """
        # Role
        你是一位拥有 10 年经验的 AI 行业资深分析师，擅长从海量信息中精准识别具有商业价值和技术深度的硬核新闻。

        # Criteria
        - **有价值**：涉及底层模型重大更新、关键技术突破、大厂战略转向、改变行业格局的融资、或重要监管政策。
        - **无价值**：产品软文、简单的工具推荐清单、公关快讯、无事实支撑的口水文。

        # Output Format
        - 若无价值，仅回复：放弃（简述理由）
        - 若有价值，严格按此格式：
        价值判断：有
        深度总结：【核心观点】... ；【行业影响】... 
        """
 
        useful_news = []
        for news in search_result['results']:
            title = news.get('title','无标题')
            content = news.get('content','')
            url = news.get('url')
            
            truncated_content = content[:3000] if content else "无内容"
            user_input = f"请分析以下新闻：\n标题：{title}\n内容：{truncated_content}"
            
            st.write(f"正在分析: `{title[:50]}...`")
       
            try:
                response = model.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_input)]).content
                
                if "价值判断：有" in response:
                    summary = response.split("深度总结：")[-1].strip()
                    st.write(f"✅ 已收录: {title}")
                    useful_news.append({
                        "日期": pd.Timestamp.now().strftime('%Y-%m-%d'),
                        "新闻标题": title,
                        "核心总结": summary,
                        "原始链接": url,
                        "参考摘要": content[:200] + "..." })
                else:
                    reason = response.replace("放弃", "").strip("（）() ")
                    st.write(f"🧹 跳过无关项: {title[:20]}... [原因: {reason}]")
              
            except Exception as e:
                st.warning(f"⚠️ 单条新闻分析失败: {e}")
                continue
        
        status.update(label="✅ 分析完成！", state="complete")
    return useful_news


if st.button("🚀 开始扫描最新 AI 新闻", use_container_width=True):
    if not deepseek_key or not tavily_key:
        st.error("请先在左侧填入两个 API Key！")
    else:
        results = run_research(tavily_key, deepseek_key)
        
        if results:
            st.divider()
            st.subheader("📊 分析结果摘要")
            df = pd.DataFrame(results)
            
            st.dataframe(df[["新闻标题", "核心总结", "原始链接"]], use_container_width=True)
           
            # 导出 Excel (Streamlit 下载按钮)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='AI新闻简报')
            
            st.download_button(
                label="📥 下载完整 Excel 报告",
                data=output.getvalue(),
                file_name=f"AI_Research_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.warning("💡 检索结束，但今天暂未发现符合“深度研究”标准的 AI 新闻。")























