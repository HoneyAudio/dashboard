# manage_names.py

import streamlit as st
from database import execute_query, fetch_all, fetch_one
import pandas as pd
from utils import clear_form_states
from openai_utils import generate_personal_text
from tts import text_to_speech_stream
from s3_utils import upload_audiostream_to_s3, generate_presigned_url
from config import OPENAI_API_KEY
import openai

# Initialize OpenAI API key
openai.api_key = OPENAI_API_KEY

def manage_names(conn):
    """
    Functions to manage names.
    """
    st.header("Manage Names")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("View All Names"):
        clear_form_states()
        st.session_state['current_view'] = 'view_all'
        st.session_state['name_page'] = False
    if col2.button("Add Name"):
        clear_form_states()
        st.session_state['show_add_form'] = True
        st.session_state['name_page'] = False
    if col3.button("Bulk Add Names"):
        clear_form_states()
        st.session_state['show_bulk_add_form'] = True
        st.session_state['name_page'] = False
    # if col4.button("Generate All Personal TTS"):
    #     clear_form_states()
    #     generate_messages_for_all_names(conn)
    #     st.session_state['name_page'] = False
    
    # Handle different views
    if st.session_state.get('show_add_form', False):
        add_name(conn)
    elif st.session_state.get('show_bulk_add_form', False):
        bulk_add_names(conn)
    elif st.session_state.get('show_update_form', False):
        update_name(conn, st.session_state['update_id'])
    elif st.session_state.get('current_view') == 'view_all':
        view_all_names(conn)
    if st.session_state.get('name_page', False):
        name_page(conn, st.session_state['name_id'])

def view_all_names(conn):
    """
    View all names in the database.
    """
    st.subheader("All Names")
    query = """
        SELECT name.id, name.name, name.gender, language.code, language.id
        FROM name
        JOIN language ON name.language_id = language.id
    """
    data = fetch_all(conn, query)
    if data:
        for row in data:
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2,2,2,2,2,2,2])
            col1.write(row[1])  # Name
            col2.write(row[2])  # Gender
            col3.write(row[3])  # Language Code
            update_clicked = col4.button("Update", key=f"update_name_{row[0]}")
            delete_clicked = col5.button("Delete", key=f"delete_name_{row[0]}")
            generate_clicked = col6.button("Gen TTS", key=f"generate_messages_{row[0]}")
            view_clicked = col7.button("View", key=f"view_name_{row[0]}")
            if view_clicked:
                st.session_state['name_page'] = True
                st.session_state['name_id'] = row[0]
                st.session_state['current_view'] = None
                st.rerun()
            if update_clicked:
                st.session_state['show_update_form'] = True
                st.session_state['update_id'] = row[0]
                st.session_state['current_view'] = None
                st.session_state['name_page'] = False
                st.rerun()
            if delete_clicked:
                delete_name(conn, row[0])
                st.rerun()
            if generate_clicked:
                generate_messages_for_name(conn, row[0], row[1], row[2], row[4])
                st.rerun()
    else:
        st.info("No names found. Please add names.")

def add_name(conn):
    """
    Add a new name to the database.
    """
    st.subheader("Add Name")
    name = st.text_input("Name", key="add_name_input")
    gender = st.selectbox("Gender", ["male", "female"], key="add_name_gender")
    
    # Fetch languages
    languages = fetch_all(conn, "SELECT id, name FROM language")
    if languages:
        language_options = {name: id for id, name in languages}
        language_name = st.selectbox("Language", list(language_options.keys()), key="add_category_language")
        language_id = language_options[language_name]
    else:
        st.warning("No languages found. Please add languages first.")
        return
    
    if st.button("Save Name", key="save_name_button"):
        if name.strip():
            try:
                execute_query(conn,
                    "INSERT INTO name (name, gender, language_id) VALUES (?, ?, ?)",
                    (name.strip(), gender, language_id)
                )
                st.success(f"Added {name.strip()}")
                clear_form_states()
                st.session_state['current_view'] = 'view_all'
                st.session_state['name_page'] = False
                st.rerun()
            except Exception as e:
                st.error(f"Error adding name: {str(e)}")
        else:
            st.error("Name cannot be empty.")

