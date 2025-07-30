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
if 'current_mode' not in st.session_state:
    st.session_state['current_mode'] = '筛选模式'
if 'compare_schools' not in st.session_state:
    st.session_state['compare_schools'] = ['', '', '', '']
if 'compare_year' not in st.session_state:
    st.session_state['compare_year'] = _default_year[0]
if 'benchmark_school' not in st.session_state:
    st.session_state['benchmark_school'] = ''
if 'benchmark_year' not in st.session_state:
    st.session_state['benchmark_year'] = _default_year[0]
if 'benchmark_range' not in st.session_state:
    st.session_state['benchmark_range'] = 30

# 主区顶部
st.markdown('<div class="title">QS World University Rankings Dashboard</div>', unsafe_allow_html=True)

# 自动补全建议
univ_names = sorted(df['NAME'].dropna().unique())

# 模式切换器
mode = st.radio(
    "选择功能模式:",
    ["筛选模式", "搜索模式", "对比模式", "对标模式"],
    horizontal=True,
    key='current_mode'
)

# 根据模式显示不同内容
if mode == "筛选模式":
    # 筛选模式 - 显示筛选栏、搜索框和筛选结果
    
    # 筛选栏（在主界面显示）
    st.subheader("筛选条件")
    col1, col2, col3, col4 = st.columns(4)
with col1:
        selected_year = st.selectbox("Year", years, key='selected_year')
with col2:
        selected_regions = st.multiselect("Region", regions, key='selected_regions')
    with col3:
        selected_countries = st.multiselect("Country", countries, key='selected_countries')
    with col4:
        selected_indicators = st.multiselect("Indicators", indicator_options, key='selected_indicators')

# 过滤数据
filtered = df[(df['YEAR'] == selected_year) & df['REGION'].isin(selected_regions)]
if selected_countries:
    filtered = filtered[filtered['COUNTRY'].isin(selected_countries)]

# 统计信息
school_count = get_school_count(filtered)
avg_score = get_avg_score(filtered)
st.markdown(f"**Total Universities: {school_count}** | **Average Total Score: {avg_score if avg_score is not None else 'None'}**")

    # 筛选功能：主表格
st.subheader("Filtered Results")

# 显示模式选择器
display_mode = st.radio(
    "Display Mode:",
    ["Score", "Rank", "Both"],
    horizontal=True,
    index=0  # 默认选择 Score
)

# 根据显示模式选择列
main_cols = ["RANK", "NAME", "COUNTRY", "YEAR", "TOTAL_SCORE"]
for ind, score_col, rank_col in INDICATORS:
    if ind in selected_indicators:
        if display_mode == "Score":
            main_cols += [score_col]
        elif display_mode == "Rank":
            main_cols += [rank_col]
        else:  # Both
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
    if ind in selected_indicators:
        if display_mode == "Score":
            col_rename[score_col] = f"{ind} Score"
        elif display_mode == "Rank":
            col_rename[rank_col] = f"{ind} Rank"
        else:  # Both
            col_rename[score_col] = f"{ind} Score"
            col_rename[rank_col] = f"{ind} Rank"

show_df = show_df.rename(columns=col_rename)
show_df = show_df.replace({None: "None", "": "None"})
show_df = show_df.reset_index(drop=True)
show_df.index = show_df.index + 1  # 序号从1开始

    # 显示表格
    st.dataframe(show_df, use_container_width=True)

