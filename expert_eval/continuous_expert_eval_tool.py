import streamlit as st
import pandas as pd
import json
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def load_data():
    """Load the conversation data from CSV"""
    try:
        # You can either upload the file or place it in the same directory
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            return df
        else:
            # Fallback: try to load from local file
            try:
                df = pd.read_csv('conversation_data.csv')
                st.info("Loaded conversation_data.csv from local directory")
                return df
            except FileNotFoundError:
                st.warning("Please upload your CSV file using the file uploader above.")
                return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def initialize_session_state(df):
    """Initialize session state for storing evaluations"""
    if 'evaluations' not in st.session_state:
        st.session_state.evaluations = {}
    
    if 'current_turn' not in st.session_state:
        st.session_state.current_turn = 0
    
    if 'total_turns' not in st.session_state:
        st.session_state.total_turns = len(df) if df is not None else 0

def save_evaluations():
    """Save evaluations to a JSON file"""
    if st.session_state.evaluations:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_evaluations_likert_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(st.session_state.evaluations, f, indent=2)
        
        st.success(f"Evaluations saved to {filename}")
        
        # Also provide download button
        json_str = json.dumps(st.session_state.evaluations, indent=2)
        st.download_button(
            label="Download Evaluations as JSON",
            data=json_str,
            file_name=filename,
            mime="application/json"
        )

def create_rating_distribution_chart():
    """Create a distribution chart of ratings"""
    if not st.session_state.evaluations:
        return None
    
    ratings = [v for v in st.session_state.evaluations.values() if v is not None]
    if not ratings:
        return None
    
    # Create histogram
    fig = px.histogram(
        x=ratings,
        nbins=5,
        title="Distribution of Ratings",
        labels={'x': 'Rating', 'y': 'Count'},
        color_discrete_sequence=['#1f77b4']
    )
    
    fig.update_layout(
        xaxis=dict(dtick=1, range=[0.5, 5.5]),
        bargap=0.1,
        height=300
    )
    
    return fig

def display_evaluation_summary(df):
    """Display summary of evaluations"""
    if not st.session_state.evaluations:
        return
    
    st.subheader("📊 Evaluation Summary")
    
    total_evaluated = len([v for v in st.session_state.evaluations.values() if v is not None])
    total_turns = len(df)
    
    if total_evaluated > 0:
        ratings = [v for v in st.session_state.evaluations.values() if v is not None]
        mean_rating = np.mean(ratings)
        std_rating = np.std(ratings)
        median_rating = np.median(ratings)
        
        # Count distribution
        rating_counts = {i: ratings.count(i) for i in range(1, 6)}
    else:
        mean_rating = std_rating = median_rating = 0
        rating_counts = {i: 0 for i in range(1, 6)}
    
    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Turns", total_turns)
    with col2:
        st.metric("Evaluated", total_evaluated)
    with col3:
        st.metric("Mean Rating", f"{mean_rating:.2f}" if total_evaluated > 0 else "N/A")
    with col4:
        st.metric("Std Dev", f"{std_rating:.2f}" if total_evaluated > 0 else "N/A")
    with col5:
        st.metric("Median", f"{median_rating:.1f}" if total_evaluated > 0 else "N/A")
    
    # Progress bar
    progress = total_evaluated / total_turns if total_turns > 0 else 0
    st.progress(progress, text=f"Progress: {total_evaluated}/{total_turns} turns evaluated")
    
    # Rating distribution
    if total_evaluated > 0:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Rating Distribution:**")
            for i in range(1, 6):
                percentage = (rating_counts[i] / total_evaluated * 100) if total_evaluated > 0 else 0
                st.write(f"Rating {i}: {rating_counts[i]} ({percentage:.1f}%)")
        
        with col2:
            # Display chart
            chart = create_rating_distribution_chart()
            if chart:
                st.plotly_chart(chart, use_container_width=True)

def get_rating_color(rating):
    """Get color for rating display"""
    if rating is None:
        return "gray"
    elif rating <= 2:
        return "red"
    elif rating == 3:
        return "orange"
    else:
        return "green"

def get_rating_emoji(rating):
    """Get emoji for rating"""
    if rating is None:
        return "❓"
    emoji_map = {1: "😞", 2: "😕", 3: "😐", 4: "😊", 5: "😍"}
    return emoji_map.get(rating, "❓")

