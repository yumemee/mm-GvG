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

@st.cache_data(ttl=600)  # 10分間キャッシュ
def load_data():
    log_url = "https://api.tamamo.dev/GvGLog?Group=19&Class=3&Block=1&Week=Sat"
    castle_url = "https://tamamo.dev/assets/Resource/CastleId.json"
    
    try:
        # API実行
        log_res = requests.get(log_url).json()
        castle_res = requests.get(castle_url).json()
        
        # データ形式のチェック（リストでない場合はエラー表示）
        if not isinstance(log_res, list):
            st.warning(f"⚠️ APIデータがリスト形式ではありません。応答内容: {log_res}")
            return pd.DataFrame()

        df = pd.DataFrame(log_res)
        
        # 城データのマッピング
        castle_map = {str(item['Id']): item['Name'] for item in castle_res}
        if 'CastleId' in df.columns:
            df['CastleName'] = df['CastleId'].astype(str).map(castle_map).fillna("Unknown")
        
        return df
    except Exception as e:
        st.error(f"❌ データの読み込み中にエラーが発生しました: {e}")
        return pd.DataFrame()

# --- メインコンテンツ ---
st.title("🛡️ GvG Strategy Dashboard")
st.caption("Real-time Guild vs Guild Analytics | Elite Class")
st.markdown("---")

df = load_data()

if not df.empty:
    # --- サイドバー フィルター ---
    st.sidebar.header("Filter Settings")
    all_guilds = sorted(df['GuildName'].unique())
    selected_guilds = st.sidebar.multiselect(
        "Select Guilds to Display", 
        options=all_guilds,
        default=all_guilds[:10] if len(all_guilds) > 10 else all_guilds
    )
    
    # フィルタリング
    filtered_df = df[df['GuildName'].isin(selected_guilds)]

    # --- 上段：メトリクスカード ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Logs", len(filtered_df))
    with col2:
        st.metric("Active Guilds", len(selected_guilds))
    with col3:
        st.metric("Castles Held", filtered_df['CastleId'].nunique())
    with col4:
        st.metric("Status", "Online", delta="Connected")

    st.markdown("### 📊 Activity Analysis")

    # --- 中段：チャートエリア ---
    left_chart, right_chart = st.columns([3, 2])

    with left_chart:
        # ギルドごとの活動ログ数
        guild_counts = filtered_df['GuildName'].value_counts().reset_index()
        guild_counts.columns = ['GuildName', 'Logs']
        fig_bar = px.bar(
            guild_counts,
            x='Logs', y='GuildName', orientation='h',
            title="Logs per Guild",
            template="plotly_dark",
            color='Logs',
            color_continuous_scale='Blues'
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

    with right_chart:
        # 城の占有分布
        if 'CastleName' in filtered_df.columns:
            fig_pie = px.pie(
                filtered_df, names='CastleName', 
                title="Castle Possession Distribution",
                template="plotly_dark",
                hole=0.5
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- 下段：データ詳細 ---
    st.markdown("### 📋 Raw Data")
    with st.expander("Click to view full logs"):
        st.dataframe(
            filtered_df[['GuildName', 'CastleName', 'CastleId']], 
            use_container_width=True
        )

else:
    st.info("💡 表示するデータがありません。APIの稼働状況を確認してください。")
    if st.button("Retry Connection"):
        st.cache_data.clear()
        st.rerun()
