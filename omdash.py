import sys
import datetime
import os
import pygame
import pickle
import requests
import urllib3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QCalendarWidget, QLabel, QListWidget, QPushButton, QHBoxLayout, QListWidgetItem, QLCDNumber
from PyQt5.QtCore import QTimer, Qt, QRect, QCoreApplication
from PyQt5.QtGui import QTextCharFormat, QFont
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from playsound import playsound

# Suppress SSL warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Calendar Widget
        self.calendar = QCalendarWidget(self)
        layout.addWidget(self.calendar)

        # To-Do List
        self.todo_label = QLabel('Upcoming Agenda:')
        layout.addWidget(self.todo_label)
        self.todo_list = QListWidget(self)
        self.populate_todos()
        layout.addWidget(self.todo_list)

        # Overall Goal
        self.goal_label = QLabel('Overall Goal: Stay Focused and Productive!')
        layout.addWidget(self.goal_label)

        # Motivational Quotes
        self.quote_label = QLabel('')
        self.quote_label.setWordWrap(True)
        layout.addWidget(self.quote_label)
        self.fetch_motivational_quote()

        # Pomodoro Timer
        self.timer_label = QLabel('Pomodoro Timer:')
        layout.addWidget(self.timer_label)
        self.lcd = QLCDNumber(self)
        self.lcd.setStyleSheet("background-color: #d17e5a; color: #000000; font-size: 40px; font-weight: bold; border: 2px solid #000000;")
        self.lcd.setFixedSize(200, 100)
        self.lcd.display('25:00')
        layout.addWidget(self.lcd)
        self.start_button = QPushButton('Start Timer', self)
        self.start_button.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.start_button.clicked.connect(self.start_timer)
        layout.addWidget(self.start_button)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.time_left = 1500  # 25 minutes in seconds

        # Audio Player
        self.audio_button = QPushButton('Play White Noise', self)
        self.audio_button.clicked.connect(self.play_audio)
        layout.addWidget(self.audio_button)

        self.setLayout(layout)
        self.setWindowTitle('Dashboard')

        # Get screen size and set the window size
        screen_geometry = QCoreApplication.instance().desktop().availableGeometry()
        self.setGeometry(QRect(0, 0, screen_geometry.width() // 3, int(screen_geometry.height() * 0.95)))
        self.move(screen_geometry.width() * 2 // 3, 0)
        self.show()

    def populate_todos(self):
        self.todo_list.clear()
        try:
            self.fetch_calendar_events()
        except Exception as e:
            print(f"Failed to fetch calendar events: {e}")
            todos = [
                'Complete project report',
                'Attend team meeting at 11:00 AM',
                'Reply to client emails',
                'Review budget proposal',
                'Plan next week’s tasks'
            ]
            for todo in sorted(todos, key=lambda x: x.split()[-1]):
                QListWidgetItem(todo, self.todo_list)

    def start_timer(self):
        self.timer.start(1000)

    def update_timer(self):
        self.time_left -= 1
        mins, secs = divmod(self.time_left, 60)
        time_format = f'{mins:02}:{secs:02}'
        self.lcd.display(time_format)
        if self.time_left == 0:
            self.timer.stop()
            self.lcd.display('25:00')
            self.time_left = 1500

    def play_audio(self):
        pygame.mixer.init()
        pygame.mixer.music.load('nepaliInstrumental.mp3')
        pygame.mixer.music.play(-1)

    def fetch_calendar_events(self):
        credentials = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                credentials = pickle.load(token)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', ['https://www.googleapis.com/auth/calendar.readonly'])
                credentials = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(credentials, token)

        service = build('calendar', 'v3', credentials=credentials)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_date = datetime.datetime.strptime(start.split('T')[0], '%Y-%m-%d').date()
            QListWidgetItem(f"{start} - {event['summary']}", self.todo_list)

            # Highlight the dates with events
            format = QTextCharFormat()
            format.setFontWeight(QFont.Bold)
            self.calendar.setDateTextFormat(event_date, format)

    def fetch_motivational_quote(self):
        try:
            response = requests.get('https://api.quotable.io/random?tags=Character|Wisdom', verify=False)
            if response.status_code == 200:
                quote_data = response.json()
                self.quote_label.setText(f'{quote_data["content"]} - {quote_data["author"]}')
            else:
                self.quote_label.setText("The secret of getting ahead is getting started.")
        except Exception as e:
            print(f"Failed to fetch quote: {e}")
            self.quote_label.setText("The secret of getting ahead is getting started.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Dashboard()
    ex.fetch_calendar_events()
    sys.exit(app.exec_())
