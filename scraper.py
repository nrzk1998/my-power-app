# -*- coding: utf-8 -*-
import datetime
import os
import time
import urllib.request

from bs4 import BeautifulSoup
import jpholiday
import pandas as pd
import streamlit as st

DATA_DIR = "data"
STATION_FILE = os.path.join(DATA_DIR, "stations.csv")


def _build_cache_path(station_name, start_date, end_date):
    date_range_str = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
    return os.path.join(DATA_DIR, f"weather_{station_name}_{date_range_str}.csv")


def _load_cached_weather_data(cache_path):
    df = pd.read_csv(cache_path, index_col=0)
    df.index = pd.to_datetime(df.index)
    df.index.name = 'Date'
    return df


def _iter_target_months(start_date, end_date):
    months = []
    current = start_date.replace(day=1)
    while current <= end_date:
        months.append((current.year, current.month))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    return months


def _build_weather_url(prec_no, block_no, year, month):
    return (
        "https://www.data.jma.go.jp/stats/etrn/view/daily_s1.php?"
        f"prec_no={prec_no}&block_no={block_no}&year={year}&month={month}&day=&view="
    )


def _parse_temperature(value):
    return float(value.replace(" )", "").replace(" ]", "").replace("×", "").replace("#", ""))


def _fetch_monthly_weather_data(prec_no, block_no, year, month):
    html = urllib.request.urlopen(_build_weather_url(prec_no, block_no, year, month)).read()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="data2_s")
    if not table:
        return []

    rows = []
    for tr in table.select("tr")[4:]:
        tds = tr.find_all("td")
        if not tds or not tds[0].string:
            continue

        rows.append({
            "Date": datetime.date(year, month, int(tds[0].string)),
            "AverageTemperature": _parse_temperature(tds[6].string),
        })

    return rows


def _classify_season(temperature):
    if temperature >= 27.0:
        return 'Cooling'
    if temperature <= 10.0:
        return 'Heating'
    return 'Intermediate'


def _build_weather_dataframe(all_data):
    df_weather = pd.DataFrame(all_data)
    df_weather['Date'] = pd.to_datetime(df_weather['Date'])
    df_weather.set_index('Date', inplace=True)
    df_weather['IsHoliday'] = df_weather.index.map(lambda x: x.dayofweek >= 5 or jpholiday.is_holiday(x))
    df_weather['Season'] = df_weather['AverageTemperature'].apply(_classify_season)
    return df_weather

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

def get_weather_data(station_name, start_date, end_date):
    """気象データを取得。キャッシュがあれば読み込み、なければスクレイピング。"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    cache_path = _build_cache_path(station_name, start_date, end_date)
    
    # キャッシュ確認
    if os.path.exists(cache_path):
        st.sidebar.success("✅ 保存済みの気象データを使用します")
        return _load_cached_weather_data(cache_path)
    
    prec_no, block_no = load_station_codes(station_name)
    if not prec_no or not block_no:
        return None
    
    all_data = []
    progress_bar = st.progress(0, text="気象庁からデータを取得中...")
    months_to_fetch = _iter_target_months(start_date, end_date)
    
    for i, (curr_year, curr_month) in enumerate(months_to_fetch):
        try:
            all_data.extend(_fetch_monthly_weather_data(prec_no, block_no, curr_year, curr_month))
        except Exception:
            continue
        
        progress_bar.progress((i + 1) / len(months_to_fetch))
        time.sleep(0.8)

    if not all_data:
        st.error(f"気象データが取得できませんでした。")
        return None

    df_w = _build_weather_dataframe(all_data)
    
    # キャッシュ保存
    df_w.to_csv(cache_path, encoding='utf-8')
    return df_w