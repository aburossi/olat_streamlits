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

def parse_flashcards_json(json_text):
    """Parses flashcards from JSON input."""
    flashcards = []
    max_back_lines = 0

    try:
        data = json.loads(json_text)
        if not isinstance(data, list):
            st.error("Ungültiges JSON-Format: Das oberste Element muss eine Liste sein.")
            return [], 0

        for item in data:
            if not isinstance(item, dict) or "question" not in item or "answer" not in item:
                st.warning(f"Überspringe ungültigen Eintrag im JSON: {item}")
                continue

            front = replace_ss_with_ss(str(item["question"]))
            answer_text = str(item["answer"])
            # Split answer by newline, handle potential multiple newlines
            backs = [replace_ss_with_ss(line.strip()) for line in answer_text.split('\n') if line.strip()]
            clean_backs = [clean_back_text(back) for back in backs]

            if not front or not clean_backs:
                st.warning(f"Überspringe Eintrag wegen fehlender Vorder- oder Rückseite: {item}")
                continue

            flashcards.append({
                "front": front,
                "clean_backs": clean_backs
            })
            if len(clean_backs) > max_back_lines:
                max_back_lines = len(clean_backs)

    except json.JSONDecodeError:
        st.error("Ungültiges JSON-Format. Bitte überprüfen Sie Ihre Eingabe.")
        return [], 0
    except Exception as e:
        st.error(f"Ein Fehler ist beim Verarbeiten des JSON aufgetreten: {e}")
        return [], 0

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


# Select Input Format
input_format = st.radio(
    "Wählen Sie das Eingabeformat Ihrer Lernkarteien:",
    ('Plain Text', 'JSON'),
    help="Wählen Sie 'Plain Text' für das Standardformat (Vorder-/Rückseite durch Zeilenumbruch, Karten durch Leerzeile getrennt) oder 'JSON' für das Format `[{'question': '...', 'answer': '...'}]`."
)

