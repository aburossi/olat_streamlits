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
```

3. **Erstellungshilfe für Lernkarteien**:
   Wenn Sie Hilfe bei der Erstellung der Lernkarteien benötigen, nutzen Sie das folgende Tool:
   [Flashcard Generator – Custom GPT](https://chatgpt.com/g/g-dGooBvtzu-flashcard-genius). 

   Dieses Tool unterstützt Sie dabei, Lernkarteien in einem kompatiblen Format zu generieren und sorgt für eine einheitliche Struktur.
   
    Hier ein weiteres Beispeil um Lernkarteien in verschiedenen Lernkarteien-Formate (Definitionen, Konzepte, Vokabel, usw.) zu erstellen: [Custom-GPT Lernkarteien](https://chatgpt.com/g/g-675ea28843a4819188dc512c1966a152-lernkarteien) erstellen.


   Oder generieren Sie einfach Lernkarteien mit einer KI.
   
   Beispielprompt:
```
Erstelle Lernkarteien zu [Thema] im folgenden Format:
1. Jeder Karte hat eine Vorderseite mit einem Titel und eine Rückseite.
2. Zwischen Vorder- und Rückseite sollte ein Absatz sein.
3. Zwischen den Karten eine leere Zeile.

Beispiel:
Front
Back

Front
Back
```
"""

# Streamlit-Abschnitt zur Formatierungserklärung
with st.expander("Anleitung zur Erstellung von Lernkarteien und Link zur Generierung"):
    st.markdown(format_text)


# Text Input
input_text = st.text_area("Fügen Sie Ihre Flashcards unten ein:", height=400)

# Select number of correct pairs
st.sidebar.header("Einstellungen für die Fragen")
n_correct = st.sidebar.slider(
    "Anzahl der korrekten Paare pro Frage",
    min_value=1,
    max_value=6,
    value=4,
    step=1,
    help="Wählen Sie, wie viele korrekte Paare in jeder Frage enthalten sein sollen. Die Gesamtanzahl der Optionen bleibt bei 8."
)

# Generate Button
if st.button("Generieren"):
    if not input_text.strip():
        st.error("Bitte fügen Sie die Flashcards-Daten ein.")
    else:
        flashcards, max_back_lines = parse_flashcards(input_text)

        if not flashcards:
            st.error("Keine gültigen Flashcards gefunden. Stellen Sie sicher, dass jede Flashcard mindestens eine Vorderseite und eine Rückseite hat.")
        else:
            # Check if all flashcards have the same number of back lines
            is_uniform, back_line_count = check_uniform_back_lines(flashcards)

            selected_lines = list(range(back_line_count))  # Default to all lines
            if is_uniform:
                st.success(f"Alle Flashcards haben {back_line_count} Rückseitenzeile(n).")
                # Let user select which lines to include
                st.sidebar.header("Rückseitenzeilen auswählen")
                selected_lines = []
                for i in range(back_line_count):
                    if st.sidebar.checkbox(f"Zeile {i+1}", value=True):
                        selected_lines.append(i)
                if not selected_lines:
                    st.error("Bitte wählen Sie mindestens eine Rückseitenzeile aus.")
            else:
                st.warning("Flashcards haben unterschiedliche Anzahlen von Rückseitenzeilen. Es werden nur die gemeinsamen Rückseitenzeilen verarbeitet.")
                # Find minimum number of back lines
                min_back_lines = min(len(card["clean_backs"]) for card in flashcards)
                st.info(f"Es werden die ersten {min_back_lines} Rückseitenzeilen jeder Flashcard verarbeitet.")
                selected_lines = list(range(min_back_lines))

            if selected_lines:
                # Default title if not provided
                question_title = custom_title if custom_title.strip() else "Lernkarteien"

                # Generate questions based on selected lines and number of correct pairs
                all_questions = []
                for line_idx in selected_lines:
                    questions = generate_questions(
                        flashcards,
                        correct_line_index=line_idx,
                        title=question_title,
                        n_correct=n_correct  # Pass the selected number of correct pairs
                    )
                    all_questions.extend(questions)

                if not all_questions:
                    st.error("Nicht genügend Flashcards, um Fragen zu generieren. Stellen Sie sicher, dass Sie mindestens 8 Flashcards haben und die Anzahl der korrekten Paare passt.")
                else:
                    output = format_questions(all_questions)

                    # JSON Output
                    with st.expander("Rohdaten der Flashcards anzeigen"):
                        st.json(flashcards)

                    # Display outputs side by side
                    # Separate outputs by lines
                    outputs = {}
                    for line_idx in selected_lines:
                        line_title = f"Zeile {line_idx + 1}"
                        questions = generate_questions(
                            flashcards,
                            correct_line_index=line_idx,
                            title=question_title,
                            n_correct=n_correct
                        )
                        formatted_output = format_questions(questions)
                        outputs[line_title] = formatted_output

                    # Display in separate columns
                    num_columns = len(outputs)
                    cols = st.columns(num_columns)

                    for idx, (line_title, formatted_output) in enumerate(outputs.items()):
                        with cols[idx]:
                            st.subheader(f"Output ({line_title})")
                            text_area_id = f"text_area_{idx}"
                            st.text_area(f"Formatierte Ausgabe - {line_title}", value=formatted_output, height=300, key=text_area_id)
                            
                            # Download Button
                            download_filename = f"{line_title.lower().replace(' ', '_')}_output.txt"
                            st.download_button(f"Download {line_title}", formatted_output, file_name=download_filename)

