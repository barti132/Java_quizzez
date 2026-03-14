import re
import json
import os
import sys

def extract_questions_and_answers(chapter_num):
    """
    Parsuje pliki tekstowe i konwertuje je na format JSON
    """
    
    questions_file = f"data/Chapter {chapter_num} - "
    answers_file = f"data/Chapter {chapter_num} - answers.txt"
    
    # Szukaj pliku pytań (nazwa może być inna dla każdego chapter)
    questions_file_path = None
    for file in os.listdir("data"):
        if file.startswith(f"Chapter {chapter_num}") and file.endswith(".txt") and "answers" not in file:
            questions_file_path = os.path.join("data", file)
            break
    
    if not questions_file_path:
        raise FileNotFoundError(f"Nie znaleziono pliku pytań dla Chapter {chapter_num}")
    
    if not os.path.exists(answers_file):
        raise FileNotFoundError(f"Nie znaleziono pliku: {answers_file}")
    
    # Odczytaj plik z pytaniami
    with open(questions_file_path, 'r', encoding='utf-8') as f:
        questions_text = f.read()
    
    # Odczytaj plik z odpowiedziami
    with open(answers_file, 'r', encoding='utf-8') as f:
        answers_text = f.read()
    
    questions_data = []
    
    # Split na poszczególne pytania - szukamy linii zaczynającej się od numeru
    question_blocks = re.split(r'\n(?=\d+\.)', questions_text)
    
    for block in question_blocks:
        if not block.strip():
            continue
        
        lines = block.strip().split('\n')
        
        # Najpierw linia to numer pytania
        match = re.match(r'(\d+)\.\s*(.*)', lines[0])
        if not match:
            continue
        
        q_id = int(match.group(1))
        first_line = match.group(2)
        
        # Zbierz tekst pytania (wszystkie linie do pierwszej opcji)
        question_lines = [first_line]
        current_position = 1
        
        # Zbierz wszystkie linie pytania aż do opcji
        while current_position < len(lines):
            line = lines[current_position]
            # Sprawdź czy to opcja (A., B., C., etc.)
            if re.match(r'^[A-Z]\.\s*', line):
                break
            question_lines.append(line)
            current_position += 1
        
        question_text = '\n'.join(question_lines).strip()
        
        # Teraz zbierz opcje
        options = []
        while current_position < len(lines):
            line = lines[current_position]
            
            # Check if line starts with option letter
            option_match = re.match(r'^([A-Z])\.\s*(.*)', line)
            if option_match:
                letter = option_match.group(1)
                text_lines = [option_match.group(2)]
                current_position += 1
                
                # Zbierz następne linie należące do tej opcji
                while current_position < len(lines):
                    next_line = lines[current_position]
                    # Sprawdź czy to nowa opcja
                    if re.match(r'^[A-Z]\.\s*', next_line):
                        break
                    # Jeśli linia ma zawartość, dodaj ją
                    if next_line.strip():
                        text_lines.append(next_line)
                    current_position += 1
                
                option_text = ' '.join(text_lines).strip()
                options.append({
                    "letter": letter,
                    "text": option_text
                })
            else:
                current_position += 1
        
        # Teraz szukaj odpowiedzi i wyjaśnienia w pliku answers
        # Szukamy linii zaczynającej się od "numer. A/B/C..."
        answer_pattern = rf'{q_id}\.\s*([A-Z,\s]+)\.'
        answer_match = re.search(answer_pattern, answers_text)
        
        if answer_match:
            correct_answer = answer_match.group(1).strip().replace(' ', '')
        else:
            correct_answer = ""
        
        # Szukaj wyjaśnienia (wszystko po odpowiedzi do następnego pytania)
        # Patrz dla "numer. ODPOWIEDŹ. tekst ... następne pytanie"
        explanation_pattern = rf'{q_id}\.\s*[A-Z,\s]+\.\s+(.*?)(?=\n{q_id + 1}\.|$)'
        explanation_match = re.search(explanation_pattern, answers_text, re.DOTALL)
        
        if explanation_match:
            explanation = explanation_match.group(1).strip()
            # Usuń oznaczenia rozdziałów na końcu
            explanation = re.sub(r'Chapter \d+:.*$', '', explanation, flags=re.MULTILINE).strip()
        else:
            explanation = ""
        
        if options:  # Dodaj tylko jeśli mamy opcje
            questions_data.append({
                "id": q_id,
                "question": question_text.strip(),
                "options": options,
                "correct": correct_answer,
                "explanation": explanation
            })
    
    return questions_data, questions_file_path

def main():
    if len(sys.argv) > 1:
        chapter_num = sys.argv[1]
    else:
        chapter_num = input("Podaj numer chapter (1-14): ")
    
    print(f"Konwertowanie Chapter {chapter_num}...")
    
    try:
        questions, questions_file_path = extract_questions_and_answers(chapter_num)
        
        # Odczytaj nazwę rozdziału z pliku pytań
        chapter_title = os.path.basename(questions_file_path).replace(".txt", "")
        
        # Tworz strukturę JSON
        quiz_data = {
            "chapter": chapter_title,
            "totalQuestions": len(questions),
            "questions": questions
        }
        
        # Zapisz do pliku JSON
        output_file = f"data/chapter{chapter_num}.json"
        
        # Utwórz katalog jeśli nie istnieje
        os.makedirs("data", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(quiz_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Pomyślnie konwertowano {len(questions)} pytań!")
        print(f"✓ Plik zapisany: {output_file}")
        print(f"\nPierwsze pytanie:")
        print(f"  ID: {questions[0]['id']}")
        print(f"  Pytanie: {questions[0]['question'][:50]}...")
        print(f"  Opcji: {len(questions[0]['options'])}")
        print(f"  Odpowiedź: {questions[0]['correct']}")
        
    except FileNotFoundError as e:
        print(f"✗ Błąd: {e}")
        print("Dostępne chapter:", [i for i in range(1, 15)])
    except Exception as e:
        print(f"✗ Błąd podczas konwersji: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