elif mode == "搜索模式":
    # 搜索模式 - 专门用于搜索单个学校的历年对比
    st.subheader("高校历年对比")
    
    search_input = st.text_input(
        "Search University (English name)",
        value=st.session_state['search_name'],
        placeholder="请输入学校英文全名并回车",
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
    
    # 搜索功能：院校历年对比
    if search_input.strip():
        search_df = df[df['NAME'].str.contains(search_input, case=False, na=False)]
        if not search_df.empty:
            st.session_state['show_search'] = True
            st.session_state['search_name'] = search_input
            st.subheader(f"{search_df.iloc[0]['NAME']}")
            
            # 显示模式选择器
            display_mode = st.radio(
                "Display Mode:",
                ["Score", "Rank", "Both"],
                horizontal=True,
                index=0  # 默认选择 Score
            )

            # 根据显示模式选择列
            compare_cols = ["YEAR", "RANK", "TOTAL_SCORE"]
            for ind, score_col, rank_col in INDICATORS:
                if display_mode == "Score":
                    compare_cols += [score_col]
                elif display_mode == "Rank":
                    compare_cols += [rank_col]
                else:  # Both
                    compare_cols += [score_col, rank_col]

            compare_df = search_df[compare_cols].sort_values("YEAR")
            compare_df = compare_df.rename(columns={
                "RANK": "Rank", "TOTAL_SCORE": "Total Score",
                **{score: f"{ind} Score" for ind, score, _ in INDICATORS},
                **{rank: f"{ind} Rank" for ind, _, rank in INDICATORS},
            })
            compare_df = compare_df.set_index("YEAR")
            st.dataframe(compare_df)
        else:
            st.info("No university found.")
            st.session_state['show_search'] = False
            st.session_state['search_name'] = ''

elif mode == "对比模式":
    # 对比模式 - 选择年份和多个学校进行对比
    st.subheader("高校间对比")
    
    # 年份选择
    compare_year = st.selectbox("选择年份", years, key='compare_year')
    
    # 学校输入框
    col1, col2 = st.columns(2)
    
    with col1:
        school1 = st.text_input("University 1", value=st.session_state['compare_schools'][0], placeholder="请输入学校英文全名并回车", key='school1', label_visibility="collapsed")
        st.markdown('<p style="color: #666666; font-size: 0.9em; margin-top: -10px;">University 1</p>', unsafe_allow_html=True)
        school2 = st.text_input("University 2", value=st.session_state['compare_schools'][1], placeholder="请输入学校英文全名并回车", key='school2', label_visibility="collapsed")
        st.markdown('<p style="color: #666666; font-size: 0.9em; margin-top: -10px;">University 2</p>', unsafe_allow_html=True)
    
    with col2:
        school3 = st.text_input("University 3", value=st.session_state['compare_schools'][2], placeholder="请输入学校英文全名并回车", key='school3', label_visibility="collapsed")
        st.markdown('<p style="color: #666666; font-size: 0.9em; margin-top: -10px;">University 3</p>', unsafe_allow_html=True)
        school4 = st.text_input("University 4", value=st.session_state['compare_schools'][3], placeholder="请输入学校英文全名并回车", key='school4', label_visibility="collapsed")
        st.markdown('<p style="color: #666666; font-size: 0.9em; margin-top: -10px;">University 4</p>', unsafe_allow_html=True)
    
    # 更新session state
    st.session_state['compare_schools'] = [school1, school2, school3, school4]
    
    # 开始对比
    if any([school1, school2, school3, school4]):
        schools_to_compare = [s for s in [school1, school2, school3, school4] if s.strip()]
        
        if schools_to_compare:
            # 获取对比数据
            compare_data = []
            for school in schools_to_compare:
                school_data = df[(df['NAME'].str.contains(school, case=False, na=False)) & (df['YEAR'] == compare_year)]
                if not school_data.empty:
                    # 取第一个匹配的学校
                    school_row = school_data.iloc[0]
                    compare_data.append({
                        'School': school_row['NAME'],
                        'Rank': school_row['RANK'],
                        'Total Score': school_row['TOTAL_SCORE']
                    })
                    
                    # 添加各指标数据
                    for ind, score_col, rank_col in INDICATORS:
                        compare_data[-1][f'{ind} Score'] = school_row[score_col]
                        compare_data[-1][f'{ind} Rank'] = school_row[rank_col]
                else:
                    compare_data.append({
                        'School': school,
                        'Rank': 'N/A',
                        'Total Score': 'N/A'
                    })
                    # 添加各指标数据
                    for ind, score_col, rank_col in INDICATORS:
                        compare_data[-1][f'{ind} Score'] = 'N/A'
                        compare_data[-1][f'{ind} Rank'] = 'N/A'
            
            if compare_data:
                # 创建对比表格
                compare_df = pd.DataFrame(compare_data)
                compare_df = compare_df.set_index('School')
                
                # 显示对比表格
                st.subheader(f"对比结果 ({compare_year}年)")
                st.dataframe(compare_df, use_container_width=True)
            else:
                st.info("未找到匹配的学校数据")
        else:
            st.info("请输入至少一个学校名称")
    else:
        pass

elif mode == "对标模式":
    # 对标模式 - 高校与竞争对手的指标对比分析
    st.subheader("对标分析")
    
    # 年份选择
    benchmark_year = st.selectbox("选择年份", years, key='benchmark_year')
    
    # 目标高校选择
    target_school = st.text_input(
        "目标高校",
        value=st.session_state['benchmark_school'],
        placeholder="请输入学校英文全名并回车",
        key='benchmark_school_input'
    )
    
    # 对比组选择
    benchmark_group = st.selectbox(
        "对比组类型", 
        ["排名前N名", "同国家高校"], 
        key='benchmark_group'
    )
    
    if benchmark_group == "排名前N名":
        benchmark_range = st.selectbox("对比范围", [10, 20, 30, 50], key='benchmark_range')
    else:  # 同国家高校
        benchmark_range = st.selectbox("对比范围", ["整体", "前100", "前200", "前300"], key='benchmark_range_country')
    
    # 更新session state
    st.session_state['benchmark_school'] = target_school
    
    if target_school.strip():
        # 查找目标高校
        target_data = df[(df['NAME'].str.contains(target_school, case=False, na=False)) & (df['YEAR'] == benchmark_year)]
        
        if not target_data.empty:
            target_row = target_data.iloc[0]
            target_rank = int(target_row['RANK'])
            
            st.success(f"✅ 找到目标高校: {target_row['NAME']} (排名: {target_rank}, 国家: {target_row['COUNTRY']})")
            
            # 根据对比组类型选择对比数据
            if benchmark_group == "排名前N名":
                # 计算对比范围
                start_rank = max(1, target_rank - benchmark_range)
                end_rank = target_rank - 1
                
                st.info(f"对比范围: 排名 {start_rank} - {end_rank}")
                
                if end_rank >= start_rank:
                    # 获取前N名高校数据 - 先将RANK转换为数值类型
                    df_filtered = df[df['YEAR'] == benchmark_year].copy()
                    df_filtered['RANK_NUMERIC'] = pd.to_numeric(df_filtered['RANK'], errors='coerce')
                    
                    # 过滤掉无效的排名数据
                    df_filtered = df_filtered.dropna(subset=['RANK_NUMERIC'])
                    
                    top_schools = df_filtered[(df_filtered['RANK_NUMERIC'] >= start_rank) & (df_filtered['RANK_NUMERIC'] <= end_rank)]
                    
                    st.info(f"找到 {len(top_schools)} 所高校在对比范围内")
                else:
                    top_schools = pd.DataFrame()  # 空DataFrame
                    
            else:  # 同国家高校
                target_country = target_row['COUNTRY']
                st.info(f"对比范围: 同国家高校 ({target_country})")
                
                # 获取同国家高校数据
                df_filtered = df[(df['YEAR'] == benchmark_year) & (df['COUNTRY'] == target_country)].copy()
                df_filtered['RANK_NUMERIC'] = pd.to_numeric(df_filtered['RANK'], errors='coerce')
                df_filtered = df_filtered.dropna(subset=['RANK_NUMERIC'])
                
                if benchmark_range == "整体":
                    top_schools = df_filtered
                    st.info(f"找到 {len(top_schools)} 所同国家高校")
                else:
                    # 解析排名范围
                    rank_limit = int(benchmark_range.replace("前", ""))
                    top_schools = df_filtered[df_filtered['RANK_NUMERIC'] <= rank_limit]
                    st.info(f"找到 {len(top_schools)} 所同国家高校 (排名前{rank_limit})")
            
            if not top_schools.empty:
                    # 准备图表数据
                    import plotly.graph_objects as go
                    import plotly.express as px
                    
                    # 指标名称映射
                    indicator_names = {
                        'ACADEMIC_REPUTATION': '学术声誉',
                        'EMPLOYER_REPUTATION': '雇主声誉', 
                        'FACULTY_STUDENT_RATIO': '师生比',
                        'CITATIONS_PER_FACULTY': '师均引用',
                        'INTERNATIONAL_FACULTY_RATIO': '国际教师比例',
                        'INTERNATIONAL_STUDENTS_RATIO': '国际学生比例',
                        'INTERNATIONAL_RESEARCH_NETWORK': '国际研究网络',
                        'EMPLOYMENT_OUTCOMES': '就业成果',
                        'SUSTAINABILITY': '可持续性',
                        'OVERALL_SCORE': '综合得分'
                    }
                    
                    # 准备数据
                    indicators = []
                    target_scores = []
                    avg_scores = []
                    max_scores = []
                    
                    for ind, score_col, rank_col in INDICATORS:
                        indicators.append(indicator_names.get(score_col, ind))
                        # 确保目标高校得分是数值类型
                        target_score = pd.to_numeric(target_row[score_col], errors='coerce')
                        target_scores.append(target_score if not pd.isna(target_score) else 0)
                        
                        # 计算前N名的平均分和最高分
                        valid_scores = top_schools[score_col].dropna()
                        if not valid_scores.empty:
                            # 确保数据类型为数值
                            numeric_scores = pd.to_numeric(valid_scores, errors='coerce').dropna()
                            if not numeric_scores.empty:
                                avg_scores.append(numeric_scores.mean())
                                max_scores.append(numeric_scores.max())
                            else:
                                avg_scores.append(0)
                                max_scores.append(0)
                        else:
                            avg_scores.append(0)
                            max_scores.append(0)
                    
                    # 创建折线图
                    fig = go.Figure()
                    
                    # 目标高校得分
                    fig.add_trace(go.Scatter(
                        x=indicators,
                        y=target_scores,
                        mode='lines+markers',
                        name=f'{target_row["NAME"]}',
                        line=dict(color='#1f77b4', width=3),
                        marker=dict(size=8)
                    ))
                    
                    # 前N名平均分
                    fig.add_trace(go.Scatter(
                        x=indicators,
                        y=avg_scores,
                        mode='lines+markers',
                        name=f'前{benchmark_range}名平均分',
                        line=dict(color='#2ca02c', width=2),
                        marker=dict(size=6)
                    ))
                    
                    # 前N名最高分
                    fig.add_trace(go.Scatter(
                        x=indicators,
                        y=max_scores,
                        mode='lines+markers',
                        name=f'前{benchmark_range}名最高分',
                        line=dict(color='#ff7f0e', width=2),
                        marker=dict(size=6)
                    ))
                    
                    # 更新布局
                    fig.update_layout(
                        title=f'{target_row["NAME"]} vs 前{benchmark_range}名高校指标对比 ({benchmark_year}年)',
                        xaxis_title='指标',
                        yaxis_title='得分',
                        height=500,
                        showlegend=True,
                        hovermode='x unified'
                    )
                    
                    # 显示图表
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 显示数据表格
                    st.subheader("详细数据对比")
                    comparison_data = {
                        '指标': indicators,
                        f'{target_row["NAME"]}': target_scores,
                        f'前{benchmark_range}名平均分': [round(x, 2) for x in avg_scores],
                        f'前{benchmark_range}名最高分': [round(x, 2) for x in max_scores]
                    }
                    comparison_df = pd.DataFrame(comparison_data)
                    st.dataframe(comparison_df, use_container_width=True)
                    
                    # 优势劣势分析
                    st.subheader("优势劣势分析")
                    advantages = []
                    disadvantages = []
                    
                    for i, (indicator, target_score, avg_score) in enumerate(zip(indicators, target_scores, avg_scores)):
                        if target_score > avg_score:
                            advantages.append(f"✅ {indicator}: {target_score:.1f} > {avg_score:.1f}")
                        else:
                            disadvantages.append(f"❌ {indicator}: {target_score:.1f} < {avg_score:.1f}")
                    
                    col1, col2 = st.columns(2)
with col1:
                        st.markdown("**优势指标:**")
                        for adv in advantages[:5]:  # 显示前5个优势
                            st.write(adv)
                    
                    with col2:
                        st.markdown("**劣势指标:**")
                        for dis in disadvantages[:5]:  # 显示前5个劣势
                            st.write(dis)
                    
                else:
                    st.warning(f"⚠️ 在排名 {start_rank}-{end_rank} 范围内没有找到高校数据")
            else:
                st.warning(f"⚠️ 目标高校排名 {target_rank} 过低，无法进行对标分析")
        else:
            st.error("❌ 未找到目标高校，请检查学校名称")
    else:
        st.info("请输入目标高校名称开始对标分析") 