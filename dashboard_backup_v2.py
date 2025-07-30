import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import os

# Page configuration
st.set_page_config(
    page_title="QS World University Rankings Dashboard",
    page_icon="🎓",
    layout="wide"
)

# Title
st.title("🎓 QS World University Rankings Dashboard")

# Data loading
@st.cache_data
def load_data():
    # Check if database file exists
    db_path = "data/qs_rankings.db"
    if not os.path.exists(db_path):
        st.error("Database file not found. Please run the import script first.")
        return pd.DataFrame()
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    # Read data
    df = pd.read_sql_query("SELECT * FROM qs_rankings", conn)
    conn.close()
    
    return df

def safe_float(val):
    try:
        return float(val) if val is not None and val != '' else None
    except (ValueError, TypeError):
        return None

def get_avg_score(df):
    scores = df['TOTAL_SCORE'].apply(safe_float)
    valid_scores = scores.dropna()
    return round(valid_scores.mean(), 2) if not valid_scores.empty else None

def get_school_count(df):
    return len(df)

# Load data
df = load_data()

if df.empty:
    st.stop()

# Data preprocessing
df['TOTAL_SCORE'] = df['TOTAL_SCORE'].apply(safe_float)

# Indicator definitions
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
    ("Sustainability", "SUS_SCORE", "SUS_RANK")
]

# Get option data
years = sorted(df['YEAR'].unique())
regions = sorted(df['REGION'].dropna().unique())
countries = sorted(df['COUNTRY'].dropna().unique())
indicator_options = [ind[0] for ind in INDICATORS]

# Set default values
_default_year = years[-1] if years else 2024
_default_regions = ['Asia'] if 'Asia' in regions else regions[:1]
_default_countries = ['China (Mainland)'] if 'China (Mainland)' in countries else countries[:1]
_default_indicators = indicator_options  # Default to all indicators

# Initialize session state
if 'search_name' not in st.session_state:
    st.session_state['search_name'] = ""
if 'show_search' not in st.session_state:
    st.session_state['show_search'] = False
if 'current_mode' not in st.session_state:
    st.session_state['current_mode'] = 'Filter Mode'
if 'compare_schools' not in st.session_state:
    st.session_state['compare_schools'] = ['', '', '', '']
if 'compare_year' not in st.session_state:
    st.session_state['compare_year'] = years[-1] if years else 2024

# Auto-complete suggestions
univ_names = sorted(df['NAME'].dropna().unique())

# Mode switcher
mode = st.radio(
    "Select Function Mode:",
    ["Filter Mode", "Search Mode", "Compare Mode"],
    horizontal=True,
    key='current_mode'
)

# Display different content based on mode
if mode == "Filter Mode":
    # Filter mode - display filter bar, search box and filtered results
    
    # Filter bar (displayed in main interface)
    st.subheader("Filter Criteria")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_year = st.selectbox("Year", years, index=len(years)-1, key='selected_year')
    with col2:
        selected_regions = st.multiselect("Region", regions, default=_default_regions, key='selected_regions')
    with col3:
        selected_countries = st.multiselect("Country", countries, default=_default_countries, key='selected_countries')
    with col4:
        selected_indicators = st.multiselect("Indicators", indicator_options, default=_default_indicators, key='selected_indicators')

    # Filter data
    filtered = df[(df['YEAR'] == selected_year) & df['REGION'].isin(selected_regions)]
    if selected_countries:
        filtered = filtered[filtered['COUNTRY'].isin(selected_countries)]

    # Statistics
    school_count = get_school_count(filtered)
    avg_score = get_avg_score(filtered)
    st.markdown(f"**Total Universities: {school_count}** | **Average Total Score: {avg_score if avg_score is not None else 'None'}**")

    # Filter function: main table
    st.subheader("Filtered Results")

    # Display mode selector
    display_mode = st.radio(
        "Display Mode:",
        ["Score", "Rank", "Both"],
        horizontal=True,
        index=0  # Default to Score
    )

    # Select columns based on display mode
    main_cols = ["RANK", "NAME", "COUNTRY", "YEAR", "TOTAL_SCORE"]
    for ind, score_col, rank_col in INDICATORS:
        if ind in selected_indicators:
            if display_mode == "Score":
                main_cols += [score_col]
            elif display_mode == "Rank":
                main_cols += [rank_col]
            else:  # Both
                main_cols += [score_col, rank_col]

    # Sort: by RANK ascending
    show_df = filtered[main_cols].copy()
    # RANK might be string, need to convert to numeric for sorting
    show_df["RANK_SORT"] = pd.to_numeric(show_df["RANK"], errors="coerce")
    show_df = show_df.sort_values(["YEAR", "RANK_SORT"]).drop(columns=["RANK_SORT"])

    # Column header beautification
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
    show_df.index = show_df.index + 1  # Index starts from 1

    # Display table
    st.dataframe(show_df, use_container_width=True)

