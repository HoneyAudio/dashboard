import streamlit as st
from database import execute_query, fetch_all, fetch_one
import pandas as pd
from utils import clear_form_states

def manage_languages(conn):
    """
    Function to manage languages.
    """
    st.header("Manage Languages")

    # Action buttons
    col1, col2, col3 = st.columns(3)
    if col1.button("View All Languages"):
        clear_form_states()
        st.session_state['current_view'] = 'view_all'
    if col2.button("Add Language"):
        clear_form_states()
        st.session_state['show_add_form'] = True
    if col3.button("Bulk Add Languages"):
        clear_form_states()
        st.session_state['show_bulk_add_form'] = True

    if st.session_state.get('show_add_form', False):
        add_language(conn)
    elif st.session_state.get('show_bulk_add_form', False):
        bulk_add_languages(conn)
    elif st.session_state.get('show_update_form', False):
        update_language(conn, st.session_state['update_id'])
    elif st.session_state.get('current_view') == 'view_all':
        view_all_languages(conn)

def view_all_languages(conn):
    """
    View all languages in the database.
    """
    st.subheader("All Languages")
    data = fetch_all(conn, "SELECT * FROM language")
    if data:
        for row in data:
            col1, col2, col3, col4 = st.columns([3,2,2,2])
            col1.write(row[1])  # Language Name
            col2.write(row[2])  # Language Code
            update_clicked = col3.button("Update", key=f"update_language_{row[0]}")
            delete_clicked = col4.button("Delete", key=f"delete_language_{row[0]}")
            if update_clicked:
                st.session_state['show_update_form'] = True
                st.session_state['update_id'] = row[0]
                st.session_state['current_view'] = None
                st.rerun()
            if delete_clicked:
                delete_language(conn, row[0])
                st.rerun()
    else:
        st.info("No languages found. Please add languages.")

def add_language(conn):
    """
    Add a new language to the database.
    """
    st.subheader("Add Language")
    language_name = st.text_input("Language Name", key="add_language_name")
    language_code = st.text_input("Language Code (e.g., 'en' for English)", key="add_language_code")
    if st.button("Save Language", key="save_language_button"):
        if language_name.strip() and language_code.strip():
            try:
                execute_query(conn, "INSERT INTO language (name, code) VALUES (?, ?)", (language_name.strip(), language_code.strip()))
                st.success(f"Added language '{language_name.strip()}'")
                clear_form_states()
                st.session_state['current_view'] = 'view_all'
                st.rerun()
            except Exception as e:
                st.error(f"Error adding language: {str(e)}")
        else:
            st.error("Language name and code cannot be empty.")

def bulk_add_languages(conn):
    """
    Bulk add languages from a CSV file.
    """
    st.subheader("Bulk Add Languages")
    uploaded_file = st.file_uploader("Upload CSV file with columns 'name' and 'code'", type=["csv"], key="bulk_add_languages_uploader")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if 'name' in df.columns and 'code' in df.columns:
            records = df[['name', 'code']].values.tolist()
            if st.button("Save Languages", key="save_bulk_languages_button"):
                success_count = 0
                for record in records:
                    try:
                        execute_query(conn, "INSERT INTO language (name, code) VALUES (?, ?)", record)
                        success_count += 1
                    except Exception as e:
                        st.warning(f"Skipped duplicate language: {record[0]}")
                st.success(f"Bulk added {success_count} languages.")
                clear_form_states()
                st.session_state['current_view'] = 'view_all'
                st.experimental_rerun()
        else:
            st.error("CSV must contain 'name' and 'code' columns.")

def update_language(conn, language_id):
    """
    Update an existing language.
    """
    st.subheader("Update Language")
    language_record = fetch_one(conn, "SELECT name, code FROM language WHERE id = ?", (language_id,))
    if language_record:
        new_language_name = st.text_input("New Language Name", value=language_record[0], key="update_language_name")
        new_language_code = st.text_input("New Language Code", value=language_record[1], key="update_language_code")
        if st.button("Save Changes", key="update_language_button"):
            if new_language_name.strip() and new_language_code.strip():
                try:
                    execute_query(conn, "UPDATE language SET name = ?, code = ? WHERE id = ?", (new_language_name.strip(), new_language_code.strip(), language_id))
                    st.success(f"Updated language to '{new_language_name.strip()}'")
                    clear_form_states()
                    st.session_state['current_view'] = 'view_all'
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error updating language: {str(e)}")
            else:
                st.error("Language name and code cannot be empty.")
    else:
        st.error("Language not found.")
        clear_form_states()
        st.session_state['current_view'] = 'view_all'

def delete_language(conn, language_id):
    """
    Delete a language from the database.
    """
    language_record = fetch_one(conn, "SELECT name FROM language WHERE id = ?", (language_id,))
    if language_record:
        execute_query(conn, "DELETE FROM language WHERE id = ?", (language_id,))
        st.success(f"Deleted language '{language_record[0]}'")
    else:
        st.error("Language not found.")
