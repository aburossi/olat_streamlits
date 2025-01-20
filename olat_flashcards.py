import streamlit as st
import re
import random
import json

# Function Definitions
def clean_back_text(back_text):
    """Cleans specific characters from the back text."""
    return re.sub(r"[📌🔍👉]", "", back_text).strip()

def replace_ss_with_ss(text):
    """Replaces 'ß' with 'ss'."""
    return text.replace("ß", "ss")

def parse_flashcards(text):
    """Parses the input flashcards into structured data."""
    blocks = text.strip().split('\n\n')
    flashcards = []
    max_back_lines = 0  # To track the maximum number of back lines

    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if len(lines) < 2:
            continue  # At least front and one back line
        front = replace_ss_with_ss(lines[0])  # Replace ß with ss
        backs = [replace_ss_with_ss(line) for line in lines[1:]]
        clean_backs = [clean_back_text(back) for back in backs]
        flashcards.append({
            "front": front,
            "clean_backs": clean_backs
        })
        if len(clean_backs) > max_back_lines:
            max_back_lines = len(clean_backs)

    return flashcards, max_back_lines

def check_uniform_back_lines(flashcards):
    """Checks if all flashcards have the same number of back lines."""
    if not flashcards:
        return False, 0
    first_len = len(flashcards[0]["clean_backs"])
    for card in flashcards:
        if len(card["clean_backs"]) != first_len:
            return False, first_len
    return True, first_len

def generate_questions(flashcards, correct_line_index, title, n_correct):
    """Generates question sets based on flashcards."""
    questions = []
    total_fronts = 8
    if len(flashcards) < total_fronts:
        return questions

    for _ in range(len(flashcards)):  # Iterate enough times to generate multiple questions
        # Select n_correct correct fronts
        selected_correct_fronts = random.sample(flashcards, n_correct)
        selected_correct_backs = []
        for front in selected_correct_fronts:
            try:
                back = front["clean_backs"][correct_line_index]
                selected_correct_backs.append(back)
            except IndexError:
                # Skip if any selected front does not have the required back line
                selected_correct_backs = []
                break

        if len(selected_correct_backs) != n_correct:
            continue  # Skip this iteration if backs are insufficient

        # Select (total_fronts - n_correct) incorrect fronts
        remaining_flashcards = [c for c in flashcards if c not in selected_correct_fronts]
        if len(remaining_flashcards) < (total_fronts - n_correct):
            continue  # Not enough incorrect fronts
        selected_incorrect_fronts = random.sample(remaining_flashcards, total_fronts - n_correct)

        # **Keine Shuffle der Backs**
        shuffled_backs = selected_correct_backs.copy()

        # Assign each correct front to one back using front text as key
        front_to_back = dict(zip([c["front"] for c in selected_correct_fronts], shuffled_backs))

        # Combine correct and incorrect fronts
        all_fronts = selected_correct_fronts + selected_incorrect_fronts
        random.shuffle(all_fronts)

        # Prepare the question data
        question_data = []
        backs_header = [""] + shuffled_backs
        num_columns = len(backs_header)

        # Helper function to pad rows
        def pad_row(row, total_cols):
            return row + [""] * (total_cols - len(row))

        # Add Typ, Title, Question, Points with padding
        question_data.append(pad_row(["Typ", "Drag&drop"], num_columns))
        question_data.append(pad_row(["Title", title], num_columns))
        question_data.append(pad_row(
            [ "Question", f"Ordnen Sie die Begriffe den korrekten Erklärungen zu. ❗ Achtung: Genau {n_correct} Begriffe können zugeordnet werden."],
            num_columns
        ))
        question_data.append(pad_row(["Points", f"{0.5 * n_correct}"], num_columns))

        # Add backs_header
        question_data.append(backs_header)

        # Add front cards with points
        for front in all_fronts:
            row = [front["front"]]
            if front["front"] in front_to_back:
                correct_back = front_to_back[front["front"]]
                for back in shuffled_backs:
                    if back == correct_back:
                        row.append("0.5")
                    else:
                        row.append("-0.25")
            else:
                row.extend(["-0.25"] * n_correct)
            row = pad_row(row, num_columns)
            question_data.append(row)

        questions.append(question_data)

    return questions

def format_questions(questions):
    """Formats the questions for display or download."""
    output_lines = []
    for q_i, q_data in enumerate(questions, start=1):
        if q_i > 1:
            output_lines.append("")  # Separator between questions
        for row in q_data:
            output_lines.append("\t".join(row))
    return "\n".join(output_lines)

