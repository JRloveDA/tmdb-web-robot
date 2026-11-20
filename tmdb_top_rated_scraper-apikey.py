import requests
import csv
import time
import os

# ===== 配置 =====
API_KEY = os.environ.get("TMDB_API_KEY")   # 在系统高级设置中添加系统变量
BASE_URL = "https://api.themoviedb.org/3"
LANG = "zh-CN"                          # 中文（简体）；需要繁体用 "zh-TW"
MOVIE_LIST_FILE = "csv_data/movie_list_byapikey.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
}

# 1. 获取高分电影榜单的 id 列表
def get_top_movie_ids(pages=1):
    ids = []
    for page in range(1, pages + 1):
        url = f"{BASE_URL}/movie/top_rated"
        resp = requests.get(url, headers=HEADERS,
                            params={"api_key": API_KEY, "language": LANG, "page": page},
                            timeout=60)
        resp.raise_for_status()
        for m in resp.json().get("results", []):
            ids.append(m["id"])
    return ids

# 2. 获取单部电影详情（中文）
def get_movie_info(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"
    resp = requests.get(url, headers=HEADERS,
                        params={"api_key": API_KEY, "language": LANG,
                                "append_to_response": "credits"},   # 一次性拿演职人员
                        timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # 导演
    directors = [c["name"] for c in data.get("credits", {}).get("crew", [])
                 if c.get("job") == "Director"]
    # 编剧 / 作者
    writers = [c["name"] for c in data.get("credits", {}).get("crew", [])
               if c.get("job") in ("Screenplay", "Writer", "Author")]
    # 主演（取前 5 位）
    cast = [c["name"] for c in data.get("credits", {}).get("cast", [])][:5]
    # 语言
    languages = [l.get("name", "") for l in data.get("spoken_languages", [])]

    release_date = data.get("release_date", "")
    year = release_date[:4] if release_date else ""

    movie_info = {
        "电影名":   data.get("title", ""),
        "电影年份": year,
        "上映时间": release_date,
        "类型":     ",".join(g.get("name", "") for g in data.get("genres", [])),
        "时长":     f"{data.get('runtime', '')} 分钟" if data.get("runtime") else "",
        "评分":     data.get("vote_average", ""),
        "语言":     ",".join(languages),
        "导演":     ",".join(directors),
        "作者":     ",".join(writers),
        "主演":     ",".join(cast),
        "Slogan":   data.get("tagline", ""),
        "简介":     data.get("overview", ""),
    }
    print(movie_info)
    return movie_info

# 3. 保存为 CSV（用 utf-8-sig，Excel 打开中文不乱码）
def save_all_movies(all_movies):
    with open(MOVIE_LIST_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "电影名","电影年份","上映时间","类型","时长","评分",
            "语言","导演","作者","主演","Slogan","简介"])
        writer.writeheader()
        writer.writerows(all_movies)

# 4. 主流程
def main():
    ids = get_top_movie_ids(pages=5)
    print(f"共获取到 {len(ids)} 部电影 id")
    all_movies = []
    for mid in ids:
        try:
            all_movies.append(get_movie_info(mid))
        except Exception as e:
            print(f"获取电影 {mid} 失败: {e}")
        time.sleep(0.25)  # 友好限速，避免触发 TMDB 限流
    save_all_movies(all_movies)
    print("全部完成，已保存到", MOVIE_LIST_FILE)

if __name__ == "__main__":
    main()
