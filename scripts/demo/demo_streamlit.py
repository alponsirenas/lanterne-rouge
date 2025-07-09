#!/usr/bin/env python3
"""
Lanterne Rouge Streamlit Demo

A web-based GUI demo for the Lanterne Rouge system using Streamlit.
This provides the same functionality as the CLI demo but with a modern web interface.

Usage:
    streamlit run scripts/demo_streamlit.py
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import date, datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.demo_enhanced import SCENARIOS, DEMO_LLM_RESPONSES, DemoTourCoach, generate_random_scenario
from src.lanterne_rouge.mission_config import bootstrap

# Page configuration
st.set_page_config(
    page_title="Lanterne Rouge Demo",
    page_icon="🚴‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #ff6b6b, #feca57);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .scenario-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize session state
    if 'show_recommendations' not in st.session_state:
        st.session_state.show_recommendations = False
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; text-align: center; margin: 0;">
            🚴‍♂️ Lanterne Rouge Interactive Demo
        </h1>
        <p style="color: white; text-align: center; margin: 0.5rem 0 0 0;">
            AI-Powered Training Coach for Every Athlete
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for controls
    with st.sidebar:
        st.header("🎛️ Demo Controls")
        
        # Reasoning mode selection
        reasoning_mode = st.radio(
            "Select Reasoning Mode:",
            ["LLM-based (Pre-recorded)", "Rule-based", "Compare Both"],
            help="LLM mode uses pre-recorded responses to demonstrate AI capabilities"
        )
        
        # Scenario selection
        st.subheader("Training Scenario")
        scenario_names = {key: info["name"] for key, info in SCENARIOS.items()}
        selected_scenario = st.selectbox(
            "Choose a scenario:",
            options=list(scenario_names.keys()),
            format_func=lambda x: scenario_names[x]
        )
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            custom_metrics = st.checkbox("Customize Metrics")
            show_detailed_analysis = st.checkbox("Show Detailed Analysis", value=True)
            
            if custom_metrics:
                st.subheader("Custom Metrics")
                readiness = st.slider("Readiness Score", 0, 100, 75)
                ctl = st.slider("CTL (Fitness)", 30, 100, 60)
                atl = st.slider("ATL (Fatigue)", 20, 120, 55)
                tsb = st.slider("TSB (Form)", -40, 30, 5)
                days_to_goal = st.slider("Days to Goal", 1, 90, 30)
    
    # Main content area
    st.subheader("📊 Training Overview")
    
    # Get metrics and scenario info
    scenario_info = SCENARIOS[selected_scenario]
    
    if 'custom_metrics' in locals() and custom_metrics:
        metrics = {
            "readiness_score": readiness,
            "ctl": ctl,
            "atl": atl,
            "tsb": tsb,
            "resting_heart_rate": 45,
            "hrv": 70
        }
        days_from_event = days_to_goal
    else:
        if selected_scenario == "random":
            if st.button("🎲 Generate Random Scenario"):
                metrics, days_from_event = generate_random_scenario()
                st.session_state.random_metrics = metrics
                st.session_state.random_days = days_from_event
            
            if 'random_metrics' in st.session_state:
                metrics = st.session_state.random_metrics
                days_from_event = st.session_state.random_days
            else:
                metrics, days_from_event = generate_random_scenario()
        else:
            metrics = scenario_info["metrics"]
            days_from_event = scenario_info["days_from_event"]
    
    # Load mission config for training phase info
    config = bootstrap("missions/tdf_sim_2025.toml")
    demo_date = config.goal_date - timedelta(days=days_from_event)
    training_phase = config.training_phase(demo_date)
    
    # Top info cards
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; color: white; text-align: center;">
            <h3 style="margin: 0; color: white;">🎯 {scenario_info['name']}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">{scenario_info['description']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 1rem; border-radius: 10px; color: white; text-align: center;">
            <h3 style="margin: 0; color: white;">📅 {days_from_event} Days</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Until goal event</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 1rem; border-radius: 10px; color: white; text-align: center;">
            <h3 style="margin: 0; color: white;">🏃‍♂️ {training_phase}</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Training phase</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Current metrics row
    st.subheader("📈 Current Metrics")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        delta_color = "normal"
        if metrics['readiness_score'] < 60:
            delta_color = "inverse"
        elif metrics['readiness_score'] > 85:
            delta_color = "normal"
        st.metric("Readiness", f"{metrics['readiness_score']}/100", 
                 delta=None, delta_color=delta_color)
    
    with col_m2:
        st.metric("CTL (Fitness)", metrics['ctl'], 
                 delta=None, delta_color="normal")
    
    with col_m3:
        st.metric("ATL (Fatigue)", metrics['atl'], 
                 delta=None, delta_color="normal")
    
    with col_m4:
        tsb_delta_color = "normal" if metrics['tsb'] > -10 else "inverse"
        st.metric("TSB (Form)", metrics['tsb'], 
                 delta=None, delta_color=tsb_delta_color)
    
    # Generate recommendations section
    st.subheader("🎯 Get Training Recommendation")
    
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("🚀 Generate Recommendation", type="primary"):
            st.session_state.show_recommendations = True
    
    with col_btn2:
        if st.session_state.get('show_recommendations', False):
            # Get the recommendation action for timeline projection
            if reasoning_mode != "Compare Both":
                use_llm = reasoning_mode == "LLM-based (Pre-recorded)"
                coach = DemoTourCoach(config, use_llm_reasoning=use_llm, demo_scenario=selected_scenario)
                temp_recommendation = coach.generate_daily_recommendation(metrics, demo_date=demo_date)
                
                # Extract action from recommendation for projection
                recommendation_action = "maintain"  # default
                if "recover" in temp_recommendation.lower() or "rest" in temp_recommendation.lower():
                    recommendation_action = "recover"
                elif "push" in temp_recommendation.lower() or "hard" in temp_recommendation.lower():
                    recommendation_action = "push"
            else:
                recommendation_action = "maintain"
            
            # Generate time series data
            timeline_data = generate_time_series_data(metrics, days_from_event, recommendation_action)
            
            # Display timeline chart
            st.subheader("📊 Training Load Timeline")
            timeline_fig = create_training_timeline_chart(timeline_data)
            st.plotly_chart(timeline_fig, use_container_width=True)
            
            # Display recommendations
            generate_recommendations(reasoning_mode, selected_scenario, metrics, days_from_event, show_detailed_analysis)


def generate_recommendations(reasoning_mode, scenario_key, metrics, days_from_event, show_details):
    """Generate and display recommendations based on the selected mode."""
    
    # Load mission config
    config = bootstrap("missions/tdf_sim_2025.toml")
    demo_date = config.goal_date - timedelta(days=days_from_event)
    
    st.subheader("🎯 Training Recommendations")
    
    if reasoning_mode == "Compare Both":
        # Show both recommendations side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🤖 LLM-Based Reasoning")
            show_recommendation(scenario_key, metrics, demo_date, use_llm=True, show_details=show_details)
        
        with col2:
            st.markdown("### ⚙️ Rule-Based Reasoning")
            show_recommendation(scenario_key, metrics, demo_date, use_llm=False, show_details=show_details)
    
    else:
        use_llm = reasoning_mode == "LLM-based (Pre-recorded)"
        show_recommendation(scenario_key, metrics, demo_date, use_llm=use_llm, show_details=show_details)


def show_recommendation(scenario_key, metrics, demo_date, use_llm=True, show_details=True):
    """Display a single recommendation with enhanced formatting."""
    
    # Load mission config
    config = bootstrap("missions/tdf_sim_2025.toml")
    
    # Create coach and generate recommendation
    coach = DemoTourCoach(config, use_llm_reasoning=use_llm, demo_scenario=scenario_key)
    
    with st.spinner("Generating recommendation..."):
        recommendation = coach.generate_daily_recommendation(metrics, demo_date=demo_date)
    
    # Parse the recommendation to extract key information
    lines = recommendation.split('\n')
    training_phase = ""
    decision = ""
    reasoning = ""
    workout_type = ""
    duration = ""
    intensity = ""
    
    for line in lines:
        if "Training Phase:" in line:
            training_phase = line.split(": ")[1]
        elif "Decision:" in line:
            decision = line.split(": ")[1]
        elif "Reasoning:" in line:
            reasoning = line.split(": ", 1)[1] if len(line.split(": ", 1)) > 1 else ""
        elif "Type:" in line:
            workout_type = line.split(": ")[1]
        elif "Duration:" in line:
            duration = line.split(": ")[1]
        elif "Intensity:" in line:
            intensity = line.split(": ")[1]
    
    # Display recommendation in an attractive card format
    recommendation_color = "#28a745"  # Green default
    recommendation_icon = "✅"
    
    if decision and ("recover" in decision.lower() or "rest" in decision.lower()):
        recommendation_color = "#ffc107"  # Yellow for recovery
        recommendation_icon = "💤"
    elif decision and ("push" in decision.lower() or "hard" in decision.lower()):
        recommendation_color = "#dc3545"  # Red for hard training
        recommendation_icon = "🔥"
    
    # Main recommendation card
    st.markdown(f"""
    <div style="background: {recommendation_color}; color: white; padding: 1.5rem; 
                border-radius: 10px; margin: 1rem 0; text-align: center;">
        <h2 style="margin: 0; color: white;">{recommendation_icon} {decision}</h2>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1em; opacity: 0.9;">
            {'🤖 AI Recommendation' if use_llm else '⚙️ Rule-based Decision'}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Workout details in columns
    if workout_type or duration or intensity:
        st.markdown("#### 🏋️‍♂️ Today's Workout Plan")
        col_w1, col_w2, col_w3 = st.columns(3)
        
        with col_w1:
            if workout_type:
                st.info(f"**Type**\n\n{workout_type}")
        
        with col_w2:
            if duration:
                st.info(f"**Duration**\n\n{duration}")
                
        with col_w3:
            if intensity:
                st.info(f"**Intensity**\n\n{intensity}")
    
    # Reasoning section
    if reasoning and show_details:
        st.markdown("#### 🧠 Reasoning")
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; 
                    border-left: 4px solid #007bff; margin: 1rem 0;">
            {reasoning}
        </div>
        """, unsafe_allow_html=True)
    
    # Show full recommendation in expander
    with st.expander("📋 Complete Coach Report"):
        st.text(recommendation)


def generate_time_series_data(current_metrics, days_from_event, recommendation_action="maintain"):
    """Generate realistic time series data for the past 7 days and projected 7 days."""
    
    # Create date range: 7 days ago to 7 days in the future
    today = datetime.now().date()
    dates = [today - timedelta(days=i) for i in range(7, 0, -1)]  # Past 7 days
    dates.append(today)  # Today
    dates.extend([today + timedelta(days=i) for i in range(1, 8)])  # Next 7 days
    
    # Convert dates to datetime objects for plotly compatibility
    dates = [datetime.combine(d, datetime.min.time()) for d in dates]
    
    # Current values
    current_ctl = current_metrics['ctl']
    current_atl = current_metrics['atl']
    current_tsb = current_metrics['tsb']
    current_readiness = current_metrics['readiness_score']
    
    # Generate historical data with some realistic variation
    np.random.seed(42)  # For consistent demo data
    
    # Historical CTL (slowly building fitness)
    historical_ctl = []
    for i in range(7, 0, -1):
        variation = np.random.normal(0, 2)
        ctl_val = current_ctl - (i * 0.5) + variation
        historical_ctl.append(max(20, ctl_val))
    
    # Historical ATL (more variable fatigue)
    historical_atl = []
    for i in range(7, 0, -1):
        variation = np.random.normal(0, 3)
        atl_val = current_atl + np.random.normal(0, 5) + variation
        historical_atl.append(max(10, atl_val))
    
    # Calculate historical TSB
    historical_tsb = [ctl - atl for ctl, atl in zip(historical_ctl, historical_atl)]
    
    # Current day values
    ctl_values = historical_ctl + [current_ctl]
    atl_values = historical_atl + [current_atl]
    tsb_values = historical_tsb + [current_tsb]
    
    # Generate projections based on recommendation
    projected_ctl = []
    projected_atl = []
    
    for i in range(1, 8):
        if recommendation_action == "recover":
            # ATL decreases faster, CTL decreases slowly
            ctl_change = -0.3 * i
            atl_change = -2.0 * i
        elif recommendation_action == "push":
            # Both increase, ATL increases faster
            ctl_change = 0.5 * i
            atl_change = 3.0 * i
        else:  # maintain
            # Gradual fitness building, moderate fatigue
            ctl_change = 0.2 * i
            atl_change = 0.5 * i
        
        projected_ctl.append(max(20, current_ctl + ctl_change + np.random.normal(0, 1)))
        projected_atl.append(max(10, current_atl + atl_change + np.random.normal(0, 2)))
    
    # Add projections
    ctl_values.extend(projected_ctl)
    atl_values.extend(projected_atl)
    tsb_values.extend([ctl - atl for ctl, atl in zip(projected_ctl, projected_atl)])
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'ctl': ctl_values,
        'atl': atl_values,
        'tsb': tsb_values,
        'period': ['Historical'] * 7 + ['Today'] + ['Projected'] * 7
    })
    
    return df


def create_training_timeline_chart(df):
    """Create a comprehensive training timeline chart."""
    fig = go.Figure()
    
    # Define colors
    colors = {
        'ctl': '#2ecc71',  # Green for fitness
        'atl': '#e74c3c',  # Red for fatigue
        'tsb': '#3498db'   # Blue for form
    }
    
    # Add CTL line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['ctl'],
        mode='lines+markers',
        name='CTL (Fitness)',
        line=dict(color=colors['ctl'], width=3),
        marker=dict(size=6, color=colors['ctl']),
        hovertemplate='<b>CTL (Fitness)</b><br>Date: %{x}<br>Value: %{y:.1f}<extra></extra>'
    ))
    
    # Add ATL line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['atl'],
        mode='lines+markers',
        name='ATL (Fatigue)',
        line=dict(color=colors['atl'], width=3),
        marker=dict(size=6, color=colors['atl']),
        hovertemplate='<b>ATL (Fatigue)</b><br>Date: %{x}<br>Value: %{y:.1f}<extra></extra>'
    ))
    
    # Add TSB line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['tsb'],
        mode='lines+markers',
        name='TSB (Form)',
        line=dict(color=colors['tsb'], width=3),
        marker=dict(size=6, color=colors['tsb']),
        hovertemplate='<b>TSB (Form)</b><br>Date: %{x}<br>Value: %{y:.1f}<extra></extra>'
    ))
    
    # Highlight today with a vertical line - use add_shape instead of add_vline
    today_date = datetime.combine(datetime.now().date(), datetime.min.time())
    fig.add_shape(
        type="line",
        x0=today_date, x1=today_date,
        y0=0, y1=1,
        yref="paper",
        line=dict(color="orange", width=3, dash="dash"),
    )
    
    # Add annotation for "Today"
    fig.add_annotation(
        x=today_date,
        y=1.02,
        yref="paper",
        text="Today",
        showarrow=False,
        font=dict(color="orange", size=12),
        xanchor="center"
    )
    
    # Add background shading for different periods using add_shape
    historical_end = today_date - timedelta(days=1)
    projected_start = today_date + timedelta(days=1)
    
    # Historical period (light gray)
    fig.add_shape(
        type="rect",
        x0=df['date'].min(), x1=historical_end,
        y0=0, y1=1,
        yref="paper",
        fillcolor="rgba(128, 128, 128, 0.1)",
        layer="below",
        line_width=0,
    )
    
    # Projected period (light blue)
    fig.add_shape(
        type="rect",
        x0=projected_start, x1=df['date'].max(),
        y0=0, y1=1,
        yref="paper",
        fillcolor="rgba(52, 152, 219, 0.1)",
        layer="below",
        line_width=0,
    )
    
    # Add TSB reference line at 0
    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="gray",
        line_width=1,
        annotation_text="TSB Balance Line",
        annotation_position="bottom right"
    )
    
    fig.update_layout(
        title="Training Load Timeline: 7 Days History + 7 Days Projection",
        xaxis_title="Date",
        yaxis_title="Training Load / Form",
        height=500,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_readiness_gauge(readiness_score):
    """Create a readiness score gauge chart."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = readiness_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Readiness Score"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 50], 'color': "red"},
                {'range': [50, 65], 'color': "orange"},
                {'range': [65, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': readiness_score
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig


if __name__ == "__main__":
    main()
