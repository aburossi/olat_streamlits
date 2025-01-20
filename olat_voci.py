import streamlit as st
import random
import math
from io import StringIO, BytesIO
import zipfile

# Seiten-Titel mit Emojis
st.title("🎓 OLAT Voci-Lernkarteien Converter 📚")

# Sidebar mit Erklärungen
st.sidebar.title("Erklärung der Lernkarten-Typen")
st.sidebar.markdown("""
👉 Verwende dieses [Custom-GPT](https://chatgpt.com/g/g-678e4d702d6881919ca1166aaf958839-lernkarteien-voci) zur Generierung von Vokabel-Lernkarten.
**Einzelne Fragen**:
- Jede Lernkarte generiert eine separate Frage.
- Inlinechoice: Bietet Multiple-Choice-Optionen für jede Frage.
- FIB: Lückentext-Fragen mit der richtigen Antwort.

**Gruppierte Fragen**:
- Lernkarten sind gruppiert, und jede Gruppe generiert ein Set von Fragen.
- Inlinechoice: Multiple-Choice-Fragen für gruppierte Lernkarten.
- FIB: Lückentext-Fragen für gruppierte Lernkarten.

> **Hinweis:** Nur die Lernkarteien, die mit dem Bot erstellt wurden, funktionieren. Es gibt zwei Formate:
> - **Individuelle Formate**: Jede Karte wird einzeln behandelt.
> - **Intergruppierte Formate**: Karten werden in Gruppen verarbeitet, was eine zusammenhängende Bearbeitung ermöglicht.
""")

def read_flashcards(content):
    flashcards = []
    raw_flashcards = [fc.strip() for fc in content.split('\n\n') if fc.strip()]
    for fc in raw_flashcards:
        lines = fc.split('\n')
        if len(lines) >= 2:
            back = lines[0].strip()
            front = lines[1].strip()
            flashcards.append((back, front))
    return flashcards

def generate_inline_single(flashcards):
    output = ""
    for back, front in flashcards:
        choices = [card[0] for card in flashcards if card[0] != back]
        if len(choices) > 3:
            choices = random.sample(choices, 3)
        choices_str = "|".join(choices)
        output += "Type\tInlinechoice\n"
        output += "Title\tWörter einordnen\n"
        output += "Question\t✏✏Wählen Sie die richtigen Begriffe.✏✏\n"
        output += "Points\t1\n"
        output += f"Text\t{front} = \n"
        output += f"1\t{choices_str}\t{back}\t|\n\n"
    return output

def generate_fib_single(flashcards):
    output = ""
    for back, front in flashcards:
        output += "Type\tFIB\n"
        output += "Title\t✏✏Vervollständigen Sie die Lücken mit dem korrekten Begriff.✏✏\n"
        output += "Points\t1\n"
        output += f"Text\t{front} = \n"
        output += f"1\t{back}\t20\n\n"
    return output

def create_groups(flashcards, group_size):
    required_appearances = 2
    assignments = flashcards * required_appearances
    random.shuffle(assignments)
    total_assignments = len(assignments)
    num_groups = math.ceil(total_assignments / group_size)
    groups = [[] for _ in range(num_groups)]
    
    for card in flashcards:
        assigned = 0
        while assigned < required_appearances:
            group_index = random.randint(0, num_groups - 1)
            if card not in groups[group_index] and len(groups[group_index]) < group_size:
                groups[group_index].append(card)
                assigned += 1
    
    for i in range(num_groups):
        while len(groups[i]) < group_size:
            available_flashcards = [card for card in flashcards if card not in groups[i]]
            if not available_flashcards:
                available_flashcards = flashcards
            groups[i].append(random.choice(available_flashcards))
    for group in groups:
        random.shuffle(group)
    
    return groups

def generate_inline_group(groups, group_size):
    output = ""
    for group in groups:
        output += "Type\tInlinechoice\n"
        output += "Title\tWörter einordnen\n"
        output += "Question\t✏✏Wählen Sie die richtigen Begriffe.✏✏\n"
        output += f"Points\t{group_size}\n"
        for _, (back, front) in enumerate(group, 1):
            distractors = [card[0] for card in group if card[0] != back]
            distractors = list(set(distractors))
            choices_str = "|".join(distractors)
            output += f"Text\t  // {front} = \n"
            output += f"1\t{choices_str}\t{back}\t|\n"
        output += "\n"
    return output

def generate_fib_group(groups, group_size):
    output = ""
    for group in groups:
        output += "Type\tFIB\n"
        output += "Title\t✏✏Vervollständigen Sie die Lücken mit dem korrekten Begriff.✏✏\n"
        output += f"Points\t{group_size}\n"
        for back, front in group:
            output += f"Text\t  // {front} = \n"
            output += f"1\t{back}\t20\n"
        output += "\n"
    return output

