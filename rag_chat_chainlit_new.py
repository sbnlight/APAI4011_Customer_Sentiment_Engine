import os
import pandas as pd
import chainlit as cl
from langchain_openai import ChatOpenAI  # 使用 OpenAI 兼容的客户端
from langchain_community.embeddings import HuggingFaceEmbeddings  # 使用本地嵌入
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain.chains import RetrievalQA

# ================= CONFIGURATION =================
# 使用 Qwen API
QWEN_API_KEY = "sk-AP6F9xfYrwdouNurkEpOobIWkFv8cC0E30A46CEC111F0BEC92E52BC8C0AB2"

# 设置环境变量
os.environ["QWEN_API_KEY"] = QWEN_API_KEY

DB_PATH = "./chroma_db"
# ===============================================

# 向量化后不需要
'''
def load_data_as_documents(folder_path):
    """加载数据文档"""
    documents = []
    if not os.path.exists(folder_path):
        print(f"警告：数据文件夹 '{folder_path}' 不存在")
        return []

    files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    if not files:
        print(f"警告：在 '{folder_path}' 中没有找到 CSV 文件")
        return []
    
    for file in files:
        file_path = os.path.join(folder_path, file)
        try:
            df = pd.read_csv(file_path)
            df = df.fillna('')
            for _, row in df.iterrows():
                content = (
                    f"Category (Industry): {row.get('Category', 'Unknown')}\n"
                    f"Brand (Competitor): {row.get('Brand', 'Unknown')}\n"
                    f"Customer Original Review: {row.get('Review', 'No text')}\n"
                    f"--- Analysis Data ---\n"
                    f"User Given Rating: {row.get('Star_Rating', 'N/A')} Stars\n"
                    f"Sentiment Implied Score: {row.get('Sentiment_Implied_Rating', 'N/A')}\n"
                    f"Final Weighted Score: {row.get('Final_Weighted_Score', 'N/A')}\n"
                )
                
                metadata = {
                    "source": file,
                    "brand": row.get('Brand', 'Unknown'),
                    "score": row.get('Final_Weighted_Score', 0)
                }
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
        except Exception as e:
            print(f"读取文件 {file} 时出错: {e}")
    
    print(f"已加载 {len(documents)} 条文档")
    return documents
'''

@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content="👋 **Hello! I am your Startup Assistant.**\n\nLoading market insights database...").send()

    # 加载嵌入模型
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # 直接从硬盘加载数据库
    if os.path.exists(DB_PATH):
        vector_store = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embeddings,
            collection_name="startup_market_insights"
        )
        print("✅ 已加载本地数据库")
    else:
        await cl.Message(content="❌ Error: Database not found. Please run build_db.py first.").send()
        return

    # 提示模板
    prompt_template = """
    You are a supportive, data-driven, and service-oriented **Startup Assistant**. 
    Your goal is to assist entrepreneurs in identifying market opportunities and handling customer relationships based on real data.
    You are NOT a boss or a lecturer; you are a helpful partner.

    You have access to real customer reviews of competitors in the market.

    Context (Real Market Feedback):
    {context}

    ---

    User Question: 
    {question}

    ---
    
    **Your Guidelines:**
    1.  **Be Helpful & Humble**: Use a professional, service-oriented tone (e.g., "Here is what I found," "You might consider...").
    2.  **Market Identification**: If asked about opportunities, analyze the "Pain Points" (complaints) and "Highlights" (praises) in the Context. Compare the User Rating vs. the Weighted Score.
    3.  **Customer Conversation**: If asked to draft a reply, draft a polite and professional response based on the specific review in the Context.
    4.  **Language**: **ALWAYS ANSWER IN ENGLISH.**
    5.  **Format**: Use Markdown (bullet points, bold text) for better readability.

    Answer:
    """
    
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    # 使用 Qwen API
    llm = ChatOpenAI(
        model="qwen-turbo",  # Qwen 模型
        api_key=QWEN_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 阿里云 Qwen API 端点
        temperature=0.3
    )

    # 创建检索链
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={"k": 8}), 
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )

    # 存储 chain 到会话
    cl.user_session.set("chain", chain)

    # 就绪消息
    welcome_text = """ **I am ready to help!**

Here are a few things I can do for you:
*   **Market Research:** "What are the common complaints in this industry?"
*   **Competitor Analysis:** "Which brand has the best weighted score and why?"
*   **Customer Support:** "Draft a polite reply to this angry customer review."

How can I assist your startup today?"""
    
    await cl.Message(content=welcome_text).send()

@cl.on_message
async def main(message: cl.Message):
    chain = cl.user_session.get("chain")
    if not chain:
        await cl.Message(content="系统未初始化，请刷新页面重试。").send()
        return
    
    cb = cl.AsyncLangchainCallbackHandler()
    
    try:
        # 执行查询
        res = await chain.acall(message.content, callbacks=[cb])
        
        answer = res["result"]
        source_documents = res["source_documents"]

        # 准备源文档显示
        text_elements = []  
        
        if source_documents:
            for i, doc in enumerate(source_documents):
                brand = doc.metadata.get('brand', 'Unknown')
                score = doc.metadata.get('score', 'N/A')
                
                # 提取评论文本预览
                raw_content = doc.page_content.split("Customer Original Review:")[-1]
                content_preview = raw_content.split("--- Analysis Data ---")[0].strip()
                
                # 创建可点击的源卡片
                source_name = f"Source {i+1}: {brand} (Score: {score})"
                text_elements.append(
                    cl.Text(content=content_preview, name=source_name, display="inline")
                )

        # 发送最终响应
        await cl.Message(content=answer, elements=text_elements).send()
    except Exception as e:
        await cl.Message(content=f"Error processing request: {str(e)}").send()