"""
Core responsibility
------------------------------------------------------------
Turns the input logic into a stream of tokens.
I decided to keep the lexer very small.
The parser should be responsible for grammar rules,
while the lexer only recognizes symbols and keywords.

Design Note
-------------------------------------------------------------
Instead of using regular expressions,I wrote this lexer as a character-by-character scanner.
Later I want to support richer biological syntax
without rewriting the lexer.
"""
class Token:
    def __init__(self, token_type, value, pos):
        self.type = token_type
        self.value = value
        self.position = pos

    def __repr__(self):
        return f"Token({self.type}, '{self.value}', {self.position})"


class BioLexer:
    # Reserved words.
    # Everything else becomes an IDENTIFIER.
    keywords = {
        'IF': 'IF',
        'AND': 'AND',
        'OR': 'OR',
        'NOT': 'NOT'
    }
    # Keeping these separate makes the identifier rule easier to change later.
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
    digits = "0123456789"

    def __init__(self, text):
        self.text = text
        self.idx = 0
        self.tokens = []

        self.char = self.text[self.idx] if len(text) > 0 else None

    def move(self):
        # One helper instead of repeating index updates everywhere.
        self.idx += 1

        if self.idx < len(self.text):
            self.char = self.text[self.idx]
        else:
            self.char = None

    def tokenize(self):

        while self.idx < len(self.text):
            # Ignore spaces. The parser doesn't need them.
            if self.char is not None and self.char.isspace():
                self.move()
                continue

            if self.char == '(':
                self.tokens.append(Token('L_Paren', '(', self.idx))
                self.move()
                continue

            if self.char == ')':
                self.tokens.append(Token('R_Paren', ')', self.idx))
                self.move()
                continue
            # My language uses "->" to separate.Condition from output protein.
            if (
                self.char == '-'
                and self.idx + 1 < len(self.text)
                and self.text[self.idx + 1] == '>'
            ):

                start_pos = self.idx

                self.move()
                self.move()

                self.tokens.append(Token('Arrow', '->', start_pos))
                continue
            # Protein names and keywords both start the same way,so read the whole word first.
            if self.char in BioLexer.letters:

                word = ""
                start_pos = self.idx

                while (
                    self.idx < len(self.text)
                    and self.char is not None
                    and (
                        self.char in BioLexer.letters
                        or self.char in BioLexer.digits
                    )
                ):
                    word += self.char
                    self.move()

                upper_word = word.upper()
                # Keywords are checked after reading the word.(This lets identifiers like AraC or TetR stay unchanged.)
                if upper_word in BioLexer.keywords:
                    self.tokens.append(
                        Token(
                            BioLexer.keywords[upper_word],
                            word,
                            start_pos
                        )
                    )
                else:
                    self.tokens.append(
                        Token(
                            'IDENTIFIER',
                            word,
                            start_pos
                        )
                    )

                continue
            # Ignore characters that are not part of the language.
            # The parser will report syntax problems later if needed.
            self.move()
        # Makes parsing easier because there is always one final token to stop on.
        self.tokens.append(Token('EOF', '', self.idx))

        return self.tokens