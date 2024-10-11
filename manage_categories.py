# manage_categories.py

import streamlit as st
from database import execute_query, fetch_all, fetch_one
import pandas as pd
from utils import clear_form_states
from openai_utils import generate_general_text, generate_themes_and_topics
from tts import text_to_speech_stream
from s3_utils import upload_audiostream_to_s3, generate_presigned_url

def manage_categories(conn):
    """
    Functions to manage categories.
    """
    st.header("Manage Categories")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    if col1.button("View All Categories"):
        clear_form_states()
        st.session_state['current_view'] = 'view_all'
    if col2.button("Add Category"):
        clear_form_states()
        st.session_state['show_add_form'] = True
    if col3.button("Bulk Add Categories"):
        clear_form_states()
        st.session_state['show_bulk_add_form'] = True

    # Handle different views
    if st.session_state.get('show_add_form', False):
        add_category(conn)
    elif st.session_state.get('show_bulk_add_form', False):
        bulk_add_categories(conn)
    elif st.session_state.get('show_update_form', False):
        update_category(conn, st.session_state['update_id'])
    elif st.session_state.get('show_category_page', False):
        category_page(conn, st.session_state['category_id'], st.session_state['category_name'])
    elif st.session_state.get('current_view') == 'view_all':
        view_all_categories(conn)

def view_all_categories(conn):
    """
    View all categories in the database.
    """
    st.subheader("All Categories")
    query = """
        SELECT category.id, category.name, language.code 
        FROM category 
        JOIN language ON category.language_id = language.id
    """
    data = fetch_all(conn, query)
    if data:
        for row in data:
            col1, col2, col3, col4, col5 = st.columns([3,2,2,2,2])
            col1.write(f"**{row[1]}**")  # Category Name
            col2.write(row[2])  # Language Code
            update_clicked = col3.button("Update", key=f"update_category_{row[0]}")
            delete_clicked = col4.button("Delete", key=f"delete_category_{row[0]}")
            view_clicked = col5.button("View", key=f"view_category_{row[0]}")
            if update_clicked:
                st.session_state['show_update_form'] = True
                st.session_state['update_id'] = row[0]
                st.session_state['current_view'] = None
                st.rerun()
            if delete_clicked:
                delete_category(conn, row[0])
                st.rerun()
            if view_clicked:
                st.session_state['category_id'] = row[0]
                st.session_state['category_name'] = row[1]
                st.session_state['show_category_page'] = True
                st.session_state['current_view'] = None
                st.rerun()
    else:
        st.info("No categories found. Please add categories.")

def add_category(conn):
    """
    Add a new category to the database.
    """
    st.subheader("Add Category")
    
    # Fetch languages
    languages = fetch_all(conn, "SELECT id, name FROM language")
    if languages:
        language_options = {name: id for id, name in languages}
        language_name = st.selectbox("Language", list(language_options.keys()), key="add_category_language")
        language_id = language_options[language_name]
    else:
        st.warning("No languages found. Please add languages first.")
        return  # Exit if no languages are available
    
    category_name = st.text_input("Category Name", key="add_category_input")
    if st.button("Save Category", key="save_category_button"):
        if category_name.strip():
            try:
                execute_query(conn, 
                    "INSERT INTO category (name, language_id) VALUES (?, ?)",
                    (category_name.strip(), language_id)
                )
                st.success(f"Added category '{category_name.strip()}'")
                clear_form_states()
                st.session_state['current_view'] = 'view_all'
                st.rerun()
            except Exception as e:
                st.error(f"Error adding category: {str(e)}")
        else:
            st.error("Category name cannot be empty.")

def bulk_add_categories(conn):
    """
    Bulk add categories from a CSV file.
    """
    st.subheader("Bulk Add Categories")
    uploaded_file = st.file_uploader("Upload CSV file with columns 'name', 'language_code'", type=["csv"], key="bulk_add_categories_uploader")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        required_columns = {'name', 'language_code'}
        if required_columns.issubset(df.columns):
            # Fetch languages
            languages = fetch_all(conn, "SELECT id, code FROM language")
            language_dict = {code: id for id, code in languages}
            records = []
            for _, row in df.iterrows():
                language_code = row['language_code']
                language_id = language_dict.get(language_code)
                if language_id:
                    records.append((row['name'], language_id))
                else:
                    st.warning(f"Language code '{language_code}' not found. Skipping category '{row['name']}'.")
            if st.button("Save Categories", key="save_bulk_categories_button"):
                success_count = 0
                for record in records:
                    try:
                        execute_query(conn, 
                            "INSERT INTO category (name, language_id) VALUES (?, ?)",
                            record
                        )
                        success_count += 1
                    except Exception as e:
                        st.warning(f"Skipped duplicate category: {record[0]}")
                st.success(f"Bulk added {success_count} categories.")
                clear_form_states()
                st.session_state['current_view'] = 'view_all'
                st.rerun()
        else:
            st.error(f"CSV must contain columns: {', '.join(required_columns)}")