def bulk_add_names(conn):
    """
    Bulk add names from a CSV file.
    """
    st.subheader("Bulk Add Names")
    uploaded_file = st.file_uploader("Upload CSV file with columns 'name', 'gender', 'language_code'", type=["csv"], key="bulk_add_names_uploader")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        required_columns = {'name', 'gender', 'language_code'}
        if required_columns.issubset(df.columns):
            # Fetch languages
            languages = fetch_all(conn, "SELECT id, code FROM language")
            language_dict = {code: id for id, code in languages}
            records = []
            for _, row in df.iterrows():
                language_code = row['language_code']
                language_id = language_dict.get(language_code)
                if language_id:
                    records.append((row['name'], row['gender'], language_id))
                else:
                    st.warning(f"Language code '{language_code}' not found. Skipping name '{row['name']}'.")
            if st.button("Save Names", key="save_bulk_names_button"):
                success_count = 0
                for record in records:
                    try:
                        execute_query(conn,
                            "INSERT INTO name (name, gender, language_id) VALUES (?, ?, ?)",
                            record
                        )
                        success_count += 1
                    except Exception as e:
                        st.warning(f"Skipped duplicate: {record}")
                st.success(f"Bulk added {success_count} names.")
                clear_form_states()
                st.session_state['current_view'] = 'view_all'
                st.session_state['name_page'] = False
                st.rerun()
        else:
            st.error(f"CSV must contain columns: {', '.join(required_columns)}")

def update_name(conn, name_id):
    """
    Update an existing name.
    """
    st.subheader("Update Name")
    name_record = fetch_one(conn, "SELECT name, gender, language_id FROM name WHERE id = ?", (name_id,))
    if name_record:
        new_name = st.text_input("New Name", value=name_record[0], key="update_name_input")
        new_gender = st.selectbox("New Gender", ["male", "female"], index=["male", "female"].index(name_record[1]), key="update_gender")
        
        # Fetch languages
        languages = fetch_all(conn, "SELECT id, name FROM language")
        language_options = {name: id for id, name in languages}
        language_names = list(language_options.keys())
        current_language_name = next(name for name, id in language_options.items() if id == name_record[2])
        new_language_name = st.selectbox("Language", language_names, index=language_names.index(current_language_name), key="update_name_language")
        new_language_id = language_options[new_language_name]
        
        if st.button("Save Changes", key="update_name_button"):
            if new_name.strip():
                try:
                    execute_query(conn,
                        "UPDATE name SET name = ?, gender = ?, language_id = ? WHERE id = ?",
                        (new_name.strip(), new_gender, new_language_id, name_id)
                    )
                    st.success(f"Updated name to {new_name.strip()}")
                    clear_form_states()
                    st.session_state['current_view'] = 'view_all'
                    st.session_state['name_page'] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating name: {str(e)}")
            else:
                st.error("Name cannot be empty.")
    else:
        st.error("Name not found.")
        clear_form_states()
        st.session_state['current_view'] = 'view_all'
        st.session_state['name_page'] = False

def delete_name(conn, name_id):
    """
    Delete a name from the database.
    """
    name_record = fetch_one(conn, "SELECT name FROM name WHERE id = ?", (name_id,))
    if name_record:
        execute_query(conn, "DELETE FROM name WHERE id = ?", (name_id,))
        st.success(f"Deleted name '{name_record[0]}'")
    else:
        st.error("Name not found.")

def name_page(conn, name_id):
    """
    Display the name page with personal messages.
    """
    st.subheader(f"Name Details")
    name_record = fetch_one(conn, "SELECT name, gender FROM name WHERE id = ?", (name_id,))
    if name_record:
        st.write(f"**Name:** {name_record[0]}")
        st.write(f"**Gender:** {name_record[1]}")

        # Button to generate texts for this name
        if st.button(f"Generate Messages for {name_record[0]}", key=f"generate_messages_name_page_{name_id}"):
            generate_messages_for_name(conn, name_id, name_record[0], name_record[1], fetch_one(conn, "SELECT language_id FROM name WHERE id = ?", (name_id,))[0])
            st.rerun()

        # Display personalized texts
        messages = fetch_all(conn, "SELECT id, type, text, audio_file FROM personal WHERE name_id = ?", (name_id,))
        for msg in messages:
            st.write(f"**Type:** {msg[1]}")
            st.write(f"**Text:** {msg[2]}")
            if msg[3]:
                signed_url = generate_presigned_url(msg[3])
                st.audio(signed_url)
            edit_clicked = st.button("Edit", key=f"edit_msg_{msg[0]}")
            delete_clicked = st.button("Delete", key=f"delete_msg_{msg[0]}")
            generate_tts_clicked = st.button("Generate TTS", key=f"generate_tts_msg_{msg[0]}")
            if edit_clicked:
                edit_personal_text(conn, msg[0], msg[2])
            if delete_clicked:
                execute_query(conn, "DELETE FROM personal WHERE id = ?", (msg[0],))
                st.success("Message deleted.")
                st.rerun()
            if generate_tts_clicked:
                generate_tts_for_personal_text(conn, msg[0])
    else:
        st.error("Name not found.")

