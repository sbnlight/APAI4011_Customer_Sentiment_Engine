import os
import warnings
import logging

# 屏蔽 TensorFlow/oneDNN 的加速提示 (白色文字)
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 只显示严重错误，屏蔽警告

# 屏蔽 Python 的警告 (红色 DeprecationWarning)
warnings.filterwarnings("ignore")

# 屏蔽 TensorFlow 内部日志
logging.getLogger('tensorflow').setLevel(logging.ERROR)

import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# 配置
DATA_FOLDER = "data_with_sentiment_score"
DB_PATH = "./chroma_db"  # 数据库保存路径

def build_vector_db():
    print("🚀 开始构建向量数据库...")
    
    # 1. 读取 CSV 数据
    documents = []
    if not os.path.exists(DATA_FOLDER):
        print("错误：找不到数据文件夹")
        return

    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.csv')]
    for file in files:
        file_path = os.path.join(DATA_FOLDER, file)
        try:
            df = pd.read_csv(file_path)
            df = df.fillna('')
            for _, row in df.iterrows():
                # 构建内容
                content = (
                    f"Category: {row.get('Category', 'Unknown')}\n"
                    f"Brand: {row.get('Brand', 'Unknown')}\n"
                    f"Review: {row.get('Review', 'No text')}\n"
                    f"Rating: {row.get('Star_Rating', 'N/A')}\n"
                    f"Weighted Score: {row.get('Final_Weighted_Score', 'N/A')}\n"
                )
                metadata = {
                    "source": file,
                    "brand": row.get('Brand', 'Unknown'),
                    "score": row.get('Final_Weighted_Score', 0)
                }
                documents.append(Document(page_content=content, metadata=metadata))
        except Exception as e:
            print(f"跳过文件 {file}: {e}")

    print(f"共加载 {len(documents)} 条数据，准备向量化（这可能需要一点时间）...")

    # 2. 初始化嵌入模型 (和 app.py 保持一致)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 3. 创建并保存数据库
    # persist_directory 参数会将数据保存到硬盘
    vector_store = Chroma.from_documents(
        documents=documents, 
        embedding=embeddings,
        collection_name="startup_market_insights",
        persist_directory=DB_PATH 
    )
    
    print(f"数据库构建完成！已保存到 '{DB_PATH}' 文件夹。")
    print("以后运行 app.py 时不需要再重新读取 CSV 了。")

if __name__ == "__main__":
    build_vector_db()