# Dropdown für den Prompt
with st.expander("📄 Prompt für die Generierung von Lernkarten anzeigen"):
    st.code("""
    //goal
    - you are an expert multilingual flashcard generator tailored for vocational students in Switzerland. Students are 15-20 years old.
    - you deliver content in the language of the user and
    - you focus on clarity and ease of comprehension. 
    - you are both informative and engaging, providing scannable and significant educational content without requiring extra interaction from the user. 
    
    //instructions
    1. the user provides {content} or {keywords} about a topic
    2. you identify the key topics about {content} or {keywords} and generate structured if not stated differently 15 flashcards according to //Format
    3. After the flashcards provide a link to the How-To-Import Guide to import the output in Quizlet https://tools.fobizz.com/website/public_pages/efd008b9-8440-46bc-85e7-f2183e38f498?token=8b2576a6af6633d7d57d99a2cf248fb1
    
    //flashcards
    ## Vocabulary Flashcards
    Definition: These flashcards are designed for language learners, featuring words or phrases in one language and their translation or explanation in another.
    Structure:
    Front: The word or phrase (e.g., "Haus").
    Back: The translation or explanation (e.g., "House").
    after the generation provide the hyperlink to this https://olat-voci.streamlit.app/ to convert the flashcards to OLAT Fill the Blanks and inline Choice formats.
    
    //Format
    IMPORTANT: generate the back of the flashcard without using the keyword on the front
    
    //output in a code block
    Format: Front\n\Back\n\nFront\n\Back
    IMPORTANT: Follow the //output_example to facilitate import to quizlet.
    
    //output_example
    ```
    Bundesverfassung  
    Constitution fédérale  
    
    Parlament  
    Parlement  
    
    Regierung  
    Gouvernement  
    
    Kanton  
    Canton  
    ```
    """, language='python')
    st.markdown("Du kannst den obigen Prompt kopieren, um eigene Lernkarten mit dem Bot zu generieren.")

# Dateiupload und Textbereich für Eingaben
uploaded_file = st.file_uploader("Lade eine .txt-Datei mit Lernkarten hoch. Trenne die Lernkarten mit einer Leerzeile. Verwende dieses [Custom-GPT](https://chatgpt.com/g/g-675ea28843a4819188dc512c1966a152-lernkarteien) zur Generierung von Vokabel-Lernkarten.", type=["txt"])
text_input = st.text_area("Oder füge deine Lernkarten hier ein. Trenne die Lernkarten mit einer Leerzeile. Verwende dieses [Custom-GPT](https://chatgpt.com/g/g-675ea28843a4819188dc512c1966a152-lernkarteien) zur Generierung von Vokabel-Lernkarten.", height=200)

# Checkboxen für Fragetypen
generate_single = st.checkbox("Einzelne Fragen generieren")
generate_group = st.checkbox("Gruppierte Fragen generieren")

# Slider für Gruppengröße (nur sichtbar, wenn gruppierte Fragen ausgewählt sind)
group_size = st.slider("Wähle die Gruppengröße", min_value=2, max_value=10, value=2) if generate_group else None

if st.button("Lernkarten generieren"):
    if uploaded_file or text_input:
        if uploaded_file:
            content = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
        else:
            content = text_input
        
        flashcards = read_flashcards(content)
        if flashcards:
            st.success(f"{len(flashcards)} Lernkarten erfolgreich geladen.")
            
            # Ergebnisse in einem Wörterbuch speichern
            outputs = {}

            if generate_single:
                outputs["inline_single.txt"] = generate_inline_single(flashcards)
                outputs["fib_single.txt"] = generate_fib_single(flashcards)

            if generate_group:
                groups = create_groups(flashcards, group_size)
                outputs["inline_group.txt"] = generate_inline_group(groups, group_size)
                outputs["fib_group.txt"] = generate_fib_group(groups, group_size)

            # Individuelle Download-Buttons für jede Datei anzeigen
            for file_name, content in outputs.items():
                st.download_button(
                    label=f"{file_name} herunterladen",
                    data=content,
                    file_name=file_name,
                    mime="text/plain"
                )

            # Zip-Datei für den Massen-Download erstellen
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for file_name, content in outputs.items():
                    zf.writestr(file_name, content)
            zip_buffer.seek(0)

            st.download_button(
                label="Alle Dateien als ZIP herunterladen",
                data=zip_buffer,
                file_name="flashcards_outputs.zip",
                mime="application/zip"
            )
        else:
            st.warning("Keine gültigen Lernkarten gefunden. Bitte überprüfe das Eingabeformat.")
    else:
        st.warning("Bitte lade eine Datei hoch oder füge Lernkarten ein.")
