# lambda_function.py

import json
import random
import boto3
import os

# Load the JSON data once when the Lambda function is initialized
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Initialize AWS S3 client
s3_client = boto3.client('s3')

AWS_S3_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME')

def generate_presigned_url(s3_file_name):
    signed_url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': AWS_S3_BUCKET_NAME, 'Key': s3_file_name},
        ExpiresIn=3600,
    )
    return signed_url

def lambda_handler(event, context):
    path = event.get('rawPath')
    if path == '/options':
        return get_options()
    elif path == '/simulateAPICall':
        # Extract query parameters
        params = event.get('queryStringParameters', {})
        selectedVoice = params.get('selectedVoice')
        selectedLanguage = params.get('selectedLanguage')
        selectedName = params.get('selectedName')
        selectedTopic = params.get('selectedTopic')
        return simulate_api_call(selectedVoice, selectedLanguage, selectedName, selectedTopic)
    else:
        return {
            'statusCode': 404,
            'body': json.dumps({'message': 'Not Found'}),
        }

def get_options():
    # Prepare voice options
    voice_options = [
        {
            'text': f"{'👩' if voice['gender'] == 'female' else '👨'} {voice['name']}",
            'value': str(voice['id']),
            'gender': 1 if voice['gender'] == 'female' else 0,
        }
        for voice in data['voices']
    ]

    # Prepare language options
    language_options = [
        {
            'text': f"{get_language_flag(lang['code'])} {lang['name']}",
            'value': lang['code'],
            'id': str(lang['id']),
        }
        for lang in data['languages']
    ]

    # Prepare name options
    name_options = [
        {
            'text': name['name'],
            'value': str(name['id']),
            'gender': 1 if name['gender'] == 'female' else 0,
            'language_id': str(name['language_id']),
        }
        for name in data['names']
    ]

    # Prepare topic options
    topics = set()
    for general in data['general']:
        topics.add(general['theme_name'])
    topic_options = [
        {
            'text': general['theme_name'],
            'value': general['theme_name'],
        }
        for general in data['general']
    ]
    topic_options = [dict(t) for t in {tuple(d.items()) for d in topic_options}]  # Remove duplicates

    response = {
        'voiceOptions': voice_options,
        'languageOptions': language_options,
        'nameOptions': name_options,
        'topicOptions': topic_options,
    }

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',  # Adjust as needed
            'Content-Type': 'application/json',
        },
        'body': json.dumps(response),
    }

def simulate_api_call(selectedVoice, selectedLanguage, selectedName, selectedTopic):
    # Find the name
    name = next((n for n in data['names'] if str(n['id']) == selectedName), None)
    if not name:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Name not found'}),
        }

    # Find the personal greeting
    personal_greetings = [
        p for p in data['personal']
        if str(p['name_id']) == selectedName and p['type'] == 'greeting'
    ]
    if not personal_greetings:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Personal greeting not found'}),
        }

    # Get the audio file and generate presigned URL
    greeting_audio_file = personal_greetings[0]['audio_file']
    greeting_url = generate_presigned_url(greeting_audio_file)

    # Find general messages based on selected options
    general_messages = [
        g for g in data['general']
        if g['theme_name'] == selectedTopic
        and g['gender'] == name['gender']
        and str(g['category_id']) in [str(c['id']) for c in data['categories'] if str(c['language_id']) == str(name['language_id'])]
    ]

    # Randomly select up to 5 audio files
    selected_general_messages = random.sample(general_messages, min(5, len(general_messages)))

    general_audio_urls = [
        generate_presigned_url(g['audio_file']) for g in selected_general_messages
    ]

    # Combine greeting and general audio files
    audio_files = [greeting_url] + general_audio_urls

    response = {
        'audioFiles': audio_files,
    }

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',  # Adjust as needed
            'Content-Type': 'application/json',
        },
        'body': json.dumps(response),
    }

def get_language_flag(code):
    # Map language codes to flag emojis
    flags = {
        'en': '🇺🇸',
        'de': '🇩🇪',
        'es': '🇪🇸',
        'fr': '🇫🇷',
        'it': '🇮🇹',
        'pt': '🇵🇹',
    }
    return flags.get(code, '')

