========================================================================
   Market Insight & Engagement Chatbot - Project README
========================================================================

1. PROJECT OVERVIEW
-------------------
This project is a RAG (Retrieval-Augmented Generation) based chatbot designed to assist startups. 
It processes Trustpilot reviews, calculates a "Weighted Sentiment Score" for each review, 
and uses the Qwen (Tongyi Qianwen) Large Language Model to answer strategic business questions.

Key features:
- Identifies market pain points from competitor reviews.
- Simulates customer service responses based on sentiment analysis.
- Uses local vector storage (ChromaDB) for fast retrieval.

2. FILE STRUCTURE
-------------------
[Source Code]
- rag_chat_chainlit_new.py      : MAIN APPLICATION. Run this to start the chatbot.
- build_db.py                   : Utility script to vectorise CSV data into ChromaDB.
- sentiment_analysis.py         : Analyzes raw reviews and calculates the Weighted Score.
- category_auto_crawler_advanced.py : Web crawler to fetch raw data from Trustpilot.

[Data Folders]
- chroma_db/                    : Pre-built vector database (The "Brain" memory).
- data_with_sentiment_score/    : Processed CSV files with weighted scores.
- categories_data_small/        : Raw scraped data.

3. PREREQUISITES
-------------------
Ensure you have Python 3.9 or higher installed.

You need to install the required Python libraries. Open your terminal/command prompt 
in this folder and run the following command:

   pip install chainlit pandas langchain langchain-community langchain-openai langchain-core langchain-huggingface chromadb

4. HOW TO RUN THE CHATBOT (Quick Start)
---------------------------------------
Since the database (`chroma_db`) is already pre-built in this package, 
you can run the chatbot immediately.

1. Open your terminal or command prompt.
2. Navigate to this project folder.
3. Run the following command:

   chainlit run rag_chat_chainlit_new.py -w

4. The browser should open automatically (http://localhost:8000). 
   If not, copy the link into your browser.

5. HOW TO REBUILD THE DATABASE (Optional)
-----------------------------------------
If you have added new CSV files to the 'data_with_sentiment_score' folder 
and want to update the chatbot's knowledge:

1. Run the build script:
   python build_db.py

2. Wait for the process to finish. It will update the 'chroma_db' folder.
3. Restart the chatbot using the command in Section 4.

6. CONFIGURATION (API Key)
--------------------------
The project is currently configured to use the Qwen API.
The API Key is located inside `rag_chat_chainlit_new.py`.

If you need to change the API Key:
1. Open `rag_chat_chainlit_new.py` in a text editor.
2. Locate the line: `QWEN_API_KEY = "sk-..."`
3. Replace the string with your new key.

7. TROUBLESHOOTING
------------------
- Issue: "Module not found" error.
  Solution: Ensure you have run the `pip install` command in Section 3.

- Issue: The chatbot does not reply.
  Solution: Check your internet connection (API requires internet) or check if the API Key is valid.

========================================================================