import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
from io import BytesIO
from pydub import AudioSegment
import base64
import os
import tempfile

st.title('Webpage Summary and Audio Extractinator')

# Initialize session state for API key and its submission status
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ''
if 'key_submitted' not in st.session_state:
    st.session_state['key_submitted'] = False

# Function to handle API key submission
def submit_api_key():
    st.session_state['api_key'] = api_key_input
    st.session_state['key_submitted'] = True
    st.sidebar.success("API Key submitted successfully!")

# API Key Input in Sidebar
api_key_input = st.sidebar.text_input("Enter your OpenAI API Key", type="password", key="api_key_input")
st.sidebar.button('Submit API Key', on_click=submit_api_key)

# Extract content from URL
def extract_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        return None, f"Error fetching URL {url}: {e}"

    soup = BeautifulSoup(response.content, 'html.parser')
    content = [tag.text.strip() for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'])]
    full_text = ' '.join(content)
    return content, full_text

# Summarize text using OpenAI
def summarize_text(text, api_key):
    openai.api_key = api_key
    try:
        response = openai.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[{"role": "user", "content": f"Summarize the following text in less than 150 words based on the langauge it is written in:\n{text}"}],
                max_tokens=700
            )
        print(response)
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        return f"Error in generating summary: {e}\n{response}"


# Function to convert summary to speech
def text_to_speech(summary, api_key):
    openai.api_key = api_key
    try:
        response = openai.audio.speech.create(
            model="tts-1",
            voice="shimmer",
            input=summary
        )

        # Write the audio content to a temporary file
        temp_audio_path = 'temp_audio.mp3'
        with open(temp_audio_path, "wb") as audio_file:
            audio_file.write(response.content)

        return temp_audio_path
    except Exception as e:
        print("Exception occurred:", e)
        return None


# Function to create audio player
def create_audio_player(audio_data):
    audio = AudioSegment.from_file(BytesIO(audio_data), format="mp3")
    audio_file = BytesIO()
    audio.export(audio_file, format="mp3")
    base64_audio = base64.b64encode(audio_file.getvalue()).decode()
    audio_html = f'<audio controls><source src="data:audio/mp3;base64,{base64_audio}" type="audio/mpeg"></audio>'
    return audio_html

# Main functionality
if st.session_state['api_key'] and st.session_state['key_submitted']:
    urls = st.text_area("Enter a URL:", key="url_input").split("\n")

    if st.button('Extract and Summarize'):
        for url in urls:
            if url.strip():
                content, full_text = extract_content(url)
                if full_text:
                    summary = summarize_text(full_text, st.session_state['api_key'])
                    st.subheader(f"Summary for {url}")
                    st.write(summary)

                    # Text to Speech
                    audio_file_path = text_to_speech(summary, st.session_state['api_key'])
                    if audio_file_path:
                        st.audio(audio_file_path, format="audio/mp3")
                    else:
                        st.error("Error in generating audio")
else:
    st.sidebar.warning("Please enter your OpenAI API Key to use this app.")
