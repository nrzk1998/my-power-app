# -*- coding: utf-8 -*-
import io
import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import analyzer
import plotter
import scraper


st.set_page_config(page_title="電力分析レポート", layout="wide")


PASSWORD = "acorn"
STATE_DEFAULTS = {
    'analyzed': False,
    'final_df': None,
    'fig_report': None,
    'fig_cal_buf': None,
    'input_filename': "",
    'k_final': None,
    'target_station': "",
}


def inject_styles():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(41, 98, 255, 0.12), transparent 28%),
                radial-gradient(circle at top right, rgba(0, 150, 136, 0.14), transparent 30%),
                linear-gradient(180deg, #f4f7fb 0%, #eef3f8 100%);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }
        .hero-panel {
            padding: 1.8rem 2rem;
            border-radius: 24px;
            color: #0f172a;
            background: linear-gradient(135deg, rgba(255,255,255,0.94), rgba(226, 240, 255, 0.9));
            border: 1px solid rgba(15, 23, 42, 0.08);
            box-shadow: 0 22px 60px rgba(15, 23, 42, 0.08);
            margin-bottom: 1.25rem;
        }
        .hero-kicker {
            font-size: 0.78rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #0f766e;
            margin-bottom: 0.65rem;
            font-weight: 700;
        }
        .hero-title {
            font-size: 2.2rem;
            line-height: 1.1;
            font-weight: 800;
            margin: 0;
        }
        .hero-copy {
            margin-top: 0.9rem;
            font-size: 1rem;
            line-height: 1.7;
            color: #334155;
            max-width: 780px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.9rem;
            margin: 1rem 0 1.4rem;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            backdrop-filter: blur(10px);
        }
        .status-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            margin-bottom: 0.45rem;
            font-weight: 700;
        }
        .status-value {
            font-size: 1.35rem;
            color: #0f172a;
            font-weight: 800;
        }
        .section-card {
            background: rgba(255, 255, 255, 0.86);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 22px;
            padding: 1.2rem 1.3rem;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.06);
        }
        .empty-state {
            padding: 1.4rem 1.5rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(230, 244, 241, 0.92));
            border: 1px solid rgba(15, 23, 42, 0.08);
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.06);
        }
        .login-panel {
            max-width: 560px;
            margin: 3.5rem auto 0;
            padding: 1.7rem 1.8rem;
            border-radius: 24px;
            background: rgba(255,255,255,0.92);
            border: 1px solid rgba(15, 23, 42, 0.08);
            box-shadow: 0 22px 60px rgba(15, 23, 42, 0.08);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #132238 100%);
            border-right: 1px solid rgba(255,255,255,0.08);
        }
        [data-testid="stSidebar"] * {
            color: #e2e8f0;
        }
        [data-testid="stSidebar"] .stButton button {
            background: linear-gradient(135deg, #0f766e, #1d4ed8);
            color: white;
            border: none;
        }
        [data-testid="stSidebar"] .stDownloadButton button {
            border-radius: 12px;
        }
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button,
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] span,
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] div,
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] small,
        [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] span,
        [data-testid="stSidebar"] [data-testid="stFileUploaderFileName"] {
            color: #f8fafc !important;
            -webkit-text-fill-color: #f8fafc !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }
        [data-testid="stSidebar"] div[data-baseweb="input"] input,
        [data-testid="stSidebar"] div[data-baseweb="base-input"] input,
        [data-testid="stSidebar"] .stNumberInput input {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            background: rgba(255, 255, 255, 0.98) !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }
        [data-testid="stSidebar"] input::placeholder {
            color: #334155 !important;
            -webkit-text-fill-color: #334155 !important;
            opacity: 1 !important;
        }
        div[data-baseweb="input"] input,
        div[data-baseweb="select"] input,
        div[data-baseweb="base-input"] input {
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_session_state():
    for key, value in STATE_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def password_entered():
    if st.session_state.get('password') == PASSWORD:
        st.session_state['password_correct'] = True
        del st.session_state['password']
    else:
        st.session_state['password_correct'] = False


def check_password():
    if st.session_state.get('password_correct'):
        return True

    st.markdown(
        """
        <div class="login-panel">
            <div class="hero-kicker">Protected Workspace</div>
            <h1 class="hero-title">電力分析ダッシュボード</h1>
            <p class="hero-copy">
                解析機能に入る前にパスワードを入力してください。レポート生成、クラスタリング、
                気象データ連携をこの画面から実行できます。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prompt = "パスワードを入力してください"
    if 'password_correct' in st.session_state and not st.session_state['password_correct']:
        prompt = "パスワードが違います。再入力してください"

    st.text_input(prompt, type="password", on_change=password_entered, key="password")
    if 'password_correct' in st.session_state and not st.session_state['password_correct']:
        st.error("パスワードが正しくありません")
    return False


def read_power_data(uploaded_file, floor_area):
    df_raw = pd.read_csv(uploaded_file, index_col=0)
    df_raw = df_raw[df_raw.index.notna()]
    df_raw.index = pd.to_datetime(df_raw.index)
    df_raw.index.name = 'Date'

    df_unit = (df_raw * 1000) / floor_area
    return df_raw, df_unit


def create_calendar_buffer(final_df):
    fig_cal = plotter.create_calendar_report(final_df)
    buf = io.BytesIO()
    fig_cal.savefig(buf, format="png", bbox_inches='tight', dpi=150)
    plt.close(fig_cal)
    return buf.getvalue()


def build_analysis_result(uploaded_file, floor_area, target_station, k_input):
    df_raw, df_unit = read_power_data(uploaded_file, floor_area)
    start_date = df_raw.index[0].date()
    end_date = df_raw.index[-1].date()

    df_weather = scraper.get_weather_data(target_station, start_date, end_date)
    if df_weather is None:
        return None

    clusters, k_final = analyzer.perform_clustering(df_unit, k_manual=k_input)
    df_unit = df_unit.copy()
    df_unit['Cluster'] = clusters

    final_df = df_unit.join(df_weather, how='inner')
    final_df['DayType'] = final_df['IsHoliday'].map({False: 'Weekday', True: 'Weekend'})

    return {
        'final_df': final_df,
        'fig_report': plotter.create_combined_report(final_df, k_final),
        'fig_cal_buf': create_calendar_buffer(final_df),
        'input_filename': os.path.splitext(uploaded_file.name)[0],
        'k_final': k_final,
        'target_station': target_station,
    }


def store_analysis_result(result):
    previous_fig = st.session_state.get('fig_report')
    if previous_fig is not None:
        plt.close(previous_fig)

    for key, value in result.items():
        st.session_state[key] = value
    st.session_state['analyzed'] = True


def run_analysis(uploaded_file, floor_area, target_station, k_input):
    with st.spinner("解析レポートを作成中..."):
        result = build_analysis_result(uploaded_file, floor_area, target_station, k_input)
        if result is not None:
            store_analysis_result(result)


def render_hero():
    st.markdown(
        """
        <div class="hero-panel">
            <div class="hero-kicker">Power Clustering Studio</div>
            <h1 class="hero-title">電力消費クラスタリングツール</h1>
            <p class="hero-copy">
                日別の消費パターンをクラスタリングし、気象条件や休日判定と合わせて可視化します。
                分析条件を左で指定すると、レポート生成とカレンダー出力まで一度に実行できます。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary():
    final_df = st.session_state.final_df
    start_date = final_df.index.min().strftime('%Y-%m-%d')
    end_date = final_df.index.max().strftime('%Y-%m-%d')
    summary_items = [
        ("解析日数", f"{len(final_df)} days"),
        ("クラスタ数", str(st.session_state.k_final)),
        ("対象地点", st.session_state.target_station),
        ("期間", f"{start_date} to {end_date}"),
    ]
    cards = "".join(
        f'<div class="status-card"><div class="status-label">{label}</div><div class="status-value">{value}</div></div>'
        for label, value in summary_items
    )
    st.markdown(f'<div class="status-grid">{cards}</div>', unsafe_allow_html=True)


def render_sidebar_controls():
    with st.sidebar:
        st.markdown("## Analysis Setup")
        st.caption("CSV と分析条件を指定してレポートを生成します。")

        uploaded_file = st.file_uploader("電力データ CSV", type="csv")
        floor_area = st.number_input("延床面積 [m2]", value=5846, min_value=1)
        target_station = st.text_input("地点名", value="神戸")

        st.markdown("### Clustering")
        auto_k = st.checkbox("クラスタ数を自動決定", value=True)
        k_input = None if auto_k else st.slider("クラスタ数 (k)", 2, 10, 4)

        run_btn = st.button("分析を実行", use_container_width=True)

    return uploaded_file, floor_area, target_station, k_input, run_btn


def render_downloads():
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Export")
    csv_data = st.session_state.final_df.to_csv(encoding='utf-8-sig')
    st.sidebar.download_button(
        label="解析結果 CSV を保存",
        data=csv_data,
        file_name=f"analysis_{st.session_state.input_filename}.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.sidebar.download_button(
        label="カレンダー PNG を保存",
        data=st.session_state.fig_cal_buf,
        file_name=f"calendar_{st.session_state.input_filename}.png",
        mime="image/png",
        use_container_width=True,
    )


def render_results():
    render_summary()
    render_downloads()

    report_tab, calendar_tab, data_tab = st.tabs(["Analysis Report", "Calendar Preview", "Merged Data"])

    with report_tab:
        st.subheader("パターン分析レポート")
        st.pyplot(st.session_state.fig_report)

    with calendar_tab:
        st.subheader("カレンダープレビュー")
        st.image(st.session_state.fig_cal_buf, use_container_width=True)

    with data_tab:
        st.subheader("結合済みデータ")
        st.dataframe(st.session_state.final_df, use_container_width=True, height=460)


def render_empty_state():
    st.markdown(
        """
        <div class="empty-state">
            <div class="hero-kicker">Ready</div>
            <h3 style="margin:0;color:#0f172a;">分析条件を設定するとここに結果が表示されます</h3>
            <p style="margin:0.9rem 0 0;color:#475569;line-height:1.7;">
                左のサイドバーで電力データ CSV、延床面積、地点名、クラスタ数の条件を指定して
                分析を実行してください。結果はレポート、カレンダー、結合データの3つのビューで確認できます。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    inject_styles()
    ensure_session_state()
    if not check_password():
        st.stop()

    render_hero()
    uploaded_file, floor_area, target_station, k_input, run_btn = render_sidebar_controls()

    if run_btn:
        if uploaded_file is None:
            st.warning("CSV ファイルをアップロードしてください")
        else:
            try:
                run_analysis(uploaded_file, floor_area, target_station, k_input)
            except Exception as exc:
                st.error(f"エラーが発生しました: {exc}")
                st.exception(exc)

    if st.session_state.analyzed:
        render_results()
    else:
        render_empty_state()


main()