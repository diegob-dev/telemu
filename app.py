import json 
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from telethon import TelegramClient
import asyncio


credentials_path = 'mycredentials.json'

# Leggi le credenziali dal file JSON
with open(credentials_path, 'r') as f:
    credentials = json.load(f)
api_id = credentials['api_id']
api_hash = credentials['api_hash']
phone_number = credentials['phone_number']
session_name = credentials['session_name']
print(credentials)
# Telegram Client
client = TelegramClient(session_name, api_id, api_hash)

class ChatListApp(App):
    def build(self):
        # Layout principale
        self.main_layout = BoxLayout(orientation='vertical')
        
        # Titolo
        self.main_layout.add_widget(Label(text="Elenco delle chat", font_size='20sp', size_hint_y=None, height=50))
        
        # Scrolling per la lista delle chat
        scroll_view = ScrollView(size_hint=(1, 1))
        self.chat_list_layout = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=10)
        self.chat_list_layout.bind(minimum_height=self.chat_list_layout.setter('height'))
        scroll_view.add_widget(self.chat_list_layout)
        
        self.main_layout.add_widget(scroll_view)
        
        # Recupera l'elenco delle chat
        asyncio.run(self.load_chats())
        
        return self.main_layout

    async def load_chats(self):
        # Connettiti al client Telegram
        await client.start(phone=phone_number)
        
        # Recupera le chat
        async for dialog in client.iter_dialogs():
            # Aggiungi ogni chat all'elenco
            chat_name = dialog.name or f"Chat senza nome (ID: {dialog.id})"
            chat_label = Label(text=chat_name, size_hint_y=None, height=40)
            self.chat_list_layout.add_widget(chat_label)

        await client.disconnect()

if __name__ == "__main__":
    ChatListApp().run()