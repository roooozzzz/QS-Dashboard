import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="QS Dashboard", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="css"]  { font-family: 'Roboto', sans-serif; }
    .title { font-family: 'Open Sans', sans-serif; font-size: 2.2em; font-weight: bold; }
    .stButton>button { margin-right: 10px; }
    </style>
""", unsafe_allow_html=True)

DB_PATH = "data/qs_rankings.db"

# 指标映射
INDICATORS = [
    ("Academic Reputation", "AR_SCORE", "AR_RANK"),
    ("Employer Reputation", "ER_SCORE", "ER_RANK"),
    ("Faculty Student", "FSR_SCORE", "FSR_RANK"),
    ("Citations per Faculty", "CPF_SCORE", "CPF_RANK"),
    ("International Faculty", "IFR_SCORE", "IFR_RANK"),
    ("International Students", "ISR_SCORE", "ISR_RANK"),
    ("International Students Diversity", "ISD_SCORE", "ISD_RANK"),
    ("International Research Network", "IRN_SCORE", "IRN_RANK"),
    ("Employment Outcomes", "EO_SCORE", "EO_RANK"),
    ("Sustainability", "SUS_SCORE", "SUS_RANK"),
]

@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM qs_rankings", conn)
    conn.close()
    return df

def safe_float(val):
    try:
        return float(val)
    except:
        return None

def get_avg_score(df):
    scores = df['TOTAL_SCORE'].apply(safe_float)
    scores = scores.dropna()
    if len(scores) == 0:
        return None
    return round(scores.mean(), 2)

def get_school_count(df):
    return df['NAME'].nunique()

df = load_data()
years = sorted(df['YEAR'].dropna().unique())
regions = sorted(df['REGION'].dropna().unique())
countries = sorted(df['COUNTRY'].dropna().unique())
indicator_options = [i[0] for i in INDICATORS]
_default_year = [2026] if 2026 in years else years[-1:]
_default_region = [r for r in regions if r.lower() == 'asia'] or regions[:1]
_default_country = [c for c in countries if c.lower() in ['china (mainland)', 'china mainland']] or countries[:1]

# session state for search result visibility
if 'show_search' not in st.session_state:
    st.session_state['show_search'] = False
if 'search_name' not in st.session_state:
    st.session_state['search_name'] = ''
if 'selected_year' not in st.session_state:
    st.session_state['selected_year'] = _default_year[0]
if 'selected_regions' not in st.session_state:
    st.session_state['selected_regions'] = _default_region
if 'selected_countries' not in st.session_state:
    st.session_state['selected_countries'] = _default_country
if 'selected_indicators' not in st.session_state:
    st.session_state['selected_indicators'] = indicator_options

# 左侧筛选栏
st.sidebar.title("Filters")
selected_year = st.sidebar.selectbox("Year", years, key='selected_year')
selected_regions = st.sidebar.multiselect("Region", regions, key='selected_regions')
selected_countries = st.sidebar.multiselect("Country", countries, key='selected_countries')
selected_indicators = st.sidebar.multiselect("Indicators", indicator_options, key='selected_indicators')

# 主区顶部
st.markdown('<div class="title">QS World University Rankings Dashboard</div>', unsafe_allow_html=True)
col1, col2 = st.columns([3,1])
# 自动补全建议
univ_names = sorted(df['NAME'].dropna().unique())
with col1:
    search_input = st.text_input(
        "Search University (English name)",
        value=st.session_state['search_name'],
        placeholder="Type to search...",
        help="Type part of a university name to see suggestions."
    )
    # 自动补全建议
    if search_input.strip():
        suggestions = [n for n in univ_names if search_input.lower() in n.lower()][:5]
        if suggestions:
            st.markdown(
                '<div style="color: #888; font-size: 0.95em;">Suggestions: ' + ', '.join(suggestions) + '</div>',
                unsafe_allow_html=True
            )
with col2:
    if st.button("Back to Home"):
        st.session_state['show_search'] = False
        st.session_state['search_name'] = ''
        st.session_state['selected_year'] = _default_year[0]
        st.session_state['selected_regions'] = _default_region
        st.session_state['selected_countries'] = _default_country
        st.session_state['selected_indicators'] = indicator_options
        st.experimental_rerun()

# 过滤数据
filtered = df[(df['YEAR'] == selected_year) & df['REGION'].isin(selected_regions)]
if selected_countries:
    filtered = filtered[filtered['COUNTRY'].isin(selected_countries)]

# 统计信息
school_count = get_school_count(filtered)
avg_score = get_avg_score(filtered)
st.markdown(f"**Total Universities: {school_count}** | **Average Total Score: {avg_score if avg_score is not None else 'None'}**")

# 1. 搜索功能：院校历年对比
if search_input.strip():
    search_df = df[df['NAME'].str.contains(search_input, case=False, na=False)]
    if not search_df.empty:
        st.session_state['show_search'] = True
        st.session_state['search_name'] = search_input
        st.subheader(f"Yearly Comparison: {search_df.iloc[0]['NAME']}")
        compare_cols = [
            "YEAR", "RANK", "TOTAL_SCORE"
        ]
        for ind, score_col, rank_col in INDICATORS:
            compare_cols += [score_col, rank_col]
        compare_df = search_df[compare_cols].sort_values("YEAR")
        compare_df = compare_df.rename(columns={
            "RANK": "Rank", "TOTAL_SCORE": "Total Score",
            **{score: f"{ind} Score" for ind, score, _ in INDICATORS},
            **{rank: f"{ind} Rank" for ind, _, rank in INDICATORS},
        })
        compare_df = compare_df.set_index("YEAR")
        close_col1, close_col2 = st.columns([8,1])
        with close_col2:
            if st.button("Hide"):
                st.session_state['show_search'] = False
                st.session_state['search_name'] = ''
        st.dataframe(compare_df)
    else:
        st.info("No university found.")
        st.session_state['show_search'] = False
        st.session_state['search_name'] = ''

# 2. 筛选功能：主表格
st.subheader("Filtered Results")
main_cols = ["RANK", "NAME", "COUNTRY", "YEAR", "TOTAL_SCORE"]
for ind, score_col, rank_col in INDICATORS:
    if ind in selected_indicators:
        main_cols += [score_col, rank_col]
# 排序：按 RANK 升序
show_df = filtered[main_cols].copy()
# RANK 可能为字符串，需转为数字排序
show_df["RANK_SORT"] = pd.to_numeric(show_df["RANK"], errors="coerce")
show_df = show_df.sort_values(["YEAR", "RANK_SORT"]).drop(columns=["RANK_SORT"])
# 表头美化
col_rename = {
    "RANK": "Rank", "NAME": "Name", "COUNTRY": "Country", "YEAR": "Year", "TOTAL_SCORE": "Total Score"
}
for ind, score_col, rank_col in INDICATORS:
    col_rename[score_col] = f"{ind} Score"
    col_rename[rank_col] = f"{ind} Rank"
show_df = show_df.rename(columns=col_rename)
show_df = show_df.replace({None: "None", "": "None"})
show_df = show_df.reset_index(drop=True)
show_df.index = show_df.index + 1  # 序号从1开始
st.dataframe(show_df, use_container_width=True) 