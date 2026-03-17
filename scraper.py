# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import urllib.request
from bs4 import BeautifulSoup
import jpholiday
import datetime
import time
import os
import streamlit as st

DATA_DIR = "data"
STATION_FILE = os.path.join(DATA_DIR, "stations.csv")

def load_station_codes(target_name):
    """stations.csvから地点番号を取得（dtype=strで型を固定）"""
    if not os.path.exists(STATION_FILE):
        st.error(f"ファイルが見つかりません: {STATION_FILE}")
        return None, None
    
    df_st = pd.read_csv(STATION_FILE, dtype=str)
    match = df_st[df_st["name"] == target_name]
    
    if match.empty:
        st.error(f"地点 '{target_name}' が見つかりません。")
        return None, None
    
    prec_no = match.iloc[0]["prec_no"]
    block_no = match.iloc[0]["block_no"]
    
    # 画面（サイドバー）に地点情報を表示
    st.sidebar.info(f"📍 取得地点: {target_name}\n- prec_no: {prec_no}\n- block_no: {block_no}")
    
    return prec_no, block_no

def get_weather_data(station_name, base_year):
    """気象データを取得。キャッシュがあれば読み込み、なければスクレイピング。"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    cache_path = os.path.join(DATA_DIR, f"weather_{station_name}_{base_year}.csv")
    
    # キャッシュ確認
    if os.path.exists(cache_path):
        st.sidebar.success("✅ 保存済みの気象データを使用します")
        df = pd.read_csv(cache_path, index_col=0)
        df.index = pd.to_datetime(df.index)
        df.index.name = 'Date'
        return df
    
    prec_no, block_no = load_station_codes(station_name)
    if not prec_no or not block_no:
        return None
    
    all_data = []
    progress_bar = st.progress(0, text="気象庁からデータを取得中...")
    
    for i in range(12):
        curr_month = (4 + i - 1) % 12 + 1
        curr_year = base_year + 1 if curr_month <= 3 else base_year
        
        url = (f"https://www.data.jma.go.jp/stats/etrn/view/daily_s1.php?"
               f"prec_no={prec_no}&block_no={block_no}&year={curr_year}&month={curr_month}&day=&view=")
        
        try:
            html = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", class_="data2_s")
            if table:
                rows = table.select("tr")[4:]
                for tr in rows:
                    tds = tr.find_all("td")
                    if not tds or not tds[0].string: continue
                    # 数値記号の除去
                    temp_val = tds[6].string.replace(" )", "").replace(" ]", "").replace("×", "").replace("#", "")
                    all_data.append({
                        "Date": datetime.date(curr_year, curr_month, int(tds[0].string)),
                        "AverageTemperature": float(temp_val)
                    })
        except:
            continue
        
        progress_bar.progress((i + 1) / 12)
        time.sleep(0.8)

    if not all_data:
        st.error(f"気象データが取得できませんでした。")
        return None

    df_w = pd.DataFrame(all_data)
    df_w['Date'] = pd.to_datetime(df_w['Date'])
    df_w.set_index('Date', inplace=True)
    
    # 休日判定（英語フラグ）
    df_w['IsHoliday'] = df_w.index.map(lambda x: x.dayofweek >= 5 or jpholiday.is_holiday(x))
    
    # 季節判定（英語ラベル）
    def classify_season(t):
        if t >= 27.0: return 'Cooling'
        elif t <= 10.0: return 'Heating'
        else: return 'Intermediate'
    
    df_w['Season'] = df_w['AverageTemperature'].apply(classify_season)
    
    # キャッシュ保存
    df_w.to_csv(cache_path, encoding='utf-8')
    return df_w