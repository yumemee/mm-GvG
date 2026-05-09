import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- ページ設定 & デザイン ---
st.set_page_config(page_title="GvG Analytics Dashboard", layout="wide")

# ダークモード用のカスタムCSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4455; }
    div[data-testid="stExpander"] { border: none; background-color: #1e2130; }
    .stDataFrame { border: 1px solid #3d4455; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data():
    log_url = "https://api.tamamo.dev/GvGLog?Group=19&Class=3&Block=1&Week=Sat"
    castle_url = "https://tamamo.dev/assets/Resource/CastleId.json"
    
    try:
        # API実行
        log_res = requests.get(log_url).json()
        castle_res = requests.get(castle_url).json()
        
        # 階層構造から実際のログ部分(Log)を抽出
        # 今回のエラー原因：log_res['data']['Log'] にデータが入っていた
        if isinstance(log_res, dict) and 'data' in log_res and 'Log' in log_res['data']:
            log_data = log_res['data']['Log']
        else:
            st.warning("⚠️ APIのデータ構造が想定と異なります。")
            return pd.DataFrame()

        df = pd.DataFrame(log_data)
        
        # 城データのマッピング (CastleID -> Name)
        # API側のキーが 'CastleID' (大文字ID) なので修正
        castle_map = {item['Id']: item['Name'] for item in castle_res}
        if 'CastleID' in df.columns:
            df['CastleName'] = df['CastleID'].map(castle_map).fillna("Unknown")
        
        return df
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {e}")
        return pd.DataFrame()

# --- メインコンテンツ ---
st.title("🛡️ GvG Strategy Dashboard")
st.caption("Real-time Guild vs Guild Analytics | Elite Class")
st.markdown("---")

df = load_data()

if not df.empty:
    # 今回のデータにはGuildNameが含まれていない可能性があるため、CastleIDベースで表示
    st.markdown("### 📊 Castle Status Analysis")

    # --- 上段：メトリクスカード ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Castles", len(df))
    with col2:
        # None以外のデータがあるかカウント（簡易的な活動チェック）
        active_count = df['DefenseTime'].count() if 'DefenseTime' in df.columns else 0
        st.metric("Active Status", active_count)
    with col3:
        st.metric("Status", "Online")

    # --- 中段：チャートエリア ---
    left_chart, right_chart = st.columns(2)

    with left_chart:
        # 城ごとのステータスを可視化（棒グラフ）
        if 'CastleName' in df.columns:
            fig_bar = px.bar(
                df, x='CastleName', y='CastleID',
                title="Castle Overview",
                template="plotly_dark",
                color='CastleID'
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with right_chart:
        # 城の分布
        if 'CastleName' in df.columns:
            fig_pie = px.pie(
                df, names='CastleName', 
                title="Castle Distribution",
                template="plotly_dark",
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- 下段：データ詳細 ---
    st.markdown("### 📋 Detailed Logs")
    with st.expander("Click to view full data table"):
        st.dataframe(df, use_container_width=True)

else:
    st.info("💡 現在表示できるデータがありません（すべての値が空の可能性があります）。")
    if st.button("Retry Connection"):
        st.cache_data.clear()
        st.rerun()
