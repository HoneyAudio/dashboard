# manage_voices.py

import streamlit as st
from database import execute_query, fetch_all, fetch_one
import pandas as pd
from utils import clear_form_states

def manage_voices(conn):
    """
    Functions to manage voices.
    """
    st.header("Manage Voices")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    if col1.button("View All Voices"):
        clear_form_states()
        st.session_state['current_view'] = 'view_all'
    if col2.button("Add Voice"):
        clear_form_states()
        st.session_state['show_add_form'] = True
    if col3.button("Bulk Add Voices"):
        clear_form_states()
        st.session_state['show_bulk_add_form'] = True

    # Handle different views
    if st.session_state.get('show_add_form', False):
        add_voice(conn)
    elif st.session_state.get('show_bulk_add_form', False):
        bulk_add_voices(conn)
    elif st.session_state.get('show_update_form', False):
        update_voice(conn, st.session_state['update_id'])
    elif st.session_state.get('current_view') == 'view_all':
        view_all_voices(conn)

def view_all_voices(conn):
    """
    View all voices in the database.
    """
    st.subheader("All Voices")
    query = """
        SELECT voice.id, voice.name, voice.gender, language.code, voice.elevenlabs_voice_id 
        FROM voice 
        JOIN language ON voice.language_id = language.id
    """
    data = fetch_all(conn, query)
    if data:
        for row in data:
            col1, col2, col3, col4, col5, col6 = st.columns([2,2,2,2,2,2])
            col1.write(row[1])  # Voice Name
            col2.write(row[2])  # Gender
            col3.write(row[3])  # Language Code
            col4.write(row[4])  # ElevenLabs Voice ID
            update_clicked = col5.button("Update", key=f"update_voice_{row[0]}")
            delete_clicked = col6.button("Delete", key=f"delete_voice_{row[0]}")
            if update_clicked:
                st.session_state['show_update_form'] = True
                st.session_state['update_id'] = row[0]
                st.session_state['current_view'] = None
                st.rerun()
            if delete_clicked:
                delete_voice(conn, row[0])
                st.rerun()
    else:
        st.info("No voices found. Please add voices.")

def add_voice(conn):
    """
    Add a new voice to the database.
    """
    st.subheader("Add Voice")
    voice_name = st.text_input("Voice Name", key="add_voice_name")
    elevenlabs_voice_id = st.text_input("ElevenLabs Voice ID", key="add_voice_id")
    gender = st.selectbox("Gender", ["male", "female"], key="add_voice_gender")
    
    # Fetch languages
    languages = fetch_all(conn, "SELECT id, name FROM language")
    if languages:
        language_options = {name: id for id, name in languages}
        language_name = st.selectbox("Language", list(language_options.keys()), key="add_voice_language_name")
        language_id = language_options[language_name]
    else:
        st.warning("No languages found. Please add languages first.")
        return

    if st.button("Save Voice", key="save_voice_button"):
        if voice_name.strip() and elevenlabs_voice_id.strip():
            try:
                execute_query(conn, 
                    "INSERT INTO voice (name, elevenlabs_voice_id, gender, language_id) VALUES (?, ?, ?, ?)",
                    (voice_name.strip(), elevenlabs_voice_id.strip(), gender, language_id)
                )
                st.success(f"Added voice '{voice_name.strip()}'")
                clear_form_states()
                st.session_state['current_view'] = 'view_all'
                st.rerun()
            except Exception as e:
                st.error(f"Error adding voice: {str(e)}")
        else:
            st.error("All fields are required.")

def bulk_add_voices(conn):
    """
    Bulk add voices from a CSV file.
    """
    st.subheader("Bulk Add Voices")
    uploaded_file = st.file_uploader("Upload CSV file with columns 'name', 'elevenlabs_voice_id', 'gender', 'language_code'", type=["csv"], key="bulk_add_voices_uploader")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        required_columns = {'name', 'elevenlabs_voice_id', 'gender', 'language_code'}
        if required_columns.issubset(df.columns):
            # Fetch languages
            languages = fetch_all(conn, "SELECT id, code FROM language")
            language_dict = {code: id for id, code in languages}
            records = []
            for _, row in df.iterrows():
                language_code = row['language_code']
                language_id = language_dict.get(language_code)
                if language_id:
                    records.append((row['name'], row['elevenlabs_voice_id'], row['gender'], language_id))
                else:
                    st.warning(f"Language code '{language_code}' not found. Skipping voice '{row['name']}'.")
            if st.button("Save Voices", key="save_bulk_voices_button"):
                success_count = 0
                for record in records:
                    try:
                        execute_query(conn, 
                            "INSERT INTO voice (name, elevenlabs_voice_id, gender, language_id) VALUES (?, ?, ?, ?)",
                            record
                        )
                        success_count += 1
                    except Exception as e:
                        st.warning(f"Skipped duplicate voice: {record[0]}")
                st.success(f"Bulk added {success_count} voices.")
                clear_form_states()
                st.session_state['current_view'] = 'view_all'
                st.rerun()
        else:
            st.error(f"CSV must contain columns: {', '.join(required_columns)}")

def update_voice(conn, voice_id):
    """
    Update an existing voice.
    """
    st.subheader("Update Voice")
    voice_record = fetch_one(conn, "SELECT name, elevenlabs_voice_id, gender, language_id FROM voice WHERE id = ?", (voice_id,))
    if voice_record:
        new_voice_name = st.text_input("New Voice Name", value=voice_record[0], key="update_voice_name")
        new_elevenlabs_voice_id = st.text_input("New ElevenLabs Voice ID", value=voice_record[1], key="update_voice_id")
        new_gender = st.selectbox("New Gender", ["male", "female"], index=["male", "female"].index(voice_record[2]), key="update_voice_gender")
        
        # Fetch languages
        languages = fetch_all(conn, "SELECT id, name FROM language")
        language_options = {name: id for id, name in languages}
        language_names = list(language_options.keys())
        current_language_name = next(name for name, id in language_options.items() if id == voice_record[3])
        new_language_name = st.selectbox("Language", language_names, index=language_names.index(current_language_name), key="update_voice_language_name")
        new_language_id = language_options[new_language_name]
        
        if st.button("Save Changes", key="update_voice_button"):
            if new_voice_name.strip() and new_elevenlabs_voice_id.strip():
                try:
                    execute_query(conn, 
                        "UPDATE voice SET name = ?, elevenlabs_voice_id = ?, gender = ?, language_id = ? WHERE id = ?",
                        (new_voice_name.strip(), new_elevenlabs_voice_id.strip(), new_gender, new_language_id, voice_id)
                    )
                    st.success(f"Updated voice to '{new_voice_name.strip()}'")
                    clear_form_states()
                    st.session_state['current_view'] = 'view_all'
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating voice: {str(e)}")
            else:
                st.error("All fields are required.")
    else:
        st.error("Voice not found.")
        clear_form_states()
        st.session_state['current_view'] = 'view_all'

def delete_voice(conn, voice_id):
    """
    Delete a voice from the database.
    """
    voice_record = fetch_one(conn, "SELECT name FROM voice WHERE id = ?", (voice_id,))
    if voice_record:
        execute_query(conn, "DELETE FROM voice WHERE id = ?", (voice_id,))
        st.success(f"Deleted voice '{voice_record[0]}'")
    else:
        st.error("Voice not found.")
