from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# --- Database connection setup ---
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="tite",   # <-- Replace this
        database="battpracv3"      # <-- Replace this
    )

# --- Pitch Pattern Management ---
class PitchPatternManager:
    def __init__(self):
        self.db = connect_to_db()

    def add_pitch_pattern(self, name, parity):
        cursor = self.db.cursor()
        query = "INSERT INTO pitch_patterns (pitch_pattern_name, pitch_pattern_parity) VALUES (%s, %s)"
        cursor.execute(query, (name, parity))
        self.db.commit()
        cursor.close()

    
    #IN CASE OF ERROR IN EDIT PITCH: --------------------------------------------------
    def edit_pitch_pattern(self, pattern_id, name=None, parity=None):
        cursor = self.db.cursor()
        updates = []
        params = []

        if name is not None:
            updates.append("pitch_pattern_name = %s")
            params.append(name)
        if parity is not None:
            updates.append("pitch_pattern_parity = %s")
            params.append(parity)

        if updates:
            query = f"UPDATE pitch_patterns SET {', '.join(updates)} WHERE pitch_pattern_id = %s"
            params.append(pattern_id)
            cursor.execute(query, tuple(params))
            self.db.commit()

        cursor.close()
    

    def delete_pitch_pattern(self, pattern_id):
        cursor = self.db.cursor()
        query = f"DELETE FROM pitch_patterns WHERE pitch_pattern_id={pattern_id}"
        cursor.execute(query)
        self.db.commit()
        cursor.close()
        
    # IN CASE OF ERROR IN DELETE ---------------------------------------------------------------
    # def delete_pitch_pattern(self, pattern_id):
    # cursor = self.db.cursor()
    # query = "DELETE FROM pitch_patterns WHERE pitch_pattern_id = %s"
    # cursor.execute(query, (pattern_id,))
    # self.db.commit()
    # cursor.close()


    def get_pitch_pattern(self, pattern_id):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM pitch_patterns WHERE pitch_pattern_id = %s", (pattern_id,))
        result = cursor.fetchone()
        cursor.close()
        return result

    def get_all_patterns(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM pitch_patterns")
        results = cursor.fetchall()
        cursor.close()
        return results
    
    def search_patterns(self, query):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM pitch_patterns WHERE pitch_pattern_name LIKE %s", (f"%{query}%",))
        results = cursor.fetchall()
        cursor.close()
        return results

def split_by_parity_pattern(s, parity): # PARITY HELPER CHECKER (1 OR 2 DIGITS)
    parity_str = str(parity)
    chunks = []
    i = 0

    if len(parity_str) == 1:
        chunk_size = int(parity_str)
        while i < len(s):
            chunks.append(s[i:i+chunk_size])
            i += chunk_size
    elif len(parity_str) == 2:
        chunk_sizes = [int(parity_str[0]), int(parity_str[1])]
        toggle = 0
        while i < len(s):
            chunk_size = chunk_sizes[toggle]
            chunks.append(s[i:i+chunk_size])
            i += chunk_size
            toggle = 1 - toggle
    else:
        raise ValueError("Parity must be one or two digits.")

    return chunks

# --- Word Translator ---
class WordTranslator:
    def __init__(self):
        self.db = connect_to_db()

    def fetch_pitch_pattern(self, pattern_id):
        cursor = self.db.cursor()
        query = "SELECT * FROM pitch_patterns WHERE pitch_pattern_id = %s"
        cursor.execute(query, (pattern_id,))
        result = cursor.fetchone()
        cursor.close()
        if not result:
            raise ValueError(f"Pitch pattern ID {pattern_id} not found.")
        return result[1], result[2]  # name, parity

    def generate_new_word(self, word, parity):
        word = list(word)
        ascii_value = []

        print(f"Translating word: {word} with parity: {parity}")

        # STEP 1: Convert characters to binary
        for i in word:
            binary = bin(ord(i))
            ascii_value.append("0" + binary[2:])
        print(f"Step 1 - ASCII binaries: {ascii_value}")

        binary_joined = "".join(ascii_value)
        print(f"Step 1 - Joined binary string: {binary_joined}")
        print(f"Word is: {word}")

        # STEP 2: Partition the binary string into chunks according to parity pattern
        new_binary = split_by_parity_pattern(binary_joined, parity)
        print(f"Step 2 - Binary chunks: {new_binary}")

        # STEP 3: Convert binary chunks to decimal
        decimal = []
        for i in new_binary:
            if i == "":
                continue
            num = int(i, 2)
            print(f"Chunk '{i}' as decimal: {num}")

            # STEP 4: Ensure decimal values are within 1–26
            while num > 26:
                num -= 26

            if num != 0:
                decimal.append(num)
        print(f"Step 4 - Decimal values after mod 26: {decimal}")

        # STEP 5: Map decimal values to letters
        alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        generated_word = ""
        for i in decimal:
            generated_word += alphabet[i-1]

        print(f"Step 5 - Generated word: {generated_word}")
        return generated_word


    def translate_word(self, word, pattern_id):
        if not word.isupper():
            raise ValueError("Word must be uppercase only.")
        _, parity = self.fetch_pitch_pattern(pattern_id)
        return self.generate_new_word(word, parity)
    
    
def octal_word_encoder(word, chunk_size): # OCTAL CONVERTER ---------------------
    if not word.isupper():
        raise ValueError("Word must be uppercase only.")
    
    octal_digits = ""
    for char in word:
        ascii_val = ord(char)
        octal_val = oct(ascii_val)[2:]  # e.g., '110' for H
        octal_digits += octal_val
    print(f"Octal string: {octal_digits}")

    chunks = split_by_parity_pattern(octal_digits, chunk_size)
    print(f"Chunks: {chunks}")

    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    generated_word = ""
    for chunk in chunks:
        if not chunk:
            continue
        num = int(chunk, 10)
        num = num % 26
        if num == 0:
            continue
        letter = alphabet[num - 1]
        generated_word += letter
        print(f"Chunk '{chunk}' → {num} → '{letter}'")

    return generated_word

def hex_word_encoder(word, chunk_size):  # HEX CONVERTER ---------------------
    if not word.isupper():
        raise ValueError("Word must be uppercase only.")

    binary = "".join(f"{ord(char):08b}" for char in word)
    print(f"Binary representation: {binary}")

    chunks = split_by_parity_pattern(binary, chunk_size)
    print(f"Chunks: {chunks}")

    alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    generated_word = ""

    for chunk in chunks:
        if not chunk:
            continue
        hex_value = hex(int(chunk, 2))[2:]  # Convert binary to hex
        num = int(hex_value, 16) % 26
        if num == 0:
            continue
        letter = alphabet[num - 1]
        generated_word += letter
        print(f"Chunk '{chunk}' → Hex '{hex_value}' → {num} → '{letter}'")

    return generated_word

# --- Routes ---

@app.route('/')
def index():
    manager = PitchPatternManager()
    patterns = manager.get_all_patterns()
    return render_template("index.html", patterns=patterns)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form['name']
        parity = int(request.form['parity'])
        manager = PitchPatternManager()
        manager.add_pitch_pattern(name, parity)
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    manager = PitchPatternManager()
    pattern = manager.get_pitch_pattern(id)
    if request.method == 'POST':
        name = request.form['name']
        parity = int(request.form['parity'])
        manager.edit_pitch_pattern(id, name, parity)
        return redirect(url_for('index'))
    return render_template('edit.html', pattern=pattern)

@app.route('/delete/<int:id>', methods=["POST"])
def delete(id):
    manager = PitchPatternManager()
    manager.delete_pitch_pattern(id)
    return redirect(url_for('index'))

@app.route('/translate', methods=['POST'])
def translate():
    word = request.form['word'].strip().upper()
    pattern_id = int(request.form['pattern_id'])
    mode = request.form.get('mode', 'binary')  # default to binary

    manager = PitchPatternManager()
    patterns = manager.get_all_patterns()

    try:
        name, parity = WordTranslator().fetch_pitch_pattern(pattern_id) # fetch parity and pass

        if mode == "binary":
            translator = WordTranslator()
            translated_word = translator.generate_new_word(word, parity)
        elif mode == "octal":
            translated_word = octal_word_encoder(word, chunk_size=parity)
        elif mode =='hex':
            translated_word = hex_word_encoder(word, chunk_size=parity)
        else:
            translated_word = "Error: Unknown mode selected."
    except Exception as e:
        translated_word = f"Error: {str(e)}"

    return render_template("index.html", patterns=patterns, translated_word=translated_word)



@app.route('/search', methods=['POST'])
def search():
    query = request.form['query'].strip()
    manager = PitchPatternManager()
    patterns = manager.search_patterns(query)
    return render_template('index.html', patterns=patterns, search_query=query)


if __name__ == '__main__':
    app.run(debug=True)
