import json
import platform
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
from kivy.clock import Clock
from ffpyplayer.player import MediaPlayer
from kivy.uix.recycleview import RecycleView
from kivy.uix.progressbar import ProgressBar
import os
import subprocess
import requests
import threading

# CONFIGURAZIONE AMBIENTE
# Imposta True per sviluppo su PC, False per produzione su TV
DEVELOPMENT_MODE = False

BASE_URL = 'https://tele-tv-be.onrender.com'


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
    def __init__(self, chat, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.chat = chat
        self.screen_manager = screen_manager
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.back_button = Button(text="⬅ Back to chats", size_hint_y=None, height=50)
        self.back_button.bind(on_press=self.go_back)
        self.layout.add_widget(self.back_button)

        self.video_list = GridLayout(cols=4, spacing=5, size_hint_y=None)
        self.video_list.bind(minimum_height=self.video_list.setter('height'))
        self.video_api = f"{BASE_URL}/download"

        scroll_view = ScrollView()
        scroll_view.add_widget(self.video_list)
        self.layout.add_widget(scroll_view)

        self.add_widget(self.layout)

        self.buttons.append(self.back_button)
        self.load_videos()

    def go_back(self, instance):
        self.screen_manager.current = "chat_list"

    def format_file_size(self, size_bytes):
        """Converte i bytes in formato leggibile (KB, MB, GB)"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def format_duration(self, duration_seconds):
        """Converte i secondi in formato mm:ss o hh:mm:ss"""
        if not duration_seconds or duration_seconds == 0:
            return "N/A"
        
        duration_seconds = int(duration_seconds)
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def format_date(self, date_string):
        """Converte la data ISO in formato leggibile"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return "Data N/A"

    def load_videos(self):
        self.buttons.clear()
        self.video_list.clear_widgets()
        try:
            chat_id = self.chat["id"]
            response = requests.get(f"{BASE_URL}/messages/{chat_id}")
            response.raise_for_status()
            videos = response.json()
            self.video_chat_list = {}

            for i, video in enumerate(videos):
                if video.get("isVideo"):
                    url = f"{self.video_api}/{video['id']}"
                    video_name = video.get("file_name", f"video_{i}.mp4")
                    video_date = video.get("date", "")
                    
                    # Formatta la data
                    date_str = self.format_date(video_date)
                    
                    # Crea il testo del pulsante con titolo e data
                    button_text = f"[b]{video_name}[/b]\n[size=12][color=888888]📅 {date_str}[/color][/size]"
                    
                    self.video_chat_list[video['id']] = video_name

                    video_button = Button(
                        text=button_text,
                        size_hint_y=None,
                        height=120,  # Altezza per ospitare titolo + data
                        text_size=(None, None),
                        halign="center",
                        valign="middle",
                        shorten=False,
                        markup=True
                    )
                    video_button.bind(size=lambda btn, size: setattr(btn, "text_size", (size[0] - 20, None)))
                    video_button.bind(
                        on_press=lambda instance, video_name=video_name, url=url:
                            self.show_video_options(
                                video_label=video_name,
                                video_ext=video_name.split('.')[-1],
                                download_link=url
                            )
                    )
                    self.buttons.append(video_button)
                    self.video_list.add_widget(video_button)
            self.reset_focus()
        except Exception as e:
            print(f"Errore nel caricamento dei video: {e}")

    def show_video_options(self, video_label="video", video_ext='mp4', download_link=None):
        videoname = f"temp.{video_ext}"
        self.app_dir = App.get_running_app().user_data_dir
        
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_layout.add_widget(Label(text=video_label, font_size='18sp'))

        self.progress_label = Label(text="Avvio scaricamento...", font_size='14sp')
        popup_layout.add_widget(self.progress_label)

        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=20)
        popup_layout.add_widget(self.progress_bar)

        # Info aggiuntiva per dimensione file
        self.file_size_label = Label(text="", font_size='12sp', color=(0.7, 0.7, 0.7, 1))
        popup_layout.add_widget(self.file_size_label)

        # Nessun pulsante - il download parte automaticamente
        self.buttons = []  # Lista vuota, nessun pulsante da navigare

        self.popup = Popup(title="Scaricamento video", content=popup_layout, size_hint=(0.6, 0.5))
        self.popup.open()
        
        # Avvia automaticamente il download dopo aver aperto il popup
        Clock.schedule_once(lambda dt: self.play_video(download_link, filename=videoname), 0.1)

    def download_video(self, endpoint_url, filename='temp.mp4'):
        try:
            response = requests.get(endpoint_url, stream=True)
            response.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            self.popup.dismiss()
            print(f"[✓] Video scaricato: {filename}")
        except requests.exceptions.RequestException as e:
            print(f"[!] Errore nel download: {e}")

    def play_video(self, endpoint_url, filename='temp.mp4'):
        # Crea il percorso nella directory AppData/Roaming invece che nella directory dell'app
        if DEVELOPMENT_MODE:
            # In sviluppo, salva in una cartella accessibile
            app_data_dir = os.path.expanduser("~/AppData/Roaming/chat")
            if not os.path.exists(app_data_dir):
                os.makedirs(app_data_dir)
            file_path = os.path.join(app_data_dir, filename)
        else:
            # Su TV, usa la directory dell'app
            file_path = os.path.join(self.app_dir, filename)
            
        print(f"Percorso di salvataggio: {file_path}")
        
        def download_thread():
            try:
                response = requests.get(endpoint_url, stream=True)
                response.raise_for_status()

                total_length = response.headers.get('content-length')
                if total_length is None:
                    total_length_int = 0
                    Clock.schedule_once(lambda dt: setattr(self.progress_label, 'text', "Dimensione sconosciuta, scaricamento in corso..."))
                else:
                    total_length_int = int(total_length)
                    # Mostra la dimensione del file
                    file_size_str = self.format_file_size(total_length_int)
                    Clock.schedule_once(lambda dt: self.update_progress(0, file_size_str))

                downloaded = 0

                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_length_int:
                                percent = int(downloaded * 100 / total_length_int)
                                file_size_str = self.format_file_size(total_length_int)
                                Clock.schedule_once(lambda dt, p=percent, fs=file_size_str: self.update_progress(p, fs))
                            else:
                                Clock.schedule_once(lambda dt, d=downloaded: setattr(self.progress_label, 'text', f"Scaricamento... {self.format_file_size(d)}"))

                Clock.schedule_once(lambda dt: self.on_download_complete(file_path))

            except requests.exceptions.RequestException as e:
                Clock.schedule_once(lambda dt: setattr(self.progress_label, 'text', "[!] Errore nel download"))
                print(f"[!] Errore nella riproduzione: {e}")

        threading.Thread(target=download_thread, daemon=True).start()

    def update_progress(self, percent, file_size_str=""):
        self.progress_bar.value = percent
        self.progress_label.text = f"Scaricamento... {percent}%"
        if hasattr(self, 'file_size_label') and file_size_str:
            self.file_size_label.text = f"Dimensione: {file_size_str}"
        

    def play_with_ffpyplayer(self, filepath):
        # ffpyplayer apre il file locale
        player = MediaPlayer(filepath)
        while True:
            frame, val = player.get_frame()
            if val == 'eof':
                break

    def open_file_cross_platform(self, filepath):
        """Apre un file con il programma predefinito del sistema operativo (solo in modalità sviluppo)"""
        if not DEVELOPMENT_MODE:
            print(f"[DEBUG] Modalità TV: non apro file esterni. File scaricato: {filepath}")
            return True
            
        try:
            print(f"Tentativo di apertura file: {filepath}")
            
            # Verifica che il file esista
            if not os.path.exists(filepath):
                print(f"Errore: File non trovato: {filepath}")
                return False
                
            # Verifica dimensione file
            file_size = os.path.getsize(filepath)
            print(f"Dimensione file: {file_size} bytes")
            
            if file_size == 0:
                print("Errore: File vuoto")
                return False
            
            if platform.system() == "Windows":
                # Su Windows, prova diversi metodi
                try:
                    # Metodo 1: startfile
                    os.startfile(filepath)
                    print("File aperto con os.startfile()")
                    return True
                except:
                    try:
                        # Metodo 2: subprocess con 'start'
                        subprocess.Popen(['start', '', filepath], shell=True)
                        print("File aperto con subprocess start")
                        return True
                    except:
                        try:
                            # Metodo 3: prova con VLC se installato
                            subprocess.Popen(['vlc', filepath])
                            print("File aperto con VLC")
                            return True
                        except:
                            print("Nessun metodo di apertura funzionante")
                            return False
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", filepath])
                print("File aperto con open (macOS)")
                return True
            else:  # Linux e altri Unix-like
                subprocess.Popen(["xdg-open", filepath])
                print("File aperto con xdg-open (Linux)")
                return True
                
        except Exception as e:
            print(f"Errore nell'apertura del file: {e}")
            return False

    def play_video_internal(self, filepath):
        """Riproduzione video interna usando ffpyplayer (per TV)"""
        try:
            print(f"[TV MODE] Avvio riproduzione interna: {filepath}")
            # Implementa qui la logica per la riproduzione su TV
            # Ad esempio usando ffpyplayer con un widget Kivy personalizzato
            self.play_with_ffpyplayer(filepath)
            return True
        except Exception as e:
            print(f"Errore nella riproduzione interna: {e}")
            return False

    def on_download_complete(self, filename):
        # Ferma l'animazione dello spinner (con controllo di sicurezza)
        if hasattr(self, 'spinner_event') and self.spinner_event:
            self.spinner_event.cancel()
        if hasattr(self, 'spinner_label'):
            self.spinner_label.text = "✅"  # Checkmark per completato
        
        # Aggiorna il testo
        if hasattr(self, 'progress_label'):
            self.progress_label.text = "Download completato! Apertura video..."
        
        # Piccolo delay prima di chiudere la popup
        if hasattr(self, 'popup'):
            Clock.schedule_once(lambda dt: self.popup.dismiss(), 1.0)
        
        if DEVELOPMENT_MODE:
            # MODALITÀ SVILUPPO: apre con player esterno del sistema
            print(f"[DEV MODE] Apertura con player esterno")
            if self.open_file_cross_platform(filename):
                print(f"[✓] Riproduzione avviata: {filename}")
            else:
                print(f"[!] Impossibile aprire il file: {filename}")
        else:
            # MODALITÀ TV: riproduzione interna
            print(f"[TV MODE] Riproduzione interna")
            if self.play_video_internal(filename):
                print(f"[✓] Riproduzione TV avviata: {filename}")
            else:
                print(f"[!] Errore nella riproduzione TV: {filename}")


class ChatListScreen(NavigableScreen):
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
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
        # Configurazione finestra basata sull'ambiente
        if DEVELOPMENT_MODE:
            # Modalità sviluppo: finestra ridimensionabile
            Window.size = (1280, 720)
            Window.resizable = True
            print("[DEV MODE] Modalità sviluppo attiva - Finestra ridimensionabile")
        else:
            # Modalità TV: fullscreen
            Window.fullscreen = True
            Window.resizable = False
            print("[TV MODE] Modalità TV attiva - Fullscreen")
            
        sm = ScreenManager()
        sm.add_widget(ChatListScreen(screen_manager=sm, name="chat_list"))
        return sm


if __name__ == "__main__":
    ChatApp().run()