def update_category(conn, category_id):
    """
    Update an existing category.
    """
    st.subheader("Update Category")
    category_record = fetch_one(conn, "SELECT name, language_id FROM category WHERE id = ?", (category_id,))
    if category_record:
        new_category_name = st.text_input("New Category Name", value=category_record[0], key="update_category_input")
        
        # Fetch languages
        languages = fetch_all(conn, "SELECT id, name FROM language")
        language_options = {name: id for id, name in languages}
        language_names = list(language_options.keys())
        current_language_name = next(name for name, id in language_options.items() if id == category_record[1])
        new_language_name = st.selectbox("Language", language_names, index=language_names.index(current_language_name), key="update_category_language")
        new_language_id = language_options[new_language_name]
        
        if st.button("Save Changes", key="update_category_button"):
            if new_category_name.strip():
                try:
                    execute_query(conn, 
                        "UPDATE category SET name = ?, language_id = ? WHERE id = ?",
                        (new_category_name.strip(), new_language_id, category_id)
                    )
                    st.success(f"Updated category to '{new_category_name.strip()}'")
                    clear_form_states()
                    st.session_state['current_view'] = 'view_all'
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating category: {str(e)}")
            else:
                st.error("Category name cannot be empty.")
    else:
        st.error("Category not found.")
        clear_form_states()
        st.session_state['current_view'] = 'view_all'

def delete_category(conn, category_id):
    """
    Delete a category from the database.
    """
    category_record = fetch_one(conn, "SELECT name FROM category WHERE id = ?", (category_id,))
    if category_record:
        execute_query(conn, "DELETE FROM category WHERE id = ?", (category_id,))
        st.success(f"Deleted category '{category_record[0]}'")
    else:
        st.error("Category not found.")

def category_page(conn, category_id, category_name):
    """
    Display the category page where themes and topics can be generated and managed.
    """
    st.subheader(f"Category: {category_name}")
    category_info = fetch_one(conn, "SELECT language_id FROM category WHERE id = ?", (category_id,))
    language_id = category_info[0]
    
    # Get language code and name
    language_info = fetch_one(conn, "SELECT code, name FROM language WHERE id = ?", (language_id,))
    language_code = language_info[0]
    language_name = language_info[1]

    gender = st.selectbox("Select Gender for Text Generation", ["male", "female"], key=f"gender_{category_id}")

    # Check if a voice exists for the selected gender and language
    matching_voice = fetch_one(conn, 
        "SELECT voice.id FROM voice WHERE language_id = ? AND gender = ?",
        (language_id, gender)
    )

    if not matching_voice:
        st.error(f"No voice available for gender '{gender}' and language '{language_name}'. Cannot generate themes and topics.")
        return

    category_description = st.text_area("Description", key="add_category_description")
    num_themes = st.number_input("Number of Themes", min_value=1, max_value=100, value=5, key=f"num_themes_{category_id}")
    num_topics = st.number_input("Number of Topics per Theme", min_value=1, max_value=100, value=5, key=f"num_topics_{category_id}")
    generate = st.button("Generate Themes and Topics", key=f"generate_themes_{category_id}")

    if generate:
        # Generate themes and topics using OpenAI API
        themes_and_topics_json = generate_themes_and_topics(category_name, category_description, int(num_themes), int(num_topics), language_code)
        import json
        try:
            data = json.loads(themes_and_topics_json)
            for theme in data.get("themes", []):
                theme_name = theme.get("theme_name")
                topics = theme.get("topics", [])
                for topic in topics:
                    try:
                        execute_query(conn, 
                            "INSERT INTO general (category_id, theme_name, topic_name, gender) VALUES (?, ?, ?, ?)",
                            (category_id, theme_name, topic, gender)
                        )
                    except Exception as e:
                        st.warning(f"Skipped duplicate theme/topic: {theme_name}/{topic}")
            st.success("Themes and topics generated and saved.")
            st.rerun()
        except Exception as e:
            st.error("Failed to parse JSON from OpenAI response.")
            st.error(f"Response was: {themes_and_topics_json}")
            return

    # Display themes and topics
    themes = fetch_all(conn, "SELECT DISTINCT theme_name FROM general WHERE category_id = ?", (category_id,))
    themes = [row[0] for row in themes]
    if themes:
        selected_theme = st.selectbox("Select Theme", themes, key=f"selected_theme_{category_id}")
        topics = fetch_all(conn, 
            "SELECT * FROM general WHERE category_id = ? AND theme_name = ?", 
            (category_id, selected_theme)
        )
        if topics:
            for topic in topics:
                topic_id = topic[0]
                topic_name = topic[3]
                st.write(f"**Topic:** {topic_name}")
                if st.button("Generate Text", key=f"generate_text_{topic_id}"):
                    text, symbols = generate_general_text(conn, category_id, selected_theme, topic_name, topic[7])  # topic[7] is gender
                    execute_query(conn, 
                        "UPDATE general SET text = ?, symbols = ? WHERE id = ?", 
                        (text, symbols, topic_id)
                    )
                    st.success(f"Generated text for topic '{topic_name}'")
                    st.rerun()
                if topic[4]:  # If text exists
                    st.write(f"**Text:** {topic[4]}")
                if st.button("Generate TTS", key=f"generate_tts_{topic_id}"):
                    # Get the ElevenLabs voice ID for the language and gender
                    voice_id = get_voice_id(conn, language_id, topic[7])
                    if voice_id:
                        audio_stream = text_to_speech_stream(topic[4], voice_id)
                        s3_file_name = upload_audiostream_to_s3(audio_stream)
                        execute_query(conn, 
                            "UPDATE general SET audio_file = ? WHERE id = ?", 
                            (s3_file_name, topic_id)
                        )
                        st.success(f"Generated TTS for topic '{topic_name}'")
                        st.rerun()
                    else:
                        st.error("No voice found for TTS generation.")
                if topic[5]:  # If audio_file exists
                    signed_url = generate_presigned_url(topic[5])
                    st.audio(signed_url)
        else:
            st.info("No topics found under this theme.")
    else:
        st.info("No themes found for this category.")

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
