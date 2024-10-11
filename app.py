# streamlit run app.py --server.headless true

import streamlit as st
from database import create_connection, create_tables
from config import DATABASE_FILE
from manage_languages import manage_languages
from manage_voices import manage_voices
from manage_categories import manage_categories
from manage_names import manage_names
from utils import clear_form_states

def main():
    """
    Main function to run the Streamlit app.
    """
    st.title("Dashboard Control Panel")

    st.sidebar.header("Menu")
    if 'menu' not in st.session_state:
        st.session_state.menu = 'Manage Languages'  # Default menu
        clear_form_states()

    if st.sidebar.button("Manage Languages"):
        st.session_state.menu = "Manage Languages"
        clear_form_states()
    if st.sidebar.button("Manage Voices"):
        st.session_state.menu = "Manage Voices"
        clear_form_states()
    if st.sidebar.button("Manage Names"):
        st.session_state.menu = "Manage Names"
        clear_form_states()
    if st.sidebar.button("Manage Categories"):
        st.session_state.menu = "Manage Categories"
        clear_form_states()

    choice = st.session_state.menu

    # Initialize the database
    conn = create_connection(DATABASE_FILE)
    create_tables(conn)

    if choice == "Manage Languages":
        manage_languages(conn)
    elif choice == "Manage Voices":
        manage_voices(conn)
    elif choice == "Manage Names":
        manage_names(conn)
    elif choice == "Manage Categories":
        manage_categories(conn)
    
    if 'language_added' not in st.session_state:
        st.session_state['language_added'] = False

    if 'voices_added' not in st.session_state:
        st.session_state['voices_added'] = False

if __name__ == '__main__':
    main()