def get_copy_button_js(button_id, text):
    """Generates JavaScript code for copying text to clipboard."""
    escaped_text = json.dumps(text)  # Safely encode the text
    copy_script = f"""
    <script>
    document.getElementById("{button_id}").addEventListener("click", function() {{
        navigator.clipboard.writeText({escaped_text});
        alert("Text kopiert!");
    }});
    </script>
    """
    return copy_script


# Streamlit UI
st.title("Flashcards zu OLAT-Drag&Drop Fragen")

# Optional custom title input
custom_title = st.text_input("Optional: Geben Sie einen benutzerdefinierten Titel für die Fragen ein. Standard ist 'Lernkarteien'.")

# Didaktische Idee: Dropdown-Erklärung
explanation_text = """
Die Umwandlung von Lernkarteien in Drag-and-Drop-Fragen hat folgende didaktische Ziele:

1. **Konzentration auf Kernkonzepte**: Jede Zeile auf der Rückseite der Lernkarteien repräsentiert ein spezifisches Konzept oder eine Erklärung.
2. **Förderung des Verstehens**: Durch die Auswahl von 8 Begriffen zur Zuordnung wird sichergestellt, dass Lernende die Kerninhalte reflektieren und verstehen müssen.
3. **Reduktion von Auswahlmöglichkeiten**: Indem nur 4 der Begriffe korrekt zugeordnet werden können, wird die Schwierigkeit aufrechterhalten, ohne die Lernenden zu überfordern.
4. **Aktives Lernen**: Drag-and-Drop-Fragen fördern interaktives und aktives Lernen, da die Lernenden Begriffe mit Konzepten direkt verbinden müssen.
5. **Flexibilität der Inhalte**: Die Struktur der Lernkarteien (z. B. 📌 Hauptidee, 🔍 Ziel, 👉 Beispiel) bietet eine vielseitige Grundlage für unterschiedliche Fragetypen.

Beispiel:
- Front: "Politische Rechte und Pflichten"
- Rückseite:
  - 📌 "Beziehen sich auf die Befugnisse und Verantwortlichkeiten der Bürger in einem Staat."
  - 🔍 "Ziel ist es, Bürgerbeteiligung zu fördern und eine gerechte Gesellschaft zu gewährleisten."
  - 👉 "Jeder Schweizer Bürger ist verpflichtet, Steuern zu zahlen und hat das Recht, an Wahlen teilzunehmen."

In den Drag-and-Drop-Fragen wird beispielsweise die Zeile "Ziel ist es, Bürgerbeteiligung zu fördern und eine gerechte Gesellschaft zu gewährleisten." als korrekter Zuordnungspunkt verwendet.
"""

# Dropdown für die didaktische Erklärung
with st.expander("Erklärung der didaktischen Idee hinter dieser Methode"):
    st.markdown(explanation_text)

# Erklärung zur Formatierung der Lernkarteien
format_text = """
### Anleitung zur Formatierung der Lernkarteien

Um Lernkarteien für die Umwandlung in Drag-and-Drop-Fragen zu erstellen, beachten Sie bitte die folgende Struktur:

1. **Format einer Karte**:
   - **Vorderseite**: Der Begriff oder Titel, der zugeordnet werden soll.
   - **Rückseite**: Mindestens eine Erklärung oder ein Konzept. Zusätzliche Zeilen für Details, Beispiele oder Ziele sind möglich.
   - Zwischen Vorder- und Rückseite muss ein **Absatz** eingefügt werden.

2. **Trennung zwischen Karten**:
   - Zwischen zwei Karten muss **eine leere Zeile** eingefügt werden, um die Karten klar voneinander zu trennen.
   - Für **Lückentextfragen zu Voci**, verwenden Sie bitte die folgende Konverter: [OLAT-Voci](https://olat-voci.streamlit.app/).   

#### Beispiel:
```text
Politische Rechte und Pflichten
📌 Beziehen sich auf die Befugnisse und Verantwortlichkeiten der Bürger in einem Staat, wie das Wahlrecht und Steuerpflicht.
🔍 Ziel ist es, Bürgerbeteiligung zu fördern und eine gerechte Gesellschaft zu gewährleisten.
👉 Jeder Schweizer Bürger ist verpflichtet, Steuern zu zahlen und hat das Recht, an Wahlen und Abstimmungen teilzunehmen.

Die Regierungsformen
📌 Sie beschreiben, wie die Staatsgewalt ausgeübt wird und umfassen Diktatur, Demokratie unter anderen.
🔍 Wesentlich ist, wer die Macht hat und wie diese kontrolliert wird.
👉 In einer Demokratie wie der Schweiz haben die Bürger das Recht, ihre Regierung durch Wahlen zu wählen.
