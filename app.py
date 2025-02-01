import json
from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterVideo
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
import os

# Caricamento credenziali da JSON
credentials_path = 'mycredentials1.json'
with open(credentials_path, 'r') as f:
    credentials = json.load(f)

API_ID = credentials['api_id']
API_HASH = credentials['api_hash']
PHONE_NUMBER = credentials['phone_number']
SESSION_NAME = credentials['session_name']

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text="Inserisci il codice ricevuto:", font_size='20sp'))

        self.text_input = TextInput(
            hint_text="Codice OTP",
            size_hint_y=None,
            height=50,
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            multiline=False
        )
        layout.add_widget(self.text_input)

        send_button = Button(text="Accedi", size_hint_y=None, height=50)
        send_button.bind(on_press=self.submit_code)
        layout.add_widget(send_button)

        self.add_widget(layout)

        self.start_client()

    def start_client(self):
        """Avvia il client Telegram e richiede il codice."""
        self.client.connect()
        if not self.client.is_user_authorized():
            self.client.send_code_request(PHONE_NUMBER)

    def submit_code(self, instance):
        """Recupera il codice e prova a effettuare il login."""
        code = self.text_input.text.strip()
        if code:
            self.verify_code(code)

    def verify_code(self, code):
        """Verifica il codice e mostra la schermata di successo."""
        try:
            self.client.sign_in(PHONE_NUMBER, code)
            print("Login riuscito!")
            self.manager.current = "chat_list"
        except Exception as e:
            print(f"Errore: {e}")


class SuccessScreen(Screen):
    def __init__(self, message="Login effettuato correttamente!", **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text=message, font_size='24sp'))
        self.add_widget(layout)


class ChatListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text="Le tue chat:", font_size='24sp'))
        
        # ScrollView to display chat list
        self.chat_list_layout = GridLayout(cols=1, size_hint_y=None)
        self.chat_list_layout.bind(minimum_height=self.chat_list_layout.setter('height'))
        scroll_view = ScrollView()
        scroll_view.add_widget(self.chat_list_layout)
        layout.add_widget(scroll_view)

        self.load_chats()

        self.add_widget(layout)

    def load_chats(self):
        """Carica e visualizza le chat dell'utente."""
        try:
            # Fetch all the chats from Telegram
            chats = self.client.get_dialogs()
            for chat in chats:
                chat_button = Button(text=chat.name, size_hint_y=None, height=40)
                self.chat_list_layout.add_widget(chat_button)
        except Exception as e:
            print(f"Errore durante il caricamento delle chat: {e}")


class ChatApp(App):
    def build(self):
        sm = ScreenManager()
        session_fn = './' + SESSION_NAME + '.session'
        if os.path.exists(session_fn):
            msg = "Bentornato!"
        else:
            sm.add_widget(LoginScreen(name="login"))
            msg = 'Login effettuato correttamente!'
        
        sm.add_widget(SuccessScreen(name="success", message=msg))
        sm.add_widget(ChatListScreen(name="chat_list"))
        return sm

try:
    if __name__ == "__main__":
        ChatApp().run()
except:
    pass
