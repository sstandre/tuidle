from __future__ import annotations

from string import ascii_letters

from textual.app import App, ComposeResult
from textual.message import Message
from textual import events
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Button, Input, Label, Static



class Charbox(Label):
    
    def on_click(self, event):
         print(self.classes)
    


class Word(Static):

    def __init__(self, letters, *args, **kwargs):
        self.letters = letters
        super().__init__(*args, **kwargs)

    
    def compose(self) -> ComposeResult:

        self.charboxes = [Charbox('') for _ in range(self.letters)]
        self.active_box = 0

        for charbox in self.charboxes:
            yield charbox


    class Submitted(Message):
        def __init__(self, word: str) -> None:
            self.word = word
            super().__init__()

    def handle_key_press(self, event: events.Key):
        if event.key == 'backspace':
            self.handle_delete()
        elif event.key in ascii_letters:
            self.handle_letter(event.key)
        elif event.key == 'enter':
            self.submit()

    def handle_letter(self, letter: str):
        if self.active_box == self.letters:
            return
        self.charboxes[self.active_box].update(letter.upper())
        self.active_box += 1

        
    def handle_delete(self):
        if self.active_box == 0:
            return
        self.active_box -= 1
        self.charboxes[self.active_box].update('')

    def submit(self):
        if self.active_box == self.letters:
            self.post_message(self.Submitted(self.get_word()))

    
    def get_word(self):
        return "".join([str(c.renderable) for c in self.charboxes])

    def update_chars(self, classes:list[str]):
        for char, cls in zip(self.charboxes, classes):
            if cls: char.add_class(cls)

    # def on_click(self, event):
    #     print(self.classes)
    #     self.refresh()s


class Keyboard(Container):

    def compose(self) -> ComposeResult:
        with Horizontal():
            for char in 'QWERTYUIOP':
                yield Charbox(char, id=char)
        with Horizontal():
            for char in 'ASDFGHJKL':
                yield Charbox(char, id=char)
        with Horizontal():
            for char in 'ZXCVBNM':
                yield Charbox(char, id=char)

    def update_chars(self, classes):
        clsval = {
            'incorrect':1,
            'maybe':2,
            'correct':3,
        }
        for char, cls in classes:
            box = self.query_one(f"Charbox#{char}")
            current = [k for k in clsval if k in box.classes]
            if not current:
                box.add_class(cls)
                return
            current = current[0]
            if  clsval[cls] > clsval[current]:
                box.remove_class(current)
                box.add_class(cls)


class WordleApp(App[None]):

    CSS_PATH='wordle.tcss'

    WORDS = 6
    LETTERS = 5

    SECRET = 'FOCUS'

    active_word = None

    def compose(self) -> ComposeResult:

        self.words = [Word(self.LETTERS) for _ in range(self.WORDS)]
        self.keyboard = Keyboard()
        self.activate_word(0)
        
        with Vertical(classes='word-box'):
            for word in self.words:
                yield word
        
        yield self.keyboard

    def activate_word(self, index: int) -> None:
        if self.active_word == self.WORDS -1:
            # self.exit()
            return
        self.active_word = index
        self.words[index].add_class('active')
        
    def on_key(self, event: events.Key) -> None:
        self.words[self.active_word].handle_key_press(event)

    def on_word_submitted(self, event: Word.Submitted):
        classes = self.evaluate_word(event.word)
        self.words[self.active_word].update_chars(classes)
        self.keyboard.update_chars(zip(event.word, classes))
        self.activate_word(self.active_word + 1)

    def evaluate_word(self, guess: str):

        classes = ["incorrect" for _ in guess]
        secret_left = []

        for i, (s,g) in enumerate(zip(self.SECRET, guess)):
            if s==g:
                classes[i] = "correct"
            else:
                secret_left.append(s)
        for i, g in enumerate(guess):
            if classes[i] == "incorrect" and g in secret_left:
                classes[i] = "maybe"
                secret_left.remove(g)

        return classes

app = WordleApp()

if __name__ == "__main__":
    app.run()
