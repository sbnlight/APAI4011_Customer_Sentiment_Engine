import pandas as pd
import os
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# 首次运行时需要下载词典

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    print("正在下载 VADER 词典...")
    nltk.download('vader_lexicon')

def analyze_sentiment_and_score():
    # 输入文件夹（爬虫生成的数据）
    input_folder = "categories_data_small"
    # 输出文件夹（处理后的数据）
    output_folder = "data_with_sentiment_score"
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 初始化情感分析器
    sid = SentimentIntensityAnalyzer()

    # 权重设置
    WEIGHT_USER_RATING = 0.5
    WEIGHT_TEXT_SENTIMENT = 0.5

    print(f"开始处理文件夹 '{input_folder}' 中的文件...\n")

    # 遍历文件夹下的所有 CSV 文件
    files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
    
    if not files:
        print(f"错误：在 '{input_folder}' 中没有找到 CSV 文件。请先运行爬虫。")
        return

    for file in files:
        input_path = os.path.join(input_folder, file)
        print(f"正在处理: {file} ...")

        try:
            df = pd.read_csv(input_path)
            
            # 确保 Review 列是字符串，处理空值
            df['Review'] = df['Review'].fillna("").astype(str)
            
            # 存储计算结果的列表
            sentiment_scores_raw = [] # VADER 原始分 (-1 到 1)
            sentiment_stars = []      # VADER 转换后的星级 (1 到 5)
            weighted_scores = []      # 最终加权分

            for index, row in df.iterrows():
                text = row['Review']
                user_rating = row['Star_Rating']
                
                # 1. 进行情感分析
                # 如果文本太短（例如只有几个字），VADER 可能不准，但它是目前最通用的方案
                if len(text.strip()) > 0:
                    ss = sid.polarity_scores(text)
                    compound_score = ss['compound'] # 获取综合得分 (-1 ~ 1)
                else:
                    # 如果没有文字，情感得分默认为中性 0
                    compound_score = 0.0

                # 2. 将情感分数映射到 1-5 星
                # logic: -1 -> 1星, 0 -> 3星, +1 -> 5星
                # linear mapping formula: y = 2x + 3
                # x=-1, y=1; x=0, y=3; x=1, y=5
                predicted_star = 2 * compound_score + 3
                
                # 限制范围在 1-5 之间 (虽然数学上不会超，但保险起见)
                predicted_star = max(1.0, min(5.0, predicted_star))

                # 3. 计算加权平均
                # 结合 用户打分 (user_rating) 和 文本分析推断分 (predicted_star)
                final_score = (user_rating * WEIGHT_USER_RATING) + (predicted_star * WEIGHT_TEXT_SENTIMENT)

                sentiment_scores_raw.append(round(compound_score, 4))
                sentiment_stars.append(round(predicted_star, 2))
                weighted_scores.append(round(final_score, 2))

            # 将结果写回 DataFrame
            df['Sentiment_Raw_Score'] = sentiment_scores_raw # VADER原始分
            df['Sentiment_Implied_Rating'] = sentiment_stars # 根据文字推断的星级
            df['Final_Weighted_Score'] = weighted_scores     # 加权后的最终得分

            # 保存到新文件夹
            output_path = os.path.join(output_folder, f"analyzed_{file}")
            df.to_csv(output_path, index=False)
            print(f" -> 已保存结果到: {output_path}")

        except Exception as e:
            print(f"处理文件 {file} 时出错: {e}")

    print(f"\n🎉 所有分析完成！请查看 '{output_folder}' 文件夹。")

if __name__ == "__main__":
    analyze_sentiment_and_score()