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
        """Verifica il codice e mostra la schermata delle chat."""
        try:
            self.client.sign_in(PHONE_NUMBER, code)
            print("Login riuscito!")
            self.manager.current = "success"  # Mostra la schermata delle chat
        except Exception as e:
            print(f"Errore: {e}")

class Chats(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.client.connect()

        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text="Elenco delle chat", font_size='20sp', size_hint_y=None, height=50))

        scroll_view = ScrollView(size_hint=(1, 1))
        self.chat_list_layout = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=10)
        self.chat_list_layout.bind(minimum_height=self.chat_list_layout.setter('height'))
        scroll_view.add_widget(self.chat_list_layout)

        layout.add_widget(scroll_view)
        self.add_widget(layout)

        self.populate_chat_list()

    def populate_chat_list(self):
        """Popola l'elenco delle chat con i dialoghi dell'utente."""
        for dialog in self.client.iter_dialogs():
            if dialog.is_user or dialog.is_group or dialog.is_channel:
                chat_button = Button(
                    text=dialog.name,
                    size_hint_y=None,
                    height=50
                )
                chat_button.bind(on_press=lambda instance, d=dialog: self.open_chat(d))
                self.chat_list_layout.add_widget(chat_button)

    def open_chat(self, dialog):
        """Apre la chat selezionata e mostra i video disponibili."""
        self.manager.current = "video_list"
        self.manager.get_screen("video_list").display_videos(dialog)

class VideoListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.client.connect()

        layout = BoxLayout(orientation='vertical')
        layout.add_widget(Label(text="Elenco dei video", font_size='20sp', size_hint_y=None, height=50))

        scroll_view = ScrollView(size_hint=(1, 1))
        self.video_list_layout = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=10)
        self.video_list_layout.bind(minimum_height=self.video_list_layout.setter('height'))
        scroll_view.add_widget(self.video_list_layout)

        layout.add_widget(scroll_view)
        self.add_widget(layout)

    def display_videos(self, dialog):
        """Mostra i video disponibili nella chat selezionata."""
        self.video_list_layout.clear_widgets()
        for message in self.client.iter_messages(dialog, filter=InputMessagesFilterVideo):
            if message.video:
                video_button = Button(
                    text=message.video.attributes[0].file_name if message.video.attributes else "Video",
                    size_hint_y=None,
                    height=50
                )
                video_button.bind(on_press=lambda instance, m=message: self.download_video(m))
                self.video_list_layout.add_widget(video_button)

    def download_video(self, message):
        """Scarica il video selezionato."""
        save_path = os.path.join("downloads", message.video.attributes[0].file_name if message.video.attributes else f"video_{message.id}.mp4")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        message.download_media(file=save_path)
        self.show_popup("Download completato", f"Video salvato in {save_path}")

    def show_popup(self, title, message):
        """Mostra un popup con un messaggio."""
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_layout.add_widget(Label(text=message))
        close_button = Button(text="Chiudi", size_hint_y=None, height=50)
        popup_layout.add_widget(close_button)

        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()


class SuccessScreen(Screen):
    def __init__(self, message = "Login effettuato correttamente!", **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text=message, font_size='24sp'))
        # self.manager.current = "chat_list"
        self.add_widget(layout)






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
       
        sm.add_widget(Chats(name="chat_list"))
        # sm.add_widget(VideoListScreen(name="video_list"))
        return sm






try:
    if __name__ == "__main__":
        ChatApp().run()
except:pass