elif mode == "Search Mode":
    # Search mode - specifically for searching individual university's yearly comparison
    st.subheader("University Yearly Comparison")
    
    search_input = st.text_input(
        "Search University (English name)",
        value=st.session_state['search_name'],
        placeholder="Enter university English name and press Enter",
        help="Type part of a university name to see suggestions."
    )
    
    # Auto-complete suggestions
    if search_input.strip():
        suggestions = [n for n in univ_names if search_input.lower() in n.lower()][:5]
        if suggestions:
            st.markdown(
                '<div style="color: #888; font-size: 0.95em;">Suggestions: ' + ', '.join(suggestions) + '</div>',
                unsafe_allow_html=True
            )
    
    # Search function: university yearly comparison
    if search_input.strip():
        search_df = df[df['NAME'].str.contains(search_input, case=False, na=False)]
        if not search_df.empty:
            st.session_state['show_search'] = True
            st.session_state['search_name'] = search_input
            st.subheader(f"{search_df.iloc[0]['NAME']}")
            
            # Display mode selector
            display_mode = st.radio(
                "Display Mode:",
                ["Score", "Rank", "Both"],
                horizontal=True,
                index=0
            )
            
            # Prepare data
            school_data = search_df.sort_values('YEAR', ascending=False)
            
            # Select columns based on display mode
            display_cols = ["YEAR", "RANK", "TOTAL_SCORE"]
            for ind, score_col, rank_col in INDICATORS:
                if display_mode == "Score":
                    display_cols += [score_col]
                elif display_mode == "Rank":
                    display_cols += [rank_col]
                else:  # Both
                    display_cols += [score_col, rank_col]
            
            # Display data
            display_df = school_data[display_cols].copy()
            
            # Column header beautification
            col_rename = {"YEAR": "Year", "RANK": "Rank", "TOTAL_SCORE": "Total Score"}
            for ind, score_col, rank_col in INDICATORS:
                if display_mode == "Score":
                    col_rename[score_col] = f"{ind} Score"
                elif display_mode == "Rank":
                    col_rename[rank_col] = f"{ind} Rank"
                else:  # Both
                    col_rename[score_col] = f"{ind} Score"
                    col_rename[rank_col] = f"{ind} Rank"
            
            display_df = display_df.rename(columns=col_rename)
            display_df = display_df.replace({None: "None", "": "None"})
            display_df = display_df.reset_index(drop=True)
            display_df.index = display_df.index + 1
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("❌ No matching universities found")

elif mode == "Compare Mode":
    # Compare mode - multiple universities' indicator comparison in specific year
    st.subheader("University Comparison")
    
    # Year selection
    compare_year = st.selectbox("Select Comparison Year", years, index=len(years)-1, key='compare_year')
    
    # University input boxes
    st.markdown('<div style="margin-bottom: 10px;"></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        school1 = st.text_input("University 1", value=st.session_state['compare_schools'][0], 
                               placeholder="Enter university English name and press Enter", key='school1')
        school3 = st.text_input("University 3", value=st.session_state['compare_schools'][2], 
                               placeholder="Enter university English name and press Enter", key='school3')
    with col2:
        school2 = st.text_input("University 2", value=st.session_state['compare_schools'][1], 
                               placeholder="Enter university English name and press Enter", key='school2')
        school4 = st.text_input("University 4", value=st.session_state['compare_schools'][3], 
                               placeholder="Enter university English name and press Enter", key='school4')
    
    # Update session state
    st.session_state['compare_schools'] = [school1, school2, school3, school4]
    
    # Comparison analysis
    schools_to_compare = [s for s in [school1, school2, school3, school4] if s.strip()]
    
    if schools_to_compare:
        # Get data for all universities
        all_school_data = []
        found_schools = []
        
        for school in schools_to_compare:
            school_data = df[(df['YEAR'] == compare_year) & 
                           (df['NAME'].str.contains(school, case=False, na=False))]
            if not school_data.empty:
                all_school_data.append(school_data.iloc[0])
                found_schools.append(school_data.iloc[0]['NAME'])
        
        if all_school_data:
            # Create comparison table
            comparison_df = pd.DataFrame(all_school_data)
            
            # Select columns to display
            display_cols = ["NAME", "RANK", "TOTAL_SCORE"]
            for ind, score_col, rank_col in INDICATORS:
                display_cols += [score_col]
            
            # Prepare display data
            show_comparison = comparison_df[display_cols].copy()
            
            # Column header beautification
            col_rename = {"NAME": "University", "RANK": "Rank", "TOTAL_SCORE": "Total Score"}
            for ind, score_col, rank_col in INDICATORS:
                col_rename[score_col] = f"{ind} Score"
            
            show_comparison = show_comparison.rename(columns=col_rename)
            show_comparison = show_comparison.replace({None: "None", "": "None"})
            show_comparison = show_comparison.reset_index(drop=True)
            show_comparison.index = show_comparison.index + 1
            
            st.dataframe(show_comparison, use_container_width=True)
            
            # Create line chart for score comparison
            st.subheader("Score Comparison Chart")
            
            # Prepare data for the chart
            chart_data = []
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Different colors for each university
            
            for idx, (_, row) in enumerate(comparison_df.iterrows()):
                university_name = row['NAME']
                scores = []
                indicators = []
                
                for ind, score_col, _ in INDICATORS:
                    score = safe_float(row[score_col])
                    if score is not None:
                        scores.append(score)
                        indicators.append(ind)
                    else:
                        scores.append(0)
                        indicators.append(ind)
                
                chart_data.append({
                    'university': university_name,
                    'scores': scores,
                    'indicators': indicators,
                    'color': colors[idx % len(colors)]
                })
            
            # Create the line chart
            fig = go.Figure()
            
            for data in chart_data:
                fig.add_trace(go.Scatter(
                    x=data['indicators'],
                    y=data['scores'],
                    mode='lines+markers',
                    name=data['university'],
                    line=dict(color=data['color'], width=3),
                    marker=dict(size=8)
                ))
            
            # Update layout
            fig.update_layout(
                title=f"University Score Comparison ({compare_year})",
                xaxis_title="Indicators",
                yaxis_title="Score",
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Download button
            if st.button("📊 Download", key='download_compare'):
                output = f"university_comparison_{compare_year}.xlsx"
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    show_comparison.to_excel(writer, sheet_name='Comparison', index=False)
                st.success(f"✅ Data downloaded to {output}")
        else:
            st.warning("❌ No matching universities found") 