from flask import Flask, request, jsonify, render_template
import torch
import librosa
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import openai
import logging
import re
import numpy as np

# Set your OpenAI API key
openai.api_key = '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'

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load Wav2Vec2.0 processor and model from local directory
model_path = "models/wav2vec2-large-xlsr-53-english"
processor = Wav2Vec2Processor.from_pretrained(model_path)
model = Wav2Vec2ForCTC.from_pretrained(model_path)

def preprocess_transcription(transcription):
    cleaned_transcription = re.sub(r'[^a-zA-Z\s]', '', transcription)
    cleaned_transcription = re.sub(r'\s+', ' ', cleaned_transcription).strip()
    return cleaned_transcription

def analyze_pauses(audio_input, sample_rate, threshold=0.3):
    intervals = librosa.effects.split(audio_input, top_db=30)
    pauses = []
    for i in range(1, len(intervals)):
        pause_duration = (intervals[i][0] - intervals[i-1][1]) / sample_rate
        if pause_duration > threshold:
            pauses.append(pause_duration)
    return pauses

def speech_to_text(audio_path):
    try:
        audio_input, sample_rate = librosa.load(audio_path, sr=16000)
        input_values = processor(audio_input, return_tensors="pt", sampling_rate=16000).input_values
        with torch.no_grad():
            logits = model(input_values).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.decode(predicted_ids[0])
        return transcription
    except Exception as e:
        logging.error(f"Error in speech_to_text: {e}")
        raise

def openai_request(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        logging.error(f"Error in openai_request: {e}")
        raise

def analyze_fluency_coherence(text, pauses, part):
    total_pause_duration = sum(pauses)
    number_of_pauses = len(pauses)
    average_pause_duration = np.mean(pauses) if pauses else 0

    prompt = (
        f"The following text is a transcript generated from speech, and it may contain errors due to speech recognition.\n\n"
        f"Context: This transcript is from IELTS Speaking Part {part}, which requires the speaker to discuss personal topics, familiar subjects, or abstract ideas depending on the part.\n\n"
        f"Total Pause Duration: {total_pause_duration:.2f} seconds\nNumber of Pauses: {number_of_pauses}\nAverage Pause Duration: {average_pause_duration:.2f} seconds\n\n"
        f"Transcript:\n{text}\n\n"
        "Please analyze the text for fluency and coherence, focusing on pauses, hesitations, and overall flow. Provide a score from 1 to 9 and detailed feedback on how the speaker can improve their fluency and coherence."
    )
    return openai_request(prompt)

def analyze_grammar(text):
    prompt = (
        f"The following text is a transcript generated from speech, and it may contain errors due to speech recognition.\n\n"
        "Context: This is from an IELTS Speaking test, where the speaker discusses various topics. The analysis should focus on the grammatical range and accuracy in the given context.\n\n"
        f"Transcript:\n{text}\n\n"
        "Evaluate the text for grammatical range and accuracy, considering the use of different tenses, complex sentences, and overall grammatical correctness. Provide a score from 1 to 9 and detailed feedback, including specific examples of errors and suggestions for improvement."
    )
    return openai_request(prompt)

def analyze_lexical_resource(text):
    prompt = (
        f"The following text is a transcript generated from speech, and it may contain errors due to speech recognition.\n\n"
        "Context: This is from an IELTS Speaking test, where the speaker needs to demonstrate a wide range of vocabulary. The analysis should focus on the use of collocations, idioms, idiomatic expressions, and binomial expressions.\n\n"
        f"Transcript:\n{text}\n\n"
        "Evaluate the text for lexical resource, considering the variety and appropriateness of vocabulary used. Provide a score from 1 to 9 and detailed feedback, highlighting the use of advanced vocabulary, idiomatic expressions, and any areas for improvement."
    )
    return openai_request(prompt)

def analyze_pronunciation(transcription):
    prompt = (
        f"The following text is a transcript generated from speech, and it may contain errors due to speech recognition.\n\n"
        "Context: This is from an IELTS Speaking test, and the evaluation is based on the transcript of an audio recording. Pronunciation may not be perfectly captured due to transcription errors.\n\n"
        f"Transcript:\n{transcription}\n\n"
        "Evaluate the text for pronunciation, considering the clarity and accuracy of the spoken words. Provide a score from 1 to 9 and detailed feedback, noting that some pronunciation nuances might be lost in transcription."
    )
    return openai_request(prompt)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        part = request.form['part']
        file = request.files['file']
        audio_path = 'uploaded_audio.wav'
        file.save(audio_path)

        logging.info(f"File saved: {audio_path}")  # Debugging info

        transcription = speech_to_text(audio_path)
        cleaned_transcription = preprocess_transcription(transcription)

        audio_input, sample_rate = librosa.load(audio_path, sr=16000)
        pauses = analyze_pauses(audio_input, sample_rate)

        fluency_feedback = analyze_fluency_coherence(transcription, pauses, part)
        grammar_feedback = analyze_grammar(cleaned_transcription)
        lexical_feedback = analyze_lexical_resource(cleaned_transcription)
        pronunciation_feedback = analyze_pronunciation(transcription)

        return jsonify({
            "fluency_feedback": fluency_feedback,
            "grammar_feedback": grammar_feedback,
            "lexical_feedback": lexical_feedback,
            "pronunciation_feedback": pronunciation_feedback
        })
    except Exception as e:
        logging.error(f"Error in /analyze route: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
