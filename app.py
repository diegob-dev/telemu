import json
from telethon.tl.functions.messages import GetDialogFiltersRequest
from kivy.uix.image import Image
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
credentials_path = 'mycredentials1.json'
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
        keyboard = self.create_navigable_keyboard()
        layout.add_widget(keyboard)
        send_button = Button(text="Accedi", size_hint_y=None, height=50)
        send_button.bind(on_press=self.submit_code)
        layout.add_widget(send_button)

        self.add_widget(layout)

        self.start_client()

    def create_navigable_keyboard(self):
        """Crea una tastiera navigabile per dispositivi TV."""
        keyboard_layout = GridLayout(cols=3, size_hint_y=None, height=200)
        keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '<', 'OK']
        
        for key in keys:
            btn = Button(text=key, size_hint=(1, 1))
            btn.bind(on_press=self.handle_key_press)
            keyboard_layout.add_widget(btn)
        return keyboard_layout 
    
    def handle_key_press(self, instance):
        """Gestisce la pressione dei tasti nella tastiera personalizzata."""
        if instance.text == '<':
            self.text_input.text = self.text_input.text[:-1]
        elif instance.text == 'OK':
            self.submit_code(None)
        else:
            self.text_input.text += instance.text

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

        from kivy.uix.screenmanager import ScreenManager, Screen

class VideoListScreen(Screen):
    def __init__(self, client, chat, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self.chat = chat
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.video_list = GridLayout(cols=4, spacing=5, size_hint_y=None)
        self.video_list.bind(minimum_height=self.video_list.setter('height'))

        scroll_view = ScrollView()
        scroll_view.add_widget(self.video_list)

        self.layout.add_widget(scroll_view)
        self.add_widget(self.layout)

        self.load_videos()

    def load_videos(self):
        try:
            videos1 = self.client.get_messages(self.chat, None, filter=InputMessagesFilterDocument)
            videos2 = self.client.get_messages(self.chat, None, filter=InputMessagesFilterVideo)
            videos = videos1 + videos2

            video_extensions = {"mp4", "mkv", "avi", "mov", "flv", "webm", "mpeg"}
            i = 0

            cleaned_videos = [video for video in videos if video.file and video.file.mime_type]

            for video in cleaned_videos:
                try:
                    ext = video.file.mime_type.split("/")[1] if video.file.mime_type else "novideo"

                    if ext in video_extensions:
                        video_name = video.file.name if video.file.name else f"{i}.{ext}"
                        i += 1

                        video_button = Button(
                        text=video_name,
                        size_hint_y=None,
                        height=100,
                        text_size=(None, None),
                        halign="center",
                        valign="middle",
                        shorten=False,
                        markup=True
                        )
                        video_button.bind(size=lambda btn, size: setattr(btn, "text_size", (size[0] - 20, None)))
                        video_button.bind(on_press=lambda instance, v=video, vn=video_name: self.show_video_options(v, vn))

                        self.video_list.add_widget(video_button)
                except Exception as e:
                    print(f"Errore {e}")

        except Exception as e:
            print(f"Errore nel caricamento dei media: {e}")

    def show_video_options(self, video, videoname):
        """Mostra le opzioni per il video selezionato."""
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_layout.add_widget(Label(text=f"{videoname}", font_size='18sp'))

        btn_download = Button(text="Download", size_hint_y=None, height=40)
        btn_download.bind(on_press=lambda instance: self.download_video(video, videoname))

        btn_play = Button(text="Play Video", size_hint_y=None, height=40)
        btn_play.bind(on_press=lambda instance: self.play_video(video))

        popup_layout.add_widget(btn_download)
        popup_layout.add_widget(btn_play)

        popup = Popup(title="Opzioni video", content=popup_layout, size_hint=(0.6, 0.4))
        popup.open()

    def download_video(self, video, videoname=""):
        """Scarica il video selezionato."""
        try:
            save_path = f"./video_{videoname}"
            self.client.download_media(video, file=save_path)
            print(f"Video scaricato con successo: {save_path}")
        except Exception as e:
            print(f"Errore durante il download del video: {e}")
    
    def play_video(self, video):
        """Riproduce il video selezionato."""
        try:
            video_path = self.client.download_media(video)
            if video_path:
                import subprocess
                subprocess.Popen(["xdg-open", video_path])  # Apri con il lettore predefinito
        except Exception as e:
            print(f"Errore durante la riproduzione del video: {e}")


class ChatListScreen(Screen):
    def __init__(self, client, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self.screen_manager = screen_manager  # Gestore delle schermate

        layout = BoxLayout(orientation='vertical', padding=2)
        self.chat_list_layout = GridLayout(cols=4, spacing=5)
        self.chat_list_layout.bind(minimum_height=self.chat_list_layout.setter('height'))

        scroll_view = ScrollView()
        scroll_view.add_widget(self.chat_list_layout)
        layout.add_widget(scroll_view)

        self.load_chats()
        self.add_widget(layout)

    def load_chats(self):
        try:
            chats = self.client.get_dialogs()
            for chat in chats:
                chat_button = Button(
                    text=chat.name,
                    size_hint_y=None,
                    height=100,
                    text_size=(None, None),
                    halign="center",
                    valign="middle",
                    shorten=False,
                    markup=True
                )
                chat_button.bind(size=lambda btn, size: setattr(btn, "text_size", (size[0] - 20, None)))
                chat_button.bind(on_press=lambda instance, c=chat: self.open_video_list(c))
                self.chat_list_layout.add_widget(chat_button)
        except Exception as e:
            print(f"Errore durante il caricamento delle chat: {e}")

    def open_video_list(self, chat):
        """Apre la schermata con la lista dei video della chat selezionata."""
        video_screen = VideoListScreen(self.client, chat, name="video_list")
        self.screen_manager.add_widget(video_screen)
        self.screen_manager.current = "video_list"

            
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
            sm.add_widget(ChatListScreen(client=self.client, screen_manager=sm, name="chat_list"))
        else:
            sm.add_widget(LoginScreen(name="login", client=self.client))

        return sm


try:
    if __name__ == "__main__":
        ChatApp().run()
except Exception as e: 
    print(e)
