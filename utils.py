import streamlit as st

def clear_form_states():
    """
    Clear form states stored in Streamlit session_state.
    """
    st.session_state['show_add_form'] = False
    st.session_state['show_bulk_add_form'] = False
    st.session_state['show_update_form'] = False
    st.session_state['update_id'] = None
    st.session_state['current_view'] = None
    st.session_state['show_category_page'] = False
