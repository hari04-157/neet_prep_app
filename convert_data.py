import pandas as pd
import json
import random
import os

def classify_subject(text):
    text = str(text).lower()
    bio_words = ['cell', 'organism', 'blood', 'plant', 'animal', 'dna', 'protein', 'enzyme', 'bio', 'life', 'tissue', 'brain', 'heart', 'leaf', 'root', 'species']
    phys_words = ['velocity', 'force', 'energy', 'gravity', 'volt', 'motion', 'light', 'sound', 'wave', 'magnet', 'thermodynamic', 'speed', 'acceleration', 'friction']
    chem_words = ['acid', 'atom', 'molecule', 'reaction', 'element', 'chemical', 'bond', 'electron', 'proton', 'organic', 'solution', 'compound', 'oxidation']
    
    b = sum(1 for k in bio_words if k in text)
    p = sum(1 for k in phys_words if k in text)
    c = sum(1 for k in chem_words if k in text)
    
    if b >= p and b >= c: return 'biology'
    if p >= b and p >= c: return 'physics'
    if c >= b and c >= p: return 'chemistry'
    return 'biology' # Default

def convert():
    print("⏳ Reading 'train.csv'... Please wait.")
    if not os.path.exists('train.csv'):
        print("❌ Error: 'train.csv' not found! Please put the file in this folder.")
        return

    try:
        df = pd.read_csv('train.csv')
        output_data = {"physics": [], "chemistry": [], "biology": []}
        
        for index, row in df.iterrows():
            q_text = str(row['question']).strip()
            correct = str(row['correct_answer']).strip()
            explanation = str(row['support']).strip()
            
            if explanation.lower() == "nan" or explanation == "": 
                explanation = "Explanation not available for this question."

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

        with open('questions.json', 'w') as f:
            json.dump(output_data, f, indent=2)
            
        print(f"✅ Success! Processed {len(df)} questions.")
        print(f"   - Physics: {len(output_data['physics'])}")
        print(f"   - Chemistry: {len(output_data['chemistry'])}")
        print(f"   - Biology: {len(output_data['biology'])}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    convert()