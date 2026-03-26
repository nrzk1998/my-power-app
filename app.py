# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import scraper
import analyzer
import plotter
import os
import io

# 簡易パスワードチェック
def check_password():
    def password_entered():
        if st.session_state["password"] == "acorn": # ここに好きなパスワードを設定
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # セッションに残さない
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("パスワードを入力してください", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("パスワードが違います", type="password", on_change=password_entered, key="password")
        st.error("😕 パスワードが正しくありません")
        return False
    else:
        return True

if not check_password():
    st.stop()  # パスワードが合っていなければここで処理を止める

# --- ここから下に元の解析コードを書く ---
st.set_page_config(page_title="電力分析レポート", layout="wide")
st.title("電力消費クラスタリングツール")

# --- 1. セッション状態の初期化 ---
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False
    st.session_state.final_df = None
    st.session_state.fig_report = None
    st.session_state.fig_cal_buf = None
    st.session_state.input_filename = ""

# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")
    uploaded_file = st.file_uploader("1. power_data.csv をアップロード", type="csv")
    floor_area = st.number_input("2. 延床面積 [m2]", value=5846, min_value=1)
    target_station = st.text_input("3. 地点名", value="神戸")
    
    st.subheader("クラスタ数設定")
    auto_k = st.checkbox("自動決定", value=True)
    k_input = st.slider("クラスタ数 (k)", 2, 10, 4) if not auto_k else None
    
    run_btn = st.button("分析実行", use_container_width=True)

# --- 2. 分析実行ロジック ---
if run_btn and uploaded_file:
    try:
        with st.spinner("解析レポートを作成中..."):
            # データ読み込みと加工
            df_raw = pd.read_csv(uploaded_file, index_col=0)
            df_raw = df_raw[df_raw.index.notna()]
            df_raw.index = pd.to_datetime(df_raw.index)
            df_raw.index.name = 'Date'
            
            df_unit = (df_raw * 1000) / floor_area
            start_date = df_raw.index[0].date()
            end_date = df_raw.index[-1].date()

            # 気象データの取得
            df_weather = scraper.get_weather_data(target_station, start_date, end_date)
            
            if df_weather is not None:
                # クラスタリング
                clusters, k_final = analyzer.perform_clustering(df_unit, k_manual=k_input)
                df_unit['Cluster'] = clusters
                
                # 結合
                final_df = df_unit.join(df_weather, how='inner')
                final_df['DayType'] = final_df['IsHoliday'].map({False: 'Weekday', True: 'Weekend'})
                
                # 結果をセッション状態に保存
                st.session_state.final_df = final_df
                st.session_state.fig_report = plotter.create_combined_report(final_df, k_final)
                st.session_state.input_filename = os.path.splitext(uploaded_file.name)[0]
                
                # カレンダー画像の事前生成
                fig_cal = plotter.create_calendar_report(final_df)
                buf = io.BytesIO()
                fig_cal.savefig(buf, format="png", bbox_inches='tight', dpi=150)
                st.session_state.fig_cal_buf = buf.getvalue()
                
                st.session_state.analyzed = True

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.exception(e)

# --- 3. 表示ロジック（解析済みであれば常に表示） ---
if st.session_state.analyzed:
    # メイン画面のレポート表示
    st.markdown("---")
    st.subheader("📈 パターン分析")
    st.pyplot(st.session_state.fig_report)

    # サイドバー：保存セクション
    st.sidebar.subheader("💾 データ保存")
    
    # CSVダウンロード
    csv_data = st.session_state.final_df.to_csv(encoding='utf-8-sig')
    st.sidebar.download_button(
        label="📊 解析結果(CSV)を保存",
        data=csv_data,
        file_name=f"analysis_{st.session_state.input_filename}.csv",
        mime="text/csv",
        use_container_width=True
    )

    # カレンダー画像ダウンロード
    st.sidebar.download_button(
        label="📅 カレンダー(PNG)を保存",
        data=st.session_state.fig_cal_buf,
        file_name=f"calendar_{st.session_state.input_filename}.png",
        mime="image/png",
        use_container_width=True
    )

else:
    if not run_btn:
        st.info("左側のサイドバーからデータをアップロードして「分析実行」を押してください。")