# Text Input
input_text = st.text_area(f"Fügen Sie Ihre Flashcards im '{input_format}'-Format unten ein:", height=400)

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
        flashcards = []
        max_back_lines = 0

        # Parse input based on selected format
        try:
            if input_format == 'Plain Text':
                flashcards, max_back_lines = parse_flashcards(input_text)
            elif input_format == 'JSON':
                # Error handling for invalid JSON is inside parse_flashcards_json
                flashcards, max_back_lines = parse_flashcards_json(input_text)

        except Exception as e: # Catch potential unexpected errors during parsing call
             st.error(f"Ein unerwarteter Fehler beim Parsen der Eingabe ist aufgetreten: {e}")
             flashcards = [] # Ensure flashcards is empty to prevent further processing

        # Proceed only if parsing was successful and yielded flashcards
        if not flashcards:
            # Display error only if no flashcards were parsed successfully.
            # Specific format errors are handled within the respective parsing functions.
            st.error("Keine gültigen Flashcards gefunden oder Parsing fehlgeschlagen. Überprüfen Sie das Format und den Inhalt Ihrer Eingabe.")
        else:
            # Check if all flashcards have the same number of back lines
            is_uniform, back_line_count = check_uniform_back_lines(flashcards)

            selected_lines = [] # Initialize selected_lines
            min_back_lines_for_non_uniform = 0 # Initialize

            if is_uniform:
                st.success(f"Alle {len(flashcards)} Flashcards haben {back_line_count} Rückseitenzeile(n).")
                # Let user select which lines to include via sidebar
                st.sidebar.header("Rückseitenzeilen auswählen")
                for i in range(back_line_count):
                    if st.sidebar.checkbox(f"Zeile {i+1} als korrekte Antwort verwenden", value=True, key=f"line_select_{i}"):
                        selected_lines.append(i)
                if not selected_lines:
                    st.error("Bitte wählen Sie mindestens eine Rückseitenzeile in der Seitenleiste aus.")
            else:
                # Find minimum number of back lines for non-uniform case
                 min_back_lines_for_non_uniform = min(len(card["clean_backs"]) for card in flashcards) if flashcards else 0

                 if min_back_lines_for_non_uniform > 0:
                    st.warning(f"Flashcards haben unterschiedliche Anzahlen von Rückseitenzeilen (Minimum: {min_back_lines_for_non_uniform}).")
                    st.sidebar.header("Rückseitenzeilen auswählen (basierend auf Minimum)")
                    for i in range(min_back_lines_for_non_uniform):
                         if st.sidebar.checkbox(f"Zeile {i+1} als korrekte Antwort verwenden", value=True, key=f"line_select_nonuniform_{i}"):
                            selected_lines.append(i)
                    if not selected_lines:
                         st.error("Bitte wählen Sie mindestens eine Rückseitenzeile (basierend auf dem Minimum) in der Seitenleiste aus.")
                 else:
                     # This case should ideally be caught by the initial parsing checks if cards have 0 back lines
                     st.error("Einige Flashcards scheinen keine gültigen Rückseitenzeilen zu haben. Verarbeitung nicht möglich.")


            # Proceed only if lines have been selected
            if selected_lines:
                # Default title if not provided
                question_title = custom_title if custom_title.strip() else "Lernkarteien"

                # --- Generate and Display Outputs ---
                all_questions_generated = False # Flag to check if any questions were generated at all
                outputs = {} # Dictionary to hold formatted output per selected line

                for line_idx in selected_lines:
                    # Generate questions for the current line index
                    questions_for_line = generate_questions(
                        flashcards,
                        correct_line_index=line_idx,
                        title=question_title,
                        n_correct=n_correct # Pass the selected number of correct pairs
                    )

                    if questions_for_line:
                        all_questions_generated = True
                        line_title = f"Zeile {line_idx + 1}" # Use 1-based index for display
                        formatted_output = format_questions(questions_for_line)
                        outputs[line_title] = formatted_output
                    # else: No questions generated for this specific line (e.g., not enough cards), continue to next line


                # Check if any questions were generated across all selected lines
                if not all_questions_generated:
                    st.error(f"Nicht genügend Flashcards ({len(flashcards)} gefunden), um Fragen zu generieren. Sie benötigen mindestens 8 Flashcards. Oder die Anzahl korrekter Paare ({n_correct}) ist für die verfügbaren Karten nicht möglich.")
                else:
                    # JSON Output for debugging/inspection
                    with st.expander("Rohdaten der verarbeiteten Flashcards anzeigen"):
                        st.json([{"front": c["front"], "clean_backs": c["clean_backs"]} for c in flashcards]) # Show processed data

                    # Display outputs side by side in columns
                    num_columns = len(outputs)
                    if num_columns > 0:
                        cols = st.columns(num_columns)
                        output_items = sorted(outputs.items()) # Sort by line number ("Zeile 1", "Zeile 2", ...)

                        for idx, (line_title, formatted_output) in enumerate(output_items):
                            with cols[idx]:
                                st.subheader(f"Output ({line_title})")
                                text_area_key = f"text_area_{line_title.replace(' ', '_')}" # Unique key
                                st.text_area(f"Formatierte Ausgabe - {line_title}", value=formatted_output, height=300, key=text_area_key)

                                # Copy Button
                                copy_button_id = f"copy_btn_{line_title.replace(' ', '_')}"
                                st.markdown(f'<button id="{copy_button_id}">Kopiere Text ({line_title})</button>', unsafe_allow_html=True)
                                st.markdown(get_copy_button_js(copy_button_id, formatted_output), unsafe_allow_html=True)

                                # Download Button
                                download_filename = f"{question_title.lower().replace(' ', '_')}_{line_title.lower().replace(' ', '_')}_output.txt"
                                st.download_button(
                                     label=f"Download ({line_title})",
                                     data=formatted_output,
                                     file_name=download_filename,
                                     mime="text/plain",
                                     key=f"download_btn_{line_title.replace(' ', '_')}" # Unique key
                                )