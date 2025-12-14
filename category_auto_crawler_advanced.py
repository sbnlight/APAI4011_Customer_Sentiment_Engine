# --- START OF FILE category_auto_crawler.py ---

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import re # 引入正则模块，用于提取星星数字

TARGET_CATEGORIES = [
    "https://www.trustpilot.com/categories/animals_pets?sort=reviews_count",
    "https://www.trustpilot.com/categories/events_entertainment?sort=reviews_count",
    "https://www.trustpilot.com/categories/home_garden?sort=reviews_count",
    "https://www.trustpilot.com/categories/restaurants_bars?sort=reviews_count",
    "https://www.trustpilot.com/categories/beauty_wellbeing?sort=reviews_count",
    "https://www.trustpilot.com/categories/food_beverages_tobacco?sort=reviews_count",
    "https://www.trustpilot.com/categories/home_services?sort=reviews_count",
    "https://www.trustpilot.com/categories/shopping_fashion?sort=reviews_count",
    "https://www.trustpilot.com/categories/business_services?sort=reviews_count",
    "https://www.trustpilot.com/categories/legal_services_government?sort=reviews_count",
    "https://www.trustpilot.com/categories/sports?sort=reviews_count",
    "https://www.trustpilot.com/categories/health_medical?sort=reviews_count",
    "https://www.trustpilot.com/categories/construction_manufactoring?sort=reviews_count",
    "https://www.trustpilot.com/categories/media_publishing?sort=reviews_count",
    "https://www.trustpilot.com/categories/travel_vacation?sort=reviews_count",
    "https://www.trustpilot.com/categories/money_insurance?sort=reviews_count",
    "https://www.trustpilot.com/categories/hobbies_crafts?sort=reviews_count",
    "https://www.trustpilot.com/categories/education_training?sort=reviews_count",
    "https://www.trustpilot.com/categories/utilities?sort=reviews_count",
    "https://www.trustpilot.com/categories/public_local_services?sort=reviews_count",
    "https://www.trustpilot.com/categories/vehicles_transportation?sort=reviews_count",
    "https://www.trustpilot.com/categories/electronics_technology?sort=reviews_count"
]

MAX_SHOPS_PER_CATEGORY = 10     # 每个分类下爬20个店
TARGET_REVIEWS_PER_SHOP = 50   # 每个店爬500条

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

def get_shops_from_category(category_url):
    base_url = category_url.split('?')[0]
    category_name = base_url.split('/')[-1]

    print(f"\n正在扫描分类: {category_name} ...")
    
    shop_links = []
    try:
        response = requests.get(category_url, headers=HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                if href.startswith('/review/') and 'trustpilot.com' not in href:
                    full_url = "https://www.trustpilot.com" + href
                    if full_url not in shop_links:
                        shop_links.append(full_url)
                    if len(shop_links) >= MAX_SHOPS_PER_CATEGORY:
                        break
        else:
            print(f"无法访问分类页面: {category_url}")
    except Exception as e:
        print(f"扫描出错: {e}")
        
    print(f" -> 在该分类下找到了 {len(shop_links)} 个店铺链接")
    return shop_links


def get_reviews_for_one_shop(shop_url, target_count):
    collected_reviews = []
    page_number = 1
    shop_name = shop_url.split('/')[-1]
    
    print(f"   [开始爬取店铺]: {shop_name}")

    while len(collected_reviews) < target_count:
        current_url = f"{shop_url}?page={page_number}"
        
        try:
            response = requests.get(current_url, headers=HEADERS)
            if response.status_code != 200:
                print(f"      页面 {page_number} 访问失败或结束")
                break
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # --- 修改重点：查找 Review 卡片 ---
            # Trustpilot 的每条评论通常被包裹在 <article> 标签中
            review_cards = soup.find_all('article')
            
            if not review_cards:
                # 如果没有 article 标签，可能是页面结构变了，尝试找特定的 div
                # 但目前 Trustpilot 主要是 article
                print("      未找到评论卡片，可能已翻页到底。")
                break

            for card in review_cards:
                # 1. 提取星星评分
                # 通常是一个 img 标签，alt 属性写着 "Rated 5 out of 5 stars"
                star_rating = None
                star_img = card.find('img', alt=re.compile(r'Rated \d out of 5 stars'))
                
                if star_img:
                    alt_text = star_img['alt']
                    # 提取数字
                    match = re.search(r'Rated (\d)', alt_text)
                    if match:
                        star_rating = int(match.group(1))
                
                # 如果找不到 img，尝试找 data-service-review-rating 属性
                if star_rating is None:
                    rating_div = card.find('div', attrs={'data-service-review-rating': True})
                    if rating_div:
                        star_rating = int(rating_div['data-service-review-rating'])

                # 2. 提取评论文本
                # 查找特定的排版 p 标签
                text_element = card.find('p', {'data-service-review-text-typography': 'true'})
                review_text = text_element.get_text(strip=True) if text_element else ""
                
                # 只有当星星和文本至少有一个存在时才保存
                # (有些评论可能只有星星没有字，或者只有标题)
                if star_rating is not None:
                    # 如果没有正文，尝试找标题 (h2)
                    if not review_text:
                        title_element = card.find('h2', {'data-service-review-title-typography': 'true'})
                        if title_element:
                            review_text = title_element.get_text(strip=True)

                    collected_reviews.append({
                        'text': review_text,
                        'rating': star_rating
                    })
                
                if len(collected_reviews) >= target_count:
                    break
            
            page_number += 1
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"      爬取出错: {e}")
            break
            
    print(f"   -> 完成，共抓取 {len(collected_reviews)} 条")
    return collected_reviews


if __name__ == "__main__":
    folder_name = "categories_data_small"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    for cat_url in TARGET_CATEGORIES:
        base_url = cat_url.split('?')[0] 
        cat_name = base_url.split('/')[-1]
        
        current_cat_data = [] 
        shops = get_shops_from_category(cat_url)
        
        for shop_url in shops:
            # 获取的数据现在是字典列表 [{'text':..., 'rating':...}]
            reviews_data = get_reviews_for_one_shop(shop_url, TARGET_REVIEWS_PER_SHOP)
            
            for item in reviews_data:
                current_cat_data.append({
                    'Category': cat_name, 
                    'Brand': shop_url.split('/')[-1],
                    'Review': item['text'],
                    'Star_Rating': item['rating'] # 新增一列
                })
            
            time.sleep(random.uniform(2, 5))
            
        if current_cat_data:
            filename = f"{folder_name}/reviews_{cat_name}.csv"
            df = pd.DataFrame(current_cat_data)
            # 确保 Review 列是字符串，防止后续处理报错
            df['Review'] = df['Review'].fillna("")
            df.to_csv(filename, index=False)
            print(f"成功！分类 '{cat_name}' 已保存为: {filename}")
        else:
            print(f"分类 '{cat_name}' 没有抓到数据。")
            
        print("-" * 50)

    print(f"\n🎉 所有分类全部处理完毕！请去 '{folder_name}' 文件夹查看结果。")