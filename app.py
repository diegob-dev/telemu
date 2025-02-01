import json
from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterVideo
from telethon.tl.types import InputMessagesFilterDocument
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
from kivy.uix.recycleview import RecycleView
# Caricamento credenziali da JSON
credentials_path = 'mycredentials.json'
with open(credentials_path, 'r') as f:
    credentials = json.load(f)

API_ID = credentials['api_id']
API_HASH = credentials['api_hash']
PHONE_NUMBER = credentials['phone_number']
SESSION_NAME = credentials['session_name']

class LoginScreen(Screen):
    def __init__(self, client, **kwargs):
        super().__init__(**kwargs)
        self.client = client  # Usiamo il client condiviso

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
        """Richiede il codice solo se l'utente non è autenticato."""
        if not self.client.is_user_authorized():
            self.client.send_code_request(PHONE_NUMBER)

    def submit_code(self, instance):
        """Recupera il codice e prova a effettuare il login."""
        code = self.text_input.text.strip()
        if code:
            self.verify_code(code)

    def verify_code(self, code):
        """Verifica il codice e cambia schermata."""
        try:
            self.client.sign_in(PHONE_NUMBER, code)
            print("Login riuscito!")
            self.manager.add_widget(ChatListScreen(name="chat_list", client=self.client))
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
    def __init__(self, client, **kwargs):
        super().__init__(**kwargs)
        self.client = client  # Usiamo il client passato

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text="Le tue chat:", font_size='24sp'))
        
        # ScrollView per mostrare la lista chat
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
            chats = self.client.get_dialogs()  # Ora possiamo usare self.client
            for chat in chats:
                chat_button = Button(text=chat.name, size_hint_y=None, height=40)
                chat_button.bind(on_press=self.load_media_from_chat)
                self.chat_list_layout.add_widget(chat_button)
        except Exception as e:
            print(f"Errore durante il caricamento delle chat: {e}")

    def load_media_from_chat(self, instance):
        """Carica e visualizza tutti i video disponibili nella chat selezionata."""
        chat_name = instance.text  # Otteniamo il nome della chat
        chat = next((c for c in self.client.get_dialogs() if c.name == chat_name), None)
        
        if not chat:
            print(f"Chat '{chat_name}' non trovata.")
            return

        try:
            # Otteniamo tutti i video dalla chat
            videos1 = self.client.get_messages(chat, None, filter=InputMessagesFilterDocument)
            videos2 = self.client.get_messages(chat, None, filter=InputMessagesFilterVideo)
            videos = videos1 + videos2  # Unione delle due liste
            print(len(videos))
            # Layout del popup
            popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
            popup_layout.add_widget(Label(text=f"Video in {chat_name}", font_size='18sp'))

            # Creiamo la lista dei video usando RecycleView
            video_list = VideoListView(videos, self.download_video)
            i=0
            video_extensions = {"mp4", "mkv", "avi", "mov", "flv", "webm", "mpeg"}

            for video in video_list.videos:
                ext = video.file.mime_type.split("/")[1]
                #count characters of video.file.name
                if ext in video_extensions:
                    if video.file.name is None:
                        i+=1
                        video_name = f"{i}.{ext}"
                    elif len(video.file.name) >= 20:
                        video_name = f"{video.file.name[:20]}.{ext}"
                    else:
                        video_name = video.file.name
                    x = Button(text=f"{video_name}", size_hint_y=None, height=40)
                    x.bind(on_press=lambda instance, v=video, vn=video_name: self.download_video(v, vn))
                    popup_layout.add_widget(x)

            # popup_layout.add_widget(video_list)
            # Creiamo e mostriamo il popup
            popup = Popup(title="Seleziona un video", content=popup_layout, size_hint=(0.8, 0.8))
            popup.open()

        except Exception as e:
            print(f"Errore nel caricamento dei media: {e}")


    def download_video(self, video, videoname=""):
        """Scarica il video selezionato."""
        try:
            save_path = f"./video_{videoname}"
            self.client.download_media(video, file=save_path)
            print(f"Video scaricato con successo: {save_path}")
        except Exception as e:
            print(f"Errore durante il download del video: {e}")

class VideoListView(RecycleView):
    """Lista di video in formato RecycleView"""
    def __init__(self, videos, download_callback, **kwargs):
        super().__init__(**kwargs)
        self.videos = videos
        self.download_callback = download_callback
        self.data = [{"text": video.file.name or f"Video {i+1}", "on_press": lambda btn, v=video: self.download_callback(v)} for i, video in enumerate(videos)]

class ChatApp(App):
    def build(self):
        sm = ScreenManager()
        session_fn = './' + SESSION_NAME + '.session'
        
        # Creiamo un solo client Telegram
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        self.client.connect()

        if self.client.is_user_authorized():
            print("Utente già autenticato")
            sm.add_widget(ChatListScreen(name="chat_list", client=self.client))
        else:
            sm.add_widget(LoginScreen(name="login", client=self.client))

        return sm

try:
    if __name__ == "__main__":
        ChatApp().run()
except Exception as e: 
    print(e)
