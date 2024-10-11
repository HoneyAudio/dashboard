# sqlite_to_json.py

import sqlite3
import json

def sqlite_to_json(db_file, json_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    data = {}

    # Fetch languages
    cursor.execute("SELECT id, name, code FROM language")
    languages = cursor.fetchall()
    data['languages'] = [
        {'id': lang[0], 'name': lang[1], 'code': lang[2]}
        for lang in languages
    ]

    # Fetch voices
    cursor.execute("SELECT id, name, elevenlabs_voice_id, gender, language_id FROM voice")
    voices = cursor.fetchall()
    data['voices'] = [
        {
            'id': voice[0],
            'name': voice[1],
            'elevenlabs_voice_id': voice[2],
            'gender': voice[3],
            'language_id': voice[4],
        }
        for voice in voices
    ]

    # Fetch names
    cursor.execute("SELECT id, name, gender, language_id FROM name")
    names = cursor.fetchall()
    data['names'] = [
        {
            'id': name[0],
            'name': name[1],
            'gender': name[2],
            'language_id': name[3],
        }
        for name in names
    ]

    # Fetch categories
    cursor.execute("SELECT id, name, language_id FROM category")
    categories = cursor.fetchall()
    data['categories'] = [
        {
            'id': category[0],
            'name': category[1],
            'language_id': category[2],
        }
        for category in categories
    ]

    # Fetch personal messages
    cursor.execute("SELECT id, name_id, text, type, audio_file FROM personal")
    personals = cursor.fetchall()
    data['personal'] = [
        {
            'id': personal[0],
            'name_id': personal[1],
            'text': personal[2],
            'type': personal[3],
            'audio_file': personal[4],
        }
        for personal in personals
    ]

    # Fetch general messages
    cursor.execute("SELECT id, category_id, theme_name, topic_name, text, audio_file, symbols, gender FROM general")
    generals = cursor.fetchall()
    data['general'] = [
        {
            'id': general[0],
            'category_id': general[1],
            'theme_name': general[2],
            'topic_name': general[3],
            'text': general[4],
            'audio_file': general[5],
            'symbols': general[6],
            'gender': general[7],
        }
        for general in generals
    ]

    # Close the connection
    conn.close()

    # Write data to JSON file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    sqlite_to_json('mydatabase.db', 'data.json')
