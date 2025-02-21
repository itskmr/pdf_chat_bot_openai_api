import os
from flask import Flask, request, render_template_string
import pdfplumber
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Global variable to store extracted PDF text (for demo purposes)
knowledge_base = ""

# Improved HTML template using Bootstrap for styling
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>PDF Chatbot App</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- Bootstrap CSS -->
  <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      background-color: #f8f9fa;
    }
    .container {
      margin-top: 50px;
    }
    .card {
      margin-bottom: 20px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1 class="text-center mb-4">PDF Chatbot App</h1>
    
    <div class="card">
      <div class="card-header">Upload PDF</div>
      <div class="card-body">
        <form action="/upload" method="post" enctype="multipart/form-data">
          <div class="form-group">
            <input type="file" name="pdf_file" class="form-control-file" required>
          </div>
          <button type="submit" class="btn btn-primary">Upload</button>
        </form>
      </div>
    </div>
    
    <div class="card">
      <div class="card-header">Ask a Question</div>
      <div class="card-body">
        <form action="/ask" method="post">
          <div class="form-group">
            <input type="text" name="question" placeholder="Your question here" class="form-control" required>
          </div>
          <button type="submit" class="btn btn-success">Ask</button>
        </form>
      </div>
    </div>
    
    {% if answer %}
    <div class="card">
      <div class="card-header">Answer</div>
      <div class="card-body">
        <p class="card-text">{{ answer }}</p>
      </div>
    </div>
    {% endif %}
    
  </div>
  
  <!-- Bootstrap JS and dependencies -->
  <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.1/dist/umd/popper.min.js"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>
</html>
"""

def extract_text_from_pdf(pdf_path):
    """Extracts text from the given PDF file using pdfplumber."""
    all_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"
    return all_text

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/upload", methods=["POST"])
def upload_pdf():
    global knowledge_base
    if 'pdf_file' not in request.files:
        return "No file part", 400
    file = request.files['pdf_file']
    if file.filename == "":
        return "No selected file", 400

    temp_filename = "temp_uploaded.pdf"
    file.save(temp_filename)
    knowledge_base = extract_text_from_pdf(temp_filename)
    os.remove(temp_filename)
    return render_template_string(HTML_TEMPLATE, answer="PDF uploaded and processed successfully!")

def get_chatbot_response(question, context):
    """Calls OpenAI's API to get an answer based on the provided context."""
    prompt = f"Based on the following information:\n\n{context}\n\nAnswer the question: {question}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a knowledgeable assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

@app.route("/ask", methods=["POST"])
def ask_question():
    question = request.form.get("question", "")
    if not question:
        return render_template_string(HTML_TEMPLATE, answer="Please ask a question.")
    if not knowledge_base:
        return render_template_string(HTML_TEMPLATE, answer="Please upload a PDF first.")
    answer = get_chatbot_response(question, knowledge_base)
    return render_template_string(HTML_TEMPLATE, answer=answer)

if __name__ == '__main__':
    app.run(debug=True)
