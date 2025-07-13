import json
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
import os
import subprocess
import requests

BASE_URL = "https://18097064373b.ngrok-free.app"

class NavigableScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(on_key_down=self.on_key_down)
        self.focus_index = 0
        self.buttons = []

    def on_key_down(self, instance, key, *args):
        if not self.buttons:
            return  
        num_cols = 4
        num_rows = (len(self.buttons) + num_cols - 1) // num_cols

        row = self.focus_index // num_cols
        col = self.focus_index % num_cols

        try: 
            if key == 275:  # Freccia destra
                col = (col + 1) % num_cols
            elif key == 276:  # Freccia sinistra
                col = (col - 1) % num_cols
            elif key == 273:  # Freccia su
                row = (row - 1) % num_rows
            elif key == 274:  # Freccia giù
                row = (row + 1) % num_rows
            elif key == 13:  # Invio
                self.buttons[self.focus_index].trigger_action(duration=0)
                self.reset_focus()
            elif key == 8:  # Backspace
                if self.manager.current == "video_list":
                    self.manager.current = "chat_list"
            self.focus_index = min(row * num_cols + col, len(self.buttons) - 1)
        except Exception as e: 
            print(f"Errore nella gestione dei tasti: {e}")

        self.update_focus()

    def update_focus(self):
        for i, btn in enumerate(self.buttons):
            if isinstance(btn, Button):
                btn.background_color = (1, 1, 1, 1) if i == self.focus_index else (0.5, 0.5, 0.5, 1)

    def reset_focus(self):
        if self.buttons:
            self.focus_index = 0
            self.update_focus()

class VideoListScreen(NavigableScreen):
    def __init__(self, chat, screen_manager, endpoint = BASE_URL, **kwargs):
        super().__init__(**kwargs)
        self.chat = chat
        self.screen_manager = screen_manager
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.back_button = Button(text="⬅ Back to chats", size_hint_y=None, height=50)
        self.back_button.bind(on_press=self.go_back)

        self.layout.add_widget(self.back_button)

        self.video_list = GridLayout(cols=4, spacing=5, size_hint_y=None)
        self.video_list.bind(minimum_height=self.video_list.setter('height'))
        self.video_api = endpoint + "/download"
        scroll_view = ScrollView()
        scroll_view.add_widget(self.video_list)

        self.layout.add_widget(scroll_view)
        self.add_widget(self.layout)

        self.buttons.append(self.back_button)
        self.load_videos()

    def go_back(self, instance):
        self.screen_manager.current = "chat_list"

    def load_videos(self):
        self.buttons.clear()
        self.video_list.clear_widgets()
        video_exts = ["mp4", "mpeg", "avi"]
        try:
            chat_id = self.chat["id"]
            response = requests.get(f"{BASE_URL}/messages/{chat_id}")
            response.raise_for_status()
            videos = response.json()

            for i, video in enumerate(videos):
                if video["file_name"] is not None:
                    video_ext = video["file_name"].split(".")[-1] 
                    if video_ext in video_exts:
                        url = self.video_api + f"/{video['id']}"
                        print(url)
                        video_name = video.get("file_name", f"video_{i}.mp4")
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
                        video_button.bind(on_press=lambda instance, v=video: self.show_video_options(video_label =video_name, 
                                                                                                     video_ext=video_ext,
                                                                                                       download_link=url))
                        self.buttons.append(video_button)
                        self.video_list.add_widget(video_button)
            self.reset_focus()
        except Exception as e:
            print(f"Errore nel caricamento dei video: {e}")

    def show_video_options(self, video_label= "video", video_ext='mp4', download_link=None):
        
        videoname = f"temp.{video_ext}"

        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_layout.add_widget(Label(text=f"{video_label}", font_size='18sp'))

        btn_download = Button(text="Download", size_hint_y=None, height=40)
        btn_download.bind(on_press=lambda instance: self.download_video(download_link, filename=videoname))

        btn_play = Button(text="Play Video", size_hint_y=None, height=40)
        btn_play.bind(on_press=lambda instance: self.play_video(download_link))

        popup_layout.add_widget(btn_download)
        popup_layout.add_widget(btn_play)

        self.buttons = [btn_download, btn_play]
        self.focus_index = 0
        self.update_focus()

        self.popup = Popup(title="Opzioni video", content=popup_layout, size_hint=(0.6, 0.4))
        self.popup.open()

    def download_video(self, endpoint_url, filename='tempfile.mp4'):
        try:
            # print(endpoint_url)
            response = requests.get(endpoint_url, stream=True)
            response.raise_for_status()  # Solleva eccezione per errori HTTP

            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            self.popup.dismiss()
            print(f"[✓] Video scaricato: {filename}")
        except requests.exceptions.RequestException as e:
            print(f"[!] Errore nel download: {e}")
        

    def play_video(self, endpoint_url, filename='tempfile.mp4'):
        try:
            # print(endpoint_url)
            response = requests.get(endpoint_url, stream=True)
            response.raise_for_status()

            video_path = "./{filename}"
            with open(video_path, "wb") as f:
                j = 1
                for chunk in response.iter_content(chunk_size=8192):
                    print(j)
                    j+=1
                    if chunk:
                        f.write(chunk)
            self.popup.dismiss()
            subprocess.Popen(["xdg-open", video_path])  # Su Windows: ["start", video_path]; macOS: ["open", video_path]
            print(f"[✓] Riproduzione avviata: {video_path}")
        except requests.exceptions.RequestException as e:
            print(f"[!] Errore nella riproduzione: {e}")

class ChatListScreen(NavigableScreen):
    def __init__(self, client, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self.screen_manager = screen_manager

        layout = BoxLayout(orientation='vertical', padding=2)
        self.chat_list_layout = GridLayout(cols=4, spacing=5)
        self.chat_list_layout.bind(minimum_height=self.chat_list_layout.setter('height'))

        scroll_view = ScrollView()
        scroll_view.add_widget(self.chat_list_layout)
        layout.add_widget(scroll_view)

        self.load_chats()
        self.add_widget(layout)

    def load_chats(self):
        self.buttons.clear()
        try:
            response = requests.get(f"{BASE_URL}/chats")
            response.raise_for_status()
            chats = response.json()

            for chat in chats:
                chat_button = Button(
                    text=chat.get("title", "No Name"),
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
                self.buttons.append(chat_button)

            self.reset_focus()
        except Exception as e:
            print(f"Errore durante il caricamento delle chat: {e}")

    def open_video_list(self, chat):
        if "video_list" in self.screen_manager.screen_names:
            video_screen = self.screen_manager.get_screen("video_list")
            video_screen.chat = chat
            video_screen.load_videos()
        else:
            video_screen = VideoListScreen(chat=chat, screen_manager=self.screen_manager, name="video_list")
            self.screen_manager.add_widget(video_screen)

        self.screen_manager.current = "video_list"
        video_screen.reset_focus()

class ChatApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(ChatListScreen(client=None, screen_manager=sm, name="chat_list"))
        return sm

try:
    if __name__ == "__main__":
        ChatApp().run()
except Exception as e: 
    print(e)