def edit_personal_text(conn, text_id, current_text):
    """
    Edit a personal text message.
    """
    new_text = st.text_area("Edit Text", value=current_text, key=f"edit_text_{text_id}")
    if st.button("Save Changes", key=f"save_text_{text_id}"):
        execute_query(conn, "UPDATE personal SET text = ? WHERE id = ?", (new_text, text_id))
        st.success("Text updated.")
        st.rerun()

def generate_tts_for_personal_text(conn, text_id):
    """
    Generate TTS for a personal text message.
    """
    text_record = fetch_one(conn, "SELECT text, name_id FROM personal WHERE id = ?", (text_id,))
    if text_record:
        text = text_record[0]
        name_id = text_record[1]
        
        # Get voice ID
        name_info = fetch_one(conn, "SELECT language_id, gender FROM name WHERE id = ?", (name_id,))
        language_id = name_info[0]
        gender = name_info[1]
        voice_id = get_voice_id(conn, language_id, gender)
        
        if voice_id:
            audio_stream = text_to_speech_stream(text, voice_id)
            s3_file_name = upload_audiostream_to_s3(audio_stream)
            execute_query(conn, "UPDATE personal SET audio_file = ? WHERE id = ?", (s3_file_name, text_id))
            st.success("TTS generated.")
            st.rerun()
        else:
            st.error("No matching voice found for TTS generation.")
    else:
        st.error("Text not found.")

def generate_messages_for_all_names(conn):
    """
    Generate messages for all names.
    """
    names = fetch_all(conn,
        "SELECT name.id, name.name, name.gender, language.id FROM name JOIN language ON name.language_id = language.id"
    )
    if names:
        for name in names:
            generate_messages_for_name(conn, name[0], name[1], name[2], name[3])
        st.success("Generated messages for all names.")
    else:
        st.error("No names found.")

def generate_messages_for_name(conn, name_id, name, gender, language_id):
    """
    Generate messages for a specific name.
    """
    # Fetch language code and name
    language_info = fetch_one(conn, "SELECT code, name FROM language WHERE id = ?", (language_id,))
    if language_info:
        language_code = language_info[0]
        language_name = language_info[1]
    else:
        st.error(f"Language ID {language_id} not found for name ID {name_id}.")
        return

    message_types = ['greeting'] # ['greeting', 'morning', 'day', 'evening', 'night']
    for msg_type in message_types:
        message_text = generate_personal_text(name, msg_type, language_name)

        # Save message
        execute_query(conn,
            "INSERT INTO personal (name_id, text, type) VALUES (?, ?, ?)",
            (name_id, message_text, msg_type)
        )

        # Generate TTS for the message
        voice_id = get_voice_id(conn, language_id, gender)
        if voice_id:
            audio_stream = text_to_speech_stream(message_text, voice_id)
            s3_file_name = upload_audiostream_to_s3(audio_stream)
            execute_query(conn,
                "UPDATE personal SET audio_file = ? WHERE name_id = ? AND type = ?",
                (s3_file_name, name_id, msg_type)
            )
        else:
            st.error(f"No voice found for gender {gender} and language code {language_code}.")

    st.success(f"Generated messages for {name}.")

def get_voice_id(conn, language_id, gender):
    """
    Get the ElevenLabs voice ID for the given language and gender.
    """
    voice_record = fetch_one(conn,
        "SELECT elevenlabs_voice_id FROM voice WHERE language_id = ? AND gender = ? LIMIT 1",
        (language_id, gender)
    )
    if voice_record:
        return voice_record[0]
    else:
        st.error(f"No voice found for language ID {language_id} and gender {gender}.")
        return None