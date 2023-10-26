from __future__ import annotations

from string import ascii_letters
import random
from enum import Enum

from textual.app import App, ComposeResult
from textual.message import Message
from textual import events
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal, Container, Grid
from textual.widgets import Button, Label, Static


class EndScreen(ModalScreen):
    """Screen with a dialog to quit."""

    label = Label("", id="message")

    class Reset(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Grid(
            self.label,
            Button("Play again", variant="primary", id="cancel"),
            Button("Quit", variant="error", id="quit"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            # self.post_message(self.Reset)
            self.app.pop_screen()

    def set_win_text(self, attempts):
        text = f"Congratulations! You won on {attempts} attempts."
        self.label.update(text)

    def set_lose_text(self):
        text = f"You lose!"
        self.label.update(text)


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

    def update_chars(self, hints):

        for char, hint in hints:
            charbox = self.query_one(f"Charbox#{char}")
            current = [k for k in hint.__class__ if k.name in charbox.classes]
            if not current:
                charbox.add_class(hint.name)
                continue
            current = current[0]
            if  hint.value > current.value:
                charbox.remove_class(current.name)
                charbox.add_class(hint.name)


class Charbox(Label):
    pass

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
            if cls: char.add_class(cls.name)

    # def on_click(self, event):
    #     print(self.classes)
    #     self.refresh()s


class WordleApp(App[None]):

    CSS_PATH='wordle.tcss'
    WORDS_FILE = 'words.txt'

    WORDS = 6
    LETTERS = 5

    class Hint(Enum):
        incorrect = 1
        maybe = 2
        correct = 3

    class State(Enum):
        INPLAY = 1
        WIN = 2
        LOSE = 3


    def read_from_file(self, path:str) -> None:
        """Import valid words from file."""
        try:
            with open(path, "r") as f:
                self.VALID_WORDS = [w.strip() for w in f.readlines()]
        except FileNotFoundError:
            self.exit()


    def compose(self) -> ComposeResult:       
        self.reset()
        with Vertical(classes='word-box'):
            for word in self.words:
                yield word
        
        yield self.keyboard

    def reset(self):
            self.read_from_file(self.WORDS_FILE)
            self.state = self.State.INPLAY
            self.SECRET = random.choice(self.VALID_WORDS)
            self.words = [Word(self.LETTERS) for _ in range(self.WORDS)]
            self.keyboard = Keyboard()
            self.activate_word(0)

    def activate_word(self, index: int) -> None:
        self.active_word = index
        self.words[index].add_class('active')
        
    def on_key(self, event: events.Key) -> None:
        self.words[self.active_word].handle_key_press(event)

    def on_word_submitted(self, event: Word.Submitted):

        guess = event.word
        if guess not in self.VALID_WORDS:
            self.notify("Not in word list", severity="error")
            return            

        classes = self.evaluate_word(guess)
        self.words[self.active_word].update_chars(classes)
        self.keyboard.update_chars(zip(guess, classes))

        if guess == self.SECRET:
            return self.win()

        if self.active_word == self.WORDS - 1:
            return self.lose()
        
        self.activate_word(self.active_word + 1)

    def on_endscreen_reset(self, event):
        self.reset()

    def evaluate_word(self, guess: str):

        classes = [self.Hint.incorrect for _ in guess]
        secret_left = []

        for i, (s,g) in enumerate(zip(self.SECRET, guess)):
            if s==g:
                classes[i] = self.Hint.correct
            else:
                secret_left.append(s)
        for i, g in enumerate(guess):
            if classes[i] == self.Hint.incorrect and g in secret_left:
                classes[i] = self.Hint.maybe
                secret_left.remove(g)

        return classes
    
    def win(self):
        self.state = self.State.WIN
        winscreen = EndScreen()
        winscreen.set_win_text(self.active_word+1)
        self.push_screen(winscreen)

    def lose(self):
        self.state = self.State.LOSE
        losescreen = EndScreen()
        losescreen.set_lose_text()
        self.push_screen(losescreen)

app = WordleApp()

if __name__ == "__main__":
    app.run()
