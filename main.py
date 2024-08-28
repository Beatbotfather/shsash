from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.utils import platform
from kivy.metrics import dp
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.clock import Clock
import os
import shutil
from datetime import datetime
from kivy.uix.textinput import TextInput

class LongPressButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.long_press_time = 1  # Время в секундах для длинного нажатия
        self.touch_time = 0
        self.long_press_callback = None
        self.short_press_callback = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_time = Clock.get_time()
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            if Clock.get_time() - self.touch_time < self.long_press_time:
                if self.short_press_callback:
                    self.short_press_callback(self.text)
            else:
                if self.long_press_callback:
                    self.long_press_callback(self.text)
        return super().on_touch_up(touch)

class FileManagerApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_path = self.get_base_directory()
        self.camera_popup = None
        self.camera = None
        self.photo_count = 0  # Счетчик фотографий

    def build(self):
        Window.size = (dp(360), dp(640))
        
        self.layout = BoxLayout(orientation='vertical')
        
        self.title_button = Button(text='File Manager', size_hint_y=None, height=dp(50))
        self.layout.add_widget(self.title_button)
        
        control_layout = BoxLayout(size_hint_y=None, height=dp(50))
        delete_all_btn = Button(text='Удалить всё', on_press=self.delete_all_prompt)
        control_layout.add_widget(delete_all_btn)
        
        if self.current_path != self.get_base_directory():
            create_folder_btn = Button(text='Создать папку', on_press=self.create_folder)
            control_layout.add_widget(create_folder_btn)
        
        add_home_btn = Button(text='Добавить дом', on_press=self.add_home)
        control_layout.add_widget(add_home_btn)
        
        self.layout.add_widget(control_layout)
        
        self.add_photo_btn = Button(text='Добавить фото', on_press=self.open_camera, size_hint_y=None, height=dp(50))
        self.add_photo_btn.opacity = 0
        self.layout.add_widget(self.add_photo_btn)
        
        scroll_view = ScrollView()
        self.file_list = BoxLayout(orientation='vertical', size_hint_y=None)
        self.file_list.bind(minimum_height=self.file_list.setter('height'))
        scroll_view.add_widget(self.file_list)
        self.layout.add_widget(scroll_view)
        
        # Layout для счетчика и кнопки сброса
        counter_layout = BoxLayout(size_hint_y=None, height=dp(50))
        
        # Виджет счетчика
        self.counter_label = Label(text='Фотографий: 0', size_hint_y=None, height=dp(25))
        counter_layout.add_widget(self.counter_label)
        
        # Кнопка сброса счетчика
        self.reset_button = Button(text='Сбросить счетчик', on_press=self.reset_counter, size_hint_y=None, height=dp(25))
        counter_layout.add_widget(self.reset_button)
        
        self.layout.add_widget(counter_layout)
        
        self.load_directory()
        
        return self.layout
    
    # Остальные методы остаются без изменений

    def get_base_directory(self):
        if platform == 'android':
            return '/sdcard/main_directory/directory'
        else:
            return 'main_directory/directory'
    
    def load_directory(self, path=None):
        self.file_list.clear_widgets()
        if path:
            self.current_path = path
        
        if not os.path.exists(self.current_path):
            os.makedirs(self.current_path)
        
        if self.current_path != self.get_base_directory():
            back_btn = LongPressButton(text='..', size_hint_y=None, height=dp(50))
            back_btn.long_press_callback = self.delete_item
            back_btn.short_press_callback = lambda x: self.load_directory(os.path.dirname(self.current_path))
            self.file_list.add_widget(back_btn)
            self.add_photo_btn.opacity = 1
            
            create_folder_btn = Button(text='Создать папку', on_press=self.create_folder, size_hint_y=None, height=dp(50))
            self.file_list.add_widget(create_folder_btn)
        else:
            self.add_photo_btn.opacity = 0
        
        files_and_folders = os.listdir(self.current_path)
        
        for item in files_and_folders:
            btn = LongPressButton(text=item, size_hint_y=None, height=dp(50))
            btn.long_press_callback = self.delete_item
            btn.short_press_callback = lambda x, path=os.path.join(self.current_path, item): self.load_directory(path)
            self.file_list.add_widget(btn)
        
        self.title_button.text = os.path.basename(self.current_path) or 'File Manager'
    
    def delete_all_prompt(self, instance):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text='Вы уверены, что хотите удалить все файлы?'))
        buttons = BoxLayout(size_hint_y=None, height=dp(50))
        yes_button = Button(text='Да')
        no_button = Button(text='Нет')
        buttons.add_widget(yes_button)
        buttons.add_widget(no_button)
        content.add_widget(buttons)

        popup = Popup(title='Подтверждение', content=content, size_hint=(0.9, 0.3))
        
        yes_button.bind(on_press=self.delete_all)
        yes_button.bind(on_press=popup.dismiss)
        no_button.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def delete_all(self, instance):
        for filename in os.listdir(self.current_path):
            file_path = os.path.join(self.current_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
        self.load_directory()
    
    def create_folder(self, instance):
        existing_folders = [f for f in os.listdir(self.current_path) if f.startswith('подъезд')]
        new_number = len(existing_folders) + 1
        new_folder_name = f'подъезд{new_number}'
        os.makedirs(os.path.join(self.current_path, new_folder_name), exist_ok=True)
        self.load_directory()

    def add_home(self, instance):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text='Введите название дома'))
        input_field = TextInput(multiline=False)
        content.add_widget(input_field)
        buttons = BoxLayout(size_hint_y=None, height=dp(50))
        create_button = Button(text='Создать')
        cancel_button = Button(text='Отмена')
        buttons.add_widget(create_button)
        buttons.add_widget(cancel_button)
        content.add_widget(buttons)

        popup = Popup(title='Добавить дом', content=content, size_hint=(0.9, 0.3))
        
        create_button.bind(on_press=lambda x: self.create_home(input_field.text, popup))
        cancel_button.bind(on_press=popup.dismiss)
        
        popup.open()

    def create_home(self, name, popup):
        if name:
            new_folder_name = name
            os.makedirs(os.path.join(self.current_path, new_folder_name), exist_ok=True)
            self.load_directory()
            popup.dismiss()
        else:
            self.show_error_popup("Введите название дома")

    def open_camera(self, instance):
        try:
            self.camera = Camera(play=True)
            capture_button = Button(text='Сделать фото', size_hint_y=None, height=dp(50))
            back_button = Button(text='Назад', size_hint_y=None, height=dp(50))
            
            capture_button.bind(on_press=self.capture_image)
            back_button.bind(on_press=self.close_camera)
            
            button_layout = BoxLayout(size_hint_y=None, height=dp(50))
            button_layout.add_widget(capture_button)
            button_layout.add_widget(back_button)
            
            layout = BoxLayout(orientation='vertical')
            layout.add_widget(self.camera)
            layout.add_widget(button_layout)
            
            self.camera_popup = Popup(title='Сделать фото', content=layout, size_hint=(0.9, 0.9))
            self.camera_popup.open()
        except Exception as e:
            self.show_error_popup(f"Ошибка при открытии камеры: {str(e)}")

    def capture_image(self, instance):
        if self.camera:
            timestr = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(self.current_path, f"IMG_{timestr}.png")
            self.camera.export_to_png(file_path)
            self.photo_count += 1  # Увеличить счетчик
            self.counter_label.text = f'Фотографий: {self.photo_count}'  # Обновить текст счетчика
            self.load_directory()
            self.show_info_popup("Фото сохранено")
        else:
            self.show_error_popup("Не удалось захватить изображение")

    def close_camera(self, instance):
        if self.camera_popup:
            self.camera_popup.dismiss()
            self.camera_popup = None
        if self.camera:
            self.camera.play = False  # Остановка камеры

    def show_error_popup(self, error_message):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=error_message))
        button = Button(text="OK", size_hint_y=None, height=dp(50))
        content.add_widget(button)
        popup = Popup(title='Ошибка', content=content, size_hint=(0.9, 0.3))
        button.bind(on_press=popup.dismiss)
        popup.open()

    def show_info_popup(self, message):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))
        button = Button(text="OK", size_hint_y=None, height=dp(50))
        content.add_widget(button)
        popup = Popup(title='Информация', content=content, size_hint=(0.9, 0.3))
        button.bind(on_press=popup.dismiss)
        popup.open()

    def delete_item(self, item_name):
        item_path = os.path.join(self.current_path, item_name)
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=f'Вы уверены, что хотите удалить {item_name}?'))
        buttons = BoxLayout(size_hint_y=None, height=dp(50))
        yes_button = Button(text='Да')
        no_button = Button(text='Нет')
        buttons.add_widget(yes_button)
        buttons.add_widget(no_button)
        content.add_widget(buttons)

        popup = Popup(title='Подтверждение', content=content, size_hint=(0.9, 0.3))
        
        yes_button.bind(on_press=lambda x: self.delete_item_confirm(item_path, popup))
        yes_button.bind(on_press=popup.dismiss)
        no_button.bind(on_press=popup.dismiss)
        
        popup.open()

    def delete_item_confirm(self, item_path, popup):
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
            self.load_directory()
        except Exception as e:
            self.show_error_popup(f"Ошибка при удалении: {str(e)}")

    def reset_counter(self, instance):
        self.photo_count = 0  # Сбросить счетчик
        self.counter_label.text = 'Фотографий: 0'  # Обновить текст счетчика

if __name__ == '__main__':
    FileManagerApp().run()