def main():
    st.set_page_config(
        page_title="Continuous Scale Conversation Evaluator",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Conversation Evaluator")
    st.markdown("Evaluate each conversation turn for friendliness on a **1-5 Likert scale**")
    
    # Rating scale explanation
    with st.expander("📋 Rating Scale Guide", expanded=False):
        st.markdown("""
        **Rating Scale (1-5):**
        - **1** 😞 - Very Poor (Completely inappropriate, false, or inconsistent)
        - **2** 😕 - Poor (Mostly inappropriate or inconsistent)
        - **3** 😐 - Neutral/Average (Somewhat appropriate, mixed quality)
        - **4** 😊 - Good (Mostly appropriate and consistent)
        - **5** 😍 - Excellent (Completely appropriate, truthful, and consistent)
        """)
    
    st.markdown("## Background")
    st.markdown("""
**Known Facts about PersonB:**
- Favorite flavor: Strawberry
- Least favorite flavor: Mint chip
- Allergic to: Nuts
- Most commonly eats: Strawberry ice cream
- Dislikes: Rocky road, mint chip
- Neutral about: Cookies and cream
""")
    
    # Load data
    df = load_data()
    
    if df is None:
        st.stop()
    
    # Validate CSV structure
    required_columns = ['turn_id', 'personA_question', 'personB_answer']
    if not all(col in df.columns for col in required_columns):
        st.error(f"CSV must contain columns: {', '.join(required_columns)}")
        st.stop()
    
    # Initialize session state
    initialize_session_state(df)
    
    # Display summary
    display_evaluation_summary(df)
    
    st.divider()
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=st.session_state.current_turn <= 0):
            st.session_state.current_turn = max(0, st.session_state.current_turn - 1)
            st.rerun()
    
    with col2:
        st.markdown(f"**Current Turn:** {st.session_state.current_turn + 1} / {len(df)}")
        # Jump to specific turn
        # target_turn = st.number_input(
        #     "Jump to turn:",
        #     min_value=1,
        #     max_value=len(df),
        #     value=st.session_state.current_turn + 1,
        #     key="jump_to_turn"
        # )
        # if st.button("Go to Turn"):
        #     st.session_state.current_turn = target_turn - 1
        #     st.rerun()
    
    with col3:
        if st.button("Next ➡️", disabled=st.session_state.current_turn >= len(df) - 1):
            st.session_state.current_turn = min(len(df) - 1, st.session_state.current_turn + 1)
            st.rerun()
    
    # Current turn display
    current_row = df.iloc[st.session_state.current_turn]
    turn_id = current_row['turn_id']
    
    st.subheader(f"Turn {turn_id} of {len(df)}")
    
    # Display conversation
    with st.container():
        st.markdown("### 🗣️ Conversation")
        
        # Question
        st.markdown(f"**Person A:** {current_row['personA_question']}")
        
        # Answer
        st.markdown(f"**Person B:** {current_row['personB_answer']}")
    
    st.divider()
    
    # Evaluation section
    st.markdown("### 📊 Evaluation")
    st.markdown("Rate Person B's answer on consistency, truthfulness, and appropriateness:")
    
    # Get current evaluation if exists
    current_evaluation = st.session_state.evaluations.get(str(turn_id), None)
    
    # Likert scale buttons
    st.markdown("**Select Rating:**")
    rating_cols = st.columns(5)
    
    for i, col in enumerate(rating_cols, 1):
        with col:
            emoji = get_rating_emoji(i)
            is_selected = current_evaluation == i
            button_type = "primary" if is_selected else "secondary"
            
            if st.button(
                f"{emoji}\n{i}",
                key=f"rating_{i}",
                type=button_type,
                use_container_width=True
            ):
                st.session_state.evaluations[str(turn_id)] = i
                st.rerun()
    
    # Alternative: Slider input
    st.markdown("**Or use slider:**")
    slider_value = st.slider(
        "Rating",
        min_value=1,
        max_value=5,
        value=current_evaluation if current_evaluation is not None else 3,
        step=1,
        key=f"slider_{turn_id}"
    )
    
    if st.button("Set Rating from Slider"):
        st.session_state.evaluations[str(turn_id)] = slider_value
        st.rerun()
    
    # Show current evaluation status
    if current_evaluation is not None:
        color = get_rating_color(current_evaluation)
        emoji = get_rating_emoji(current_evaluation)
        st.markdown(f"**Current evaluation:** :{color}[{emoji} Rating: {current_evaluation}]")
    else:
        st.markdown("**Current evaluation:** Not evaluated yet")
    
    # Quick navigation to next unrated turn
    unrated_turns = [i for i, row in df.iterrows() 
                    if st.session_state.evaluations.get(str(row['turn_id']), None) is None]
    
    if unrated_turns:
        if st.button(f"🚀 Jump to Next Unrated Turn ({len(unrated_turns)} remaining)"):
            st.session_state.current_turn = unrated_turns[0]
            st.rerun()
    
    # Add notes section
    st.divider()
    notes_key = f"notes_{turn_id}"
    if notes_key not in st.session_state:
        st.session_state[notes_key] = ""
    
    notes = st.text_area(
        "📝 Notes (optional):",
        value=st.session_state[notes_key],
        key=f"notes_input_{turn_id}",
        height=100
    )
    st.session_state[notes_key] = notes
    
    # Clear rating option
    if current_evaluation is not None:
        if st.button("🗑️ Clear Rating", type="secondary"):
            st.session_state.evaluations[str(turn_id)] = None
            st.rerun()
    
    # Save/Export section
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save Evaluations", use_container_width=True):
            save_evaluations()
    
    with col2:
        if st.session_state.evaluations:
            # Create results DataFrame
            results_data = []
            for idx, row in df.iterrows():
                turn_id = str(row['turn_id'])
                evaluation = st.session_state.evaluations.get(turn_id, None)
                notes = st.session_state.get(f"notes_{row['turn_id']}", "")
                
                results_data.append({
                    'turn_id': row['turn_id'],
                    'personA_question': row['personA_question'],
                    'personB_answer': row['personB_answer'],
                    'likert_rating': evaluation,
                    'notes': notes
                })
            
            results_df = pd.DataFrame(results_data)
            csv_data = results_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv_data,
                file_name=f"likert_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

if __name__ == "__main__":
    main()