import openai
from config import OPENAI_API_KEY

# Initialize OpenAI API key
openai.api_key = OPENAI_API_KEY

def generate_themes_and_topics(category_name, description, num_themes, num_topics, language_code):
    """
    Generate themes and topics using OpenAI API based on a category description.
    """
    prompt = f"""
        You are a highly skilled assistant helping to create a motivational and supportive experience for users. Based on the following description, generate {num_themes} distinct themes, each with {num_topics} topics, suited to the given category and context.

        The response should be in JSON format as follows:
        {{
            "themes": [
                {{
                    "theme_name": "Theme 1",
                    "topics": ["Topic 1", "Topic 2", ...]
                }},
                ...
            ]
        }}
        The response must be in the {language_code.upper()} language.

        Keep in mind the sensitive nature of the category and the user's emotional state. Make sure the themes and topics provide the appropriate kind of support or motivation as per the user's chosen category and language.

        Here are the details:
        Category: "{category_name}"
        Language: "{language_code.upper()}"
        Description: "{description}"

        Now, generate {num_themes} unique themes, each with {num_topics} motivating or supportive topics that align with the given category.
    """
    response = openai.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini",
    )
    content = response.choices[0].message.content.strip()
    return content  # You should parse the content as needed

def generate_general_text(conn, category_id, theme_name, topic_name, gender):
    cursor = conn.cursor()
    cursor.execute("SELECT language.name FROM category JOIN language ON category.language_id = language.id WHERE category.id = ?", (category_id,))
    language_name = cursor.fetchone()[0]
    # Fetch language_id
    cursor.execute("SELECT language_id FROM category WHERE id = ?", (category_id,))
    language_id = cursor.fetchone()[0]

    # Count existing texts for this theme, language, and gender
    cursor.execute("""
        SELECT COUNT(*) FROM general WHERE category_id = ? AND theme_name = ? AND gender = ? AND text IS NOT NULL
    """, (category_id, theme_name, gender))
    existing_texts_count = cursor.fetchone()[0]

    # Calculate character limit
    text_number = existing_texts_count + 1
    char_limit = 100 # text_number * 600  # Assuming 1 minute TTS = 600 characters

    # Generate prompt
    prompt = f"""
        Create an affectionate, motivational text for each topic in {language_name} language. 
        Theme: "{theme_name}"
        Topic: "{topic_name}"
        The text should be filled with affirmations, praise, encouragement, affectionate words, and motivation. 
        Use affectionate terms like 'kitten', 'sunshine', etc., and address the user with affectionate words appropriate for {gender}. 
        The text should not exceed {char_limit} characters.
    """

    response = openai.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini",
    )
    text = response.choices[0].message.content.strip()
    symbols = len(text)
    return text, symbols

def generate_personal_text(name, msg_type, language_name):
    """
    Create a prompt for generating a message of a specific type.
    """
    # Limit the generated text to 100 characters
    prompt_limit = 100

    # Placeholder for diminutive variants; implement logic as needed
    name_variants = name

    # Common prompt additions
    common_prompt = f"""
        Write a relaxed, slow-paced, and affectionate message in {language_name} for someone named {name_variants}.
        The message should be suitable for Text-to-Speech conversion and will be played in a whisper.
        Use ElevenLabs speech synthesis markup to add natural pauses where appropriate (e.g., <break time="1.0s" />).
        Make the text free-form and friendly and be sure to use the name in the text, if possible, names should be in diminutive form.
        The message must be in {language_name} language and contain no more than {prompt_limit} characters. 
    """

    if msg_type == 'greeting':
        prompt = common_prompt + "Create a personalized greeting."
    elif msg_type == 'morning':
        prompt = common_prompt + "Generate an inspiring morning message."
    elif msg_type == 'day':
        prompt = common_prompt + "Write a positive affirmation for the day."
    elif msg_type == 'evening':
        prompt = common_prompt + "Compose a relaxing evening message."
    elif msg_type == 'night':
        prompt = common_prompt + "Craft a thoughtful night message."
    else:
        prompt = common_prompt
    
    response = openai.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o-mini",
    )
    message_text = response.choices[0].message.content.strip()

    return message_text