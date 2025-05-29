# utils/pitch_pattern_module.py

def translate_word(word, parity):
    """
    Translate a word using pitch pattern parity:
    - If parity is even: reverse the word
    - If parity is odd: uppercase every other letter
    """

    if int(parity) % 2 == 0:
        return word[::-1]  # Even → reverse
    else:
        # Odd → alternate uppercase and lowercase
        result = ''
        for i, c in enumerate(word):
            result += c.upper() if i % 2 == 0 else c.lower()
        return result
