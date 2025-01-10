import streamlit as st
import random
import math
from io import StringIO, BytesIO
import zipfile

# Sidebar with explanation
st.sidebar.title("Flashcard Types Explanation")
st.sidebar.markdown("""
👉 Use this [Custom-GPT](https://chatgpt.com/g/g-675ea28843a4819188dc512c1966a152-lernkarteien) to generate Vocabulary-Flashcards.
**Single Questions**:
- Each flashcard generates a separate question.
- Inlinechoice: Provides multiple choice options for each question.
- FIB: Fill-in-the-blank style questions with the correct answer.

**Grouped Questions**:
- Flashcards are grouped, and each group generates a set of questions.
- Inlinechoice: Multiple choice questions for grouped flashcards.
- FIB: Fill-in-the-blank questions for grouped flashcards.
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

# Main Title
st.title("Flashcards Formatter")

# File uploader and text area for input
uploaded_file = st.file_uploader("Upload a .txt file with flashcards. Separate flashcards with an empty line. Use this [Custom-GPT](https://chatgpt.com/g/g-675ea28843a4819188dc512c1966a152-lernkarteien) to generate Vocabulary-Flashcards.", type=["txt"])
text_input = st.text_area("Or paste your flashcards here. Separate flashcards with an empty line. Use this [Custom-GPT](https://chatgpt.com/g/g-675ea28843a4819188dc512c1966a152-lernkarteien) to generate Vocabulary-Flashcards.", height=200)

# Checkboxes for question types
generate_single = st.checkbox("Generate single questions")
generate_group = st.checkbox("Generate grouped questions")

# Slider for group size (shown only if grouped questions are selected)
group_size = st.slider("Select group size", min_value=2, max_value=10, value=2) if generate_group else None

if st.button("Generate Flashcards"):
    if uploaded_file or text_input:
        if uploaded_file:
            content = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
        else:
            content = text_input
        
        flashcards = read_flashcards(content)
        if flashcards:
            st.success(f"Loaded {len(flashcards)} flashcards.")
            
            # Store outputs in a dictionary for easy access
            outputs = {}

            if generate_single:
                outputs["inline_single.txt"] = generate_inline_single(flashcards)
                outputs["fib_single.txt"] = generate_fib_single(flashcards)

            if generate_group:
                groups = create_groups(flashcards, group_size)
                outputs["inline_group.txt"] = generate_inline_group(groups, group_size)
                outputs["fib_group.txt"] = generate_fib_group(groups, group_size)

            # Show individual download buttons for each file
            for file_name, content in outputs.items():
                st.download_button(
                    label=f"Download {file_name}",
                    data=content,
                    file_name=file_name,
                    mime="text/plain"
                )

            # Create a zip file for bulk download
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for file_name, content in outputs.items():
                    zf.writestr(file_name, content)
            zip_buffer.seek(0)

            st.download_button(
                label="Download All Files as ZIP",
                data=zip_buffer,
                file_name="flashcards_outputs.zip",
                mime="application/zip"
            )
        else:
            st.warning("No valid flashcards found. Please check your input format.")
    else:
        st.warning("Please upload a file or paste flashcards.")
