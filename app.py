import random
from flask import Flask, render_template, request
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
import pytesseract
import cv2
import nltk

app = Flask(__name__)

# Download NLTK resources if not already downloaded
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# Set the Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

def extract_keywords(content):
    sentences = sent_tokenize(content)
    keywords = []
    for sentence in sentences:
        words = word_tokenize(sentence)
        tagged_words = pos_tag(words)
        nouns = [word for word, pos in tagged_words if pos.startswith('NN')]
        keywords.extend(nouns)

    stop_words = set(stopwords.words('english'))
    keywords = [word.lower() for word in keywords if word.lower() not in stop_words]
    return keywords

def extract_text_from_image(image_path):
    try:
        image = cv2.imread(image_path)
        if image is not None:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(gray)
            return text.strip()
        else:
            return "Error: Unable to read the image file. Please make sure the file exists and is a valid image."
    except Exception as e:
        return f"Error extracting text from image: {str(e)}"

def generate_option(sentences, selected_index, correct_option):
    if len(sentences) <= 1:
        return []

    incorrect_indices = [i for i in range(len(sentences)) if i != selected_index and sentences[i] != correct_option]
    if not incorrect_indices:
        return []

    random.shuffle(incorrect_indices)
    options = []

    for i, idx in enumerate(incorrect_indices[:3]):
        option_text = f"{sentences[idx]} (Option {chr(ord('A') + i)})"
        options.append(option_text)

    options.append(f"{correct_option} (Option D)")
    return options

def generate_question(content, question_word, question_type):
    sentences = sent_tokenize(content)
    relevant_sentences = [sentence for sentence in sentences if question_word in sentence.lower()]

    if not relevant_sentences:
        return f"No relevant information found for {question_word}", None, None, None

    selected_sentence = random.choice(relevant_sentences)
    sentence_index = sentences.index(selected_sentence)

    nearby_sentences = [sentences[i] for i in range(max(0, sentence_index - 1), min(len(sentences), sentence_index + 2)) if i != sentence_index]
    if not nearby_sentences:
        return f"No nearby sentences found for {question_word}", None, None, None

    correct_option = random.choice(nearby_sentences)

    if question_type == 'mcqs':
        question = f"What does '{question_word}' represent in the following sentence?<br><br>'{selected_sentence}'"
        options = generate_option(sentences, sentence_index, correct_option)
        random.shuffle(options)
        correct_option_text = f"The correct option is: {correct_option}"
        hint = f"A helpful hint related to the correct answer based on the content: '{selected_sentence}'"
    elif question_type == 'theory':
        question = f"Explain '{question_word}' in the context of the following sentence?<br><br>'{selected_sentence}'"
        options = []
        correct_option_text = ""
        hint = ""

    return question, options, correct_option_text, hint

@app.route('/')
def quiz_form():
    return render_template('quiz_form.html')

@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    user_choice = request.form['user_choice']

    if user_choice == '1':
        content = request.form['text_content']
    elif user_choice == '2':
        image_path = request.form['image_path']
        content = extract_text_from_image(image_path)
    else:
        return "Invalid choice. Please go back and choose '1' or '2'."

    num_questions = int(request.form['num_questions'])
    num_questions = min(num_questions, 10)

    difficulty_level = request.form['difficulty_level'].lower()
    question_type = request.form['question_type'].lower()

    question_keywords = extract_keywords(content)
    num_questions = min(num_questions, len(question_keywords))
    selected_questions = random.sample(question_keywords, num_questions)

    quiz_data = []

    for i, question_word in enumerate(selected_questions, start=1):
        question, options, correct_option_text, hint = generate_question(content, question_word, question_type)

        quiz_data.append({
            'question_number': i,
            'question': question,
            'options': options,
            'hint': hint,
            'correct_option_text': correct_option_text
        })

    return render_template('quiz_result.html', quiz_data=quiz_data, difficulty_level=difficulty_level)

if __name__ == '__main__':
    app.run(debug=True)
