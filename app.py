from flask import Flask, render_template, jsonify, request
import json
import random
import os
import shutil
import pandas as pd
import google.generativeai as genai
# REMOVED: from dotenv import load_dotenv (Not needed on Render)

app = Flask(__name__)

# --- 🔐 CONFIGURATION ---
# Use Environment Variable if available (Render), else fallback to hardcoded (Local)
# This single line works perfectly in both places without dotenv!
MY_GOOGLE_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyAfGw2eXQzIvShLCdXDIhpPDtBq1GDRhxk")
genai.configure(api_key=MY_GOOGLE_KEY)

# --- DATA LOADING ---
def classify_subject(text):
    text = str(text).lower()
    bio = ['cell', 'organism', 'blood', 'plant', 'animal', 'dna', 'protein']
    phys = ['velocity', 'force', 'energy', 'gravity', 'volt', 'motion', 'light']
    chem = ['acid', 'atom', 'molecule', 'reaction', 'element', 'bond', 'organic']
    
    b = sum(1 for k in bio if k in text)
    p = sum(1 for k in phys if k in text)
    c = sum(1 for k in chem if k in text)
    
    if b >= p and b >= c: return 'biology'
    if p >= b and p >= c: return 'physics'
    return 'chemistry'

def ensure_database_exists():
    json_path = os.path.join(app.root_path, 'questions.json')
    csv_path = os.path.join(app.root_path, 'train.csv')
    
    if os.path.exists(json_path): return

    if os.path.exists(csv_path):
        print("⚙️ Converting CSV to JSON...")
        try:
            df = pd.read_csv(csv_path)
            output_data = {"physics": [], "chemistry": [], "biology": []}
            
            for index, row in df.iterrows():
                q_text = str(row['question']).strip()
                correct = str(row['correct_answer']).strip()
                explanation = str(row['support']).strip()
                if explanation.lower() == "nan" or explanation == "": 
                    explanation = "Explanation not available."

                subject = classify_subject(q_text + " " + correct)
                options = [str(row['distractor1']), str(row['distractor2']), str(row['distractor3']), correct]
                options = [opt for opt in options if opt.lower() != 'nan']
                
                if len(options) == 4:
                    random.shuffle(options)
                    output_data[subject].append({
                        "id": f"{subject[0]}{index}",
                        "question": q_text,
                        "options": options,
                        "answer": correct,
                        "explanation": explanation,
                        "subject": subject.capitalize()
                    })

            with open(json_path, 'w') as f: json.dump(output_data, f, indent=2)
            print(f"✅ Database Ready!")
        except Exception as e: print(f"❌ CSV Error: {e}")

ensure_database_exists()

def load_questions():
    path = os.path.join(app.root_path, 'questions.json')
    if not os.path.exists(path): return {}
    with open(path, 'r') as f: return json.load(f)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/get_exam')
def get_exam():
    data = load_questions()
    try: count = int(request.args.get('count', 10))
    except: count = 10
    exam_paper = []
    per_subject = count // 3
    for subject in ['physics', 'chemistry', 'biology']:
        if subject in data:
            questions = data[subject]
            k = min(len(questions), per_subject)
            selection = random.sample(questions, k)
            exam_paper.extend(selection)
    if len(exam_paper) < count:
        all_q = []
        for s in data: all_q.extend(data[s])
        needed = count - len(exam_paper)
        if needed > 0: exam_paper.extend(random.sample(all_q, min(len(all_q), needed)))
    random.shuffle(exam_paper)
    return jsonify(exam_paper)

@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.json
    user_answers = data.get('answers', {})
    paper = data.get('paper', [])
    time_taken = data.get('time_taken', 0)
    
    score = 0; correct = 0; wrong = 0; skipped = 0
    detailed_result = []
    
    for q in paper:
        q_id = q['id']
        user_selected = user_answers.get(q_id, None)
        is_correct = (user_selected == q['answer'])
        
        if user_selected:
            if is_correct: score += 4; correct += 1
            else: score -= 1; wrong += 1
        else: skipped += 1

        detailed_result.append({
            "id": q_id, "question": q['question'],
            "user_answer": user_selected if user_selected else "Skipped",
            "correct_answer": q['answer'],
            "status": "correct" if is_correct else ("wrong" if user_selected else "skipped"),
            "explanation": q.get('explanation', "No explanation available.")
        })

    total = len(paper)
    attempted = correct + wrong
    max_marks = total * 4
    acc = (correct/total)*100 if total>0 else 0
    prec = (correct/attempted)*100 if attempted>0 else 0
    speed = time_taken/attempted if attempted>0 else 0

    feedback = "Keep practicing!"
    badge = "Student"
    if prec > 90 and attempted > 0: feedback = "🎯 Precision Sniper!"; badge = "Sniper"
    elif speed < 15 and prec < 60: feedback = "⚠️ You're rushing!"; badge = "Speedster"
    elif acc > 80: feedback = "🏆 Topper Material!"; badge = "Topper"

    return jsonify({
        "score": score, "max_marks": max_marks, "correct": correct, "wrong": wrong,
        "accuracy": round(acc, 1), "precision": round(prec, 1), "avg_speed": round(speed, 1),
        "feedback": feedback, "badge": badge, "analysis": detailed_result
    })

# --- AI CHAT ---
@app.route('/api/chat_ai', methods=['POST'])
def chat_ai():
    data = request.json
    user_query = data.get('query', '')
    context = data.get('context', '')

    prompt = f"""
    You are Hari, a supportive boyfriend helping Harini study for NEET.
    Question: {context}
    Her Doubt: {user_query}
    Explain simply (max 3 sentences). Be encouraging. Use 'we' and 'us'. No markdown.
    """
    
    try:
        # Using gemini-2.5-flash as verified earlier
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"Gemini Error: {e}")
        return jsonify({"reply": "My AI brain is busy. Try again!"})

if __name__ == '__main__':
    app.run(debug=True, port=5001)