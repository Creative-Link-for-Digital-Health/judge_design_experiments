import streamlit as st
import pandas as pd
import json
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
        filename = f"conversation_evaluations_{timestamp}.json"
        
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

def display_evaluation_summary(df):
    """Display summary of evaluations"""
    if not st.session_state.evaluations:
        return
    
    st.subheader("📊 Evaluation Summary")
    
    total_evaluated = len(st.session_state.evaluations)
    total_turns = len(df)
    true_count = sum(1 for v in st.session_state.evaluations.values() if v == True)
    false_count = sum(1 for v in st.session_state.evaluations.values() if v == False)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Turns", total_turns)
    with col2:
        st.metric("Evaluated", total_evaluated)
    with col3:
        st.metric("True", true_count, delta=f"{true_count/total_evaluated*100:.1f}%" if total_evaluated > 0 else "0%")
    with col4:
        st.metric("False", false_count, delta=f"{false_count/total_evaluated*100:.1f}%" if total_evaluated > 0 else "0%")
    
    # Progress bar
    progress = total_evaluated / total_turns if total_turns > 0 else 0
    st.progress(progress, text=f"Progress: {total_evaluated}/{total_turns} turns evaluated")

def main():
    st.set_page_config(
        page_title="Conversation Evaluator",
        page_icon="💬",
        layout="wide"
    )
    
    st.title("💬 Conversation Turn Evaluator")
    st.markdown("Evaluate each conversation turn as **True** or **False**")
    st.markdown("## Background")
    st.markdown("""
**Known Facts about PersonB:**
- Favorite flavor: Strawberry
- Least favorite flavor: Mint chip
- Allergic to: Nuts
- Most commonly eats: Strawberry ice cream
- Dislikes: Rocky road, mint chip
- Neutral about: Cookies and cream"
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
        st.markdown("Use the buttons to navigate or evaluate the current turn.")
    
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
    st.markdown("### ✅ Evaluation")
    st.markdown("Is Person B's answer consistent, truthful, or appropriate?")
    
    # Get current evaluation if exists
    current_evaluation = st.session_state.evaluations.get(str(turn_id), None)
    
    # Evaluation buttons
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("✅ True", type="primary" if current_evaluation == True else "secondary", use_container_width=True):
            st.session_state.evaluations[str(turn_id)] = True
            st.rerun()
    
    with col2:
        if st.button("❌ False", type="primary" if current_evaluation == False else "secondary", use_container_width=True):
            st.session_state.evaluations[str(turn_id)] = False
            st.rerun()

    
    # Show current evaluation status
    if current_evaluation is not None:
        status_color = "green" if current_evaluation else "red"
        status_text = "True ✅" if current_evaluation else "False ❌"
        st.markdown(f"**Current evaluation:** :{status_color}[{status_text}]")
    else:
        st.markdown("**Current evaluation:** Not evaluated yet")
    
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
    

    # Save/Export section
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save Evaluations", use_container_width=True):
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
                    'evaluation': evaluation,
                    'notes': notes
                })
            
            results_df = pd.DataFrame(results_data)
            csv_data = results_df.to_csv(index=False)
            
            st.download_button(
                label="Download Results as CSV",
                data=csv_data,
                file_name=f"conversation_evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

if __name__ == "__main__":
    main()