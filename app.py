import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests


# --- ページ設定 & デザイン ---
st.set_page_config(page_title="GvG Analytics Dashboard", layout="wide")

# ダークモード用のカスタムCSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3d4455; }
    div[data-testid="stExpander"] { border: none; background-color: #1e2130; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_data():
    # データの取得
    log_url = "https://api.tamamo.dev/GvGLog?Group=19&Class=3&Block=1&Week=Sat"
    castle_url = "https://tamamo.dev/assets/Resource/CastleId.json"
    
    log_res = requests.get(log_url).json()
    castle_res = requests.get(castle_url).json()
    
    df = pd.DataFrame(log_res)
    # CastleIdを名称にマッピング
    castle_map = {str(item['Id']): item['Name'] for item in castle_res}
    df['CastleName'] = df['CastleId'].astype(str).map(castle_map)
    
    return df

# --- ヘッダー ---
st.title("🛡️ GvG Strategy Dashboard")
st.markdown("---")

try:
    df = load_data()

    # --- サイドバー フィルター ---
    st.sidebar.header("Filter Settings")
    selected_guild = st.sidebar.multiselect(
        "Select Guilds", 
        options=df['GuildName'].unique(),
        default=df['GuildName'].unique()[:5]
    )
    
    filtered_df = df[df['GuildName'].isin(selected_guild)]

    # --- 上段：メトリクスカード ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", len(filtered_df))
    with col2:
        st.metric("Unique Guilds", df['GuildName'].nunique())
    with col3:
        st.metric("Active Castles", filtered_df['CastleId'].nunique())
    with col4:
        st.metric("Class Level", "Elite (3)")

    st.markdown("### Analysis")

    # --- 中段：チャートエリア ---
    left_chart, right_chart = st.columns(2)

    with left_chart:
        # ギルドごとのスコア/活動量
        fig_bar = px.bar(
            filtered_df.groupby('GuildName').size().reset_index(name='Count'),
            x='Count', y='GuildName', orientation='h',
            title="Activity by Guild",
            template="plotly_dark",
            color_discrete_sequence=['#636EFA']
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with right_chart:
        # 城ごとの分布
        fig_pie = px.pie(
            filtered_df, names='CastleName', 
            title="Castle Distribution",
            template="plotly_dark",
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- 下段：データ詳細 ---
    with st.expander("📝 View Raw Data"):
        st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"データの読み込みに失敗しました: {e}")
