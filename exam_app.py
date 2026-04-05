"""
ProctraAI - Advanced Proctored Exam Platform
Professional exam environment with JEE-style interface, eye tracking, and AI proctoring
"""

import cv2
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
from datetime import datetime
from collections import deque
import numpy as np
from PIL import Image, ImageTk, ImageDraw
import os


# Modern Lavender & Cream Color Palette (from "Coming Soon" design)
COLORS = {
    'primary': '#8B7BC9',          # Rich Lavender (main theme)
    'primary_light': '#B8A5D6',    # Light Lavender
    'primary_very_light': '#E2D5F0', # Very Light Lavender
    'white': '#FFFFFF',
    'accent': '#FFFACD',           # Cream/Gold (from coming-soon image)
    'accent_light': '#FFFEF0',     # Very light cream
    'dark_bg': '#F5F1FB',          # Soft lavender background
    'text_dark': '#4A3F6B',        # Dark purple text
    'text_light': '#6B5B9E',       # Medium purple text
    'border': '#D0C3E0',           # Border color
    'success': '#06D6A0',          # Green
    'warning': '#FFB703',          # Orange
    'danger': '#D62828',           # Red
    'info': '#4361EE',             # Blue
    'gray': '#A8A8A8',
    'light_gray': '#E8E8E8',
    'answered': '#06D6A0',         # Green
    'unanswered': '#FFFFFF',       # White
    'flagged': '#D62828',          # Red
    'review': '#FFB703',           # Orange
}


class AIProctorPlaceholder:
    """Placeholder for AI Model Integration"""
    
    def __init__(self):
        self.model = None
        self.model_loaded = False
    
    def load_model(self, model_path):
        """Load trained AI model"""
        try:
            print(f"[AI Proctor] Loading model from: {model_path}")
            self.model_loaded = True
        except Exception as e:
            print(f"[AI Proctor] Error loading model: {e}")
            self.model_loaded = False
    
    def detect_suspicious_activity(self, frame):
        return {'suspicious': False, 'activity': 'Normal', 'confidence': 0.95}
    
    def detect_cheating(self, frame):
        return {'cheating_detected': False, 'reason': None, 'confidence': 0.0}


class ExamQuestion:
    """Represents a single exam question"""
    
    def __init__(self, qid, question_text, options, correct_answer, marks=1):
        self.qid = qid
        self.question_text = question_text
        self.options = options
        self.correct_answer = correct_answer
        self.marks = marks
        self.user_answer = None
        self.answered_at = None
        self.flagged = False  # NEW: Flag for review
    
    def get_status(self):
        """Get question status"""
        if self.flagged:
            return 'flagged' if self.user_answer else 'review'
        return 'answered' if self.user_answer else 'unanswered'
    
    def to_dict(self):
        return {
            'qid': self.qid,
            'question': self.question_text,
            'options': self.options,
            'correct': self.correct_answer,
            'user_answer': self.user_answer,
            'marks': self.marks,
            'flagged': self.flagged
        }


class ExamSession:
    """Manages exam session and student data"""
    
    def __init__(self, roll_no, passkey):
        self.roll_no = roll_no
        self.passkey = passkey
        self.start_time = datetime.now()
        self.questions = []
        self.current_question_index = 0
        self.score = 0
        self.suspicious_activity_count = 0
        self.cheating_detected_count = 0
        self.camera_disconnections = 0
        self.look_away_count = 0
        self.face_detected_last = True
        self.look_away_threshold = 4
        self.no_face_frames = 0
    
    def add_question(self, question):
        self.questions.append(question)
    
    def get_current_question(self):
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
    
    def next_question(self):
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            return True
        return False
    
    def previous_question(self):
        if self.current_question_index > 0:
            self.current_question_index -= 1
            return True
        return False
    
    def jump_to_question(self, index):
        """Jump to a specific question"""
        if 0 <= index < len(self.questions):
            self.current_question_index = index
            return True
        return False
    
    def record_answer(self, answer):
        current = self.get_current_question()
        if current:
            current.user_answer = answer
            current.answered_at = datetime.now()
    
    def toggle_flag(self):
        """Toggle flag on current question"""
        current = self.get_current_question()
        if current:
            current.flagged = not current.flagged
    
    def calculate_score(self):
        score = 0
        for question in self.questions:
            if question.user_answer == question.correct_answer:
                score += question.marks
        return score
    
    def get_session_report(self):
        return {
            'roll_no': self.roll_no,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': (datetime.now() - self.start_time).total_seconds(),
            'score': self.calculate_score(),
            'total_marks': sum(q.marks for q in self.questions),
            'suspicious_activities': self.suspicious_activity_count,
            'cheating_incidents': self.cheating_detected_count,
            'camera_disconnections': self.camera_disconnections,
            'look_away_count': self.look_away_count,
            'questions_answered': sum(1 for q in self.questions if q.user_answer),
            'questions_flagged': sum(1 for q in self.questions if q.flagged),
            'questions_total': len(self.questions),
            'answers': [q.to_dict() for q in self.questions]
        }


class CameraFeed:
    """Handle real-time camera feed with AI monitoring"""
    
    def __init__(self, exam_session, ai_proctor):
        self.exam_session = exam_session
        self.ai_proctor = ai_proctor
        self.cap = None
        self.running = False
        self.frame = None
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
    
    def initialize_camera(self):
        """Initialize camera connection"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            return False
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        return True
    
    def get_frame(self):
        """Get current camera frame"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                self.frame = frame
                return frame
        return None
    
    def detect_faces(self, frame):
        """Detect faces in frame with better filtering"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        height, width = frame.shape[:2]
        
        # Better cascade parameters to reduce false positives
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.05,      # Smaller scale factor = more thorough but stricter
            minNeighbors=8,         # Increased from 5 = requires more neighbors for detection
            flags=cv2.CASCADE_SCALE_IMAGE,
            minSize=(60, 60),       # Increased from 30 = ignore small objects
            maxSize=(int(height*0.8), int(width*0.8))  # Ignore very large detections
        )
        
        # Filter faces by aspect ratio (real faces are roughly square)
        filtered_faces = []
        for (x, y, w, h) in faces:
            aspect_ratio = w / h if h > 0 else 0
            # Accept faces with aspect ratio between 0.75 and 1.25 (roughly square)
            if 0.75 <= aspect_ratio <= 1.25:
                filtered_faces.append((x, y, w, h))
        
        return filtered_faces
    
    def detect_eyes(self, frame, face_region):
        """Detect eyes within face region with better filtering"""
        (x, y, w, h) = face_region
        face_roi = frame[y:y+h, x:x+w]
        gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # More strict eye detection parameters
        eyes = self.eye_cascade.detectMultiScale(
            gray_roi, 
            scaleFactor=1.05,
            minNeighbors=8,
            flags=cv2.CASCADE_SCALE_IMAGE,
            minSize=(20, 15),
            maxSize=(w//2, h//2)
        )
        
        # Filter eyes - they should be roughly circular/oval, not lines or tiny specs
        filtered_eyes = []
        for (ex, ey, ew, eh) in eyes:
            aspect_ratio = ew / eh if eh > 0 else 0
            # Eyes should be roughly 1.2-1.8 aspect ratio (wider than tall)
            if 1.0 <= aspect_ratio <= 2.0 and ew >= 20:
                filtered_eyes.append((ex, ey, ew, eh))
        
        return filtered_eyes
    
    def process_frame(self):
        """Process frame for proctoring"""
        frame = self.get_frame()
        if frame is None:
            self.exam_session.camera_disconnections += 1
            return None
        
        faces = self.detect_faces(frame)
        
        # Track look-away events
        if len(faces) == 0:
            self.exam_session.no_face_frames += 1
            if self.exam_session.no_face_frames >= self.exam_session.look_away_threshold:
                if self.exam_session.face_detected_last:
                    self.exam_session.look_away_count += 1
                    self.exam_session.face_detected_last = False
        else:
            self.exam_session.no_face_frames = 0
            self.exam_session.face_detected_last = True
        
        # Draw face boxes with color coding
        for (x, y, w, h) in faces:
            color = (0, 255, 0) if len(faces) == 1 else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.circle(frame, (x + w//2, y + h//2), 5, color, -1)
            
            # Detect eyes
            eyes = self.detect_eyes(frame, (x, y, w, h))
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(frame, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (255, 0, 0), 2)
                cv2.circle(frame, (x+ex+ew//2, y+ey+eh//2), 3, (0, 255, 255), -1)
        
        # Status indicators
        if len(faces) != 1:
            cv2.putText(frame, "[!] Check Position", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "[OK] Face Detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        cv2.putText(frame, f"Look Away: {self.exam_session.look_away_count}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        
        return frame
    
    def release(self):
        """Release camera"""
        if self.cap:
            self.cap.release()


class ProctraAIApp:
    """Main Exam Interface Application - JEE Style with Lavender Theme"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ProctraAI - Professional Exam Platform")
        self.root.geometry("1800x1000")
        self.root.configure(bg=COLORS['dark_bg'])
        
        self.exam_session = None
        self.ai_proctor = AIProctorPlaceholder()
        self.camera_feed = None
        self.exam_started = False
        self.time_remaining = 1800
        self.question_buttons = []
        
        self.default_questions = self.load_default_questions()
        
        self.show_login_screen()
    
    def show_login_screen(self):
        """Display modern, beautiful login screen with Tkinter"""
        self.clear_window()
        
        self.root.configure(bg=COLORS['dark_bg'])
        
        # Main container
        main_frame = tk.Frame(self.root, bg=COLORS['dark_bg'])
        main_frame.pack(fill='both', expand=True)
        
        # Center the card
        card_frame = tk.Frame(main_frame, bg=COLORS['white'], relief='flat', bd=0)
        card_frame.place(relx=0.5, rely=0.5, anchor='center', width=420, height=550)
        
        # Add subtle shadow effect with border frame
        shadow = tk.Frame(main_frame, bg=COLORS['primary_very_light'], relief='flat', bd=0)
        shadow.place(relx=0.5, rely=0.505, anchor='center', width=430, height=560)
        card_frame.lift()
        
        # Header with gradient-like appearance
        header = tk.Frame(card_frame, bg=COLORS['primary'], height=120, relief='flat', bd=0)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Logo
        tk.Label(header, text="ProctraAI", font=('Arial', 42, 'bold'),
                fg=COLORS['white'], bg=COLORS['primary']).pack(pady=(25, 5))
        
        tk.Label(header, text="AI-Powered Secure Exam Platform", 
                font=('Arial', 9), fg=COLORS['primary_light'], bg=COLORS['primary']).pack()
        
        # Form area
        form_frame = tk.Frame(card_frame, bg=COLORS['white'])
        form_frame.pack(fill='both', expand=True, padx=35, pady=30)
        
        # Roll Number
        tk.Label(form_frame, text="Roll Number", font=('Arial', 10, 'bold'),
                fg=COLORS['text_dark'], bg=COLORS['white']).pack(anchor='w', pady=(0, 8))
        
        self.roll_entry = tk.Entry(form_frame, font=('Arial', 11),
                                   bg=COLORS['dark_bg'], fg=COLORS['text_dark'],
                                   relief='solid', bd=1, 
                                   insertbackground=COLORS['primary'])
        self.roll_entry.pack(fill='x', ipady=11, pady=(0, 18))
        self.roll_entry.bind('<FocusIn>', lambda e: self._login_entry_focus(self.roll_entry))
        self.roll_entry.bind('<FocusOut>', lambda e: self._login_entry_blur(self.roll_entry))
        
        # Passcode
        tk.Label(form_frame, text="Passcode", font=('Arial', 10, 'bold'),
                fg=COLORS['text_dark'], bg=COLORS['white']).pack(anchor='w', pady=(0, 8))
        
        self.pass_entry = tk.Entry(form_frame, font=('Arial', 11),
                                   bg=COLORS['dark_bg'], fg=COLORS['text_dark'],
                                   relief='solid', bd=1, show='•',
                                   insertbackground=COLORS['primary'])
        self.pass_entry.pack(fill='x', ipady=11, pady=(0, 8))
        self.pass_entry.bind('<FocusIn>', lambda e: self._login_entry_focus(self.pass_entry))
        self.pass_entry.bind('<FocusOut>', lambda e: self._login_entry_blur(self.pass_entry))
        self.pass_entry.bind('<Return>', lambda e: self.verify_and_start())
        
        # Forgot password link
        tk.Label(form_frame, text="Forgot passcode?", font=('Arial', 8),
                fg=COLORS['primary'], bg=COLORS['white'], cursor='hand2').pack(anchor='e', pady=(0, 20))
        
        # Error label
        self.error_label = tk.Label(form_frame, text="", font=('Arial', 9),
                                   fg=COLORS['danger'], bg=COLORS['white'])
        self.error_label.pack(pady=(0, 12))
        
        # Login button
        login_btn = tk.Button(form_frame, text="START EXAM", 
                             command=self.verify_and_start,
                             font=('Arial', 11, 'bold'),
                             bg=COLORS['primary'], fg=COLORS['white'],
                             relief='flat', bd=0, cursor='hand2',
                             activebackground=COLORS['accent'],
                             activeforeground=COLORS['white'],
                             highlightthickness=0)
        login_btn.pack(fill='x', ipady=13, pady=(5, 20))
        
        # Demo info
        tk.Label(form_frame, text="Demo: Roll=123  Passcode=exam123",
                font=('Arial', 8), fg=COLORS['text_light'], bg=COLORS['white']).pack()
    
    def _login_entry_focus(self, entry):
        """Handle login entry focus"""
        entry.config(bg=COLORS['primary_very_light'], relief='solid', bd=2)
    
    def _login_entry_blur(self, entry):
        """Handle login entry blur"""
        entry.config(bg=COLORS['dark_bg'], relief='solid', bd=1)
    
    def verify_and_start(self):
        """Verify and start exam"""
        roll_no = self.roll_entry.get().strip()
        passcode = self.pass_entry.get().strip()
        
        if not roll_no:
            self.error_label.config(text="⚠ Enter Roll Number")
            return
        
        if not passcode or len(passcode) < 4:
            self.error_label.config(text="⚠ Passcode must be 4+ chars")
            return
        
        self.exam_session = ExamSession(roll_no, passcode)
        for q in self.default_questions:
            self.exam_session.add_question(q)
        
        self.camera_feed = CameraFeed(self.exam_session, self.ai_proctor)
        if not self.camera_feed.initialize_camera():
            messagebox.showerror("Camera Error", "Cannot access camera.")
            return
        
        self.exam_started = True
        self.time_remaining = 1800
        self.show_exam_screen()
    
    def show_exam_screen(self):
        """JEE-style exam interface"""
        self.clear_window()
        
        # Header
        header = tk.Frame(self.root, bg=COLORS['primary'], height=80)
        header.pack(fill='x', padx=0, pady=0)
        header.pack_propagate(False)
        
        hdr = tk.Frame(header, bg=COLORS['primary'])
        hdr.pack(fill='x', padx=20, pady=15)
        
        left_hdr = tk.Frame(hdr, bg=COLORS['primary'])
        left_hdr.pack(side='left', fill='x', expand=True)
        
        tk.Label(left_hdr, text="ProctraAI - General Knowledge & Science",
                font=('Arial', 14, 'bold'),
                fg=COLORS['white'], bg=COLORS['primary']).pack(anchor='w')
        
        tk.Label(left_hdr, text=f"Roll: {self.exam_session.roll_no}",
                font=('Arial', 11, 'bold'),
                fg=COLORS['primary_light'], bg=COLORS['primary']).pack(anchor='w')
        
        timer_frame = tk.Frame(hdr, bg=COLORS['primary'])
        timer_frame.pack(side='right')
        
        tk.Label(timer_frame, text="Time Remaining",
                font=('Arial', 11, 'bold'),
                fg=COLORS['primary_light'], bg=COLORS['primary']).pack()
        
        self.timer_label = tk.Label(timer_frame, text="30:00",
                                   font=('Arial', 24, 'bold'),
                                   fg=COLORS['warning'], bg=COLORS['primary'])
        self.timer_label.pack()
        
        # Main content
        content = tk.Frame(self.root, bg=COLORS['dark_bg'])
        content.pack(fill='both', expand=True, padx=12, pady=12)
        
        # Left - Question Display
        left_content = tk.Frame(content, bg=COLORS['white'], highlightthickness=1, highlightbackground=COLORS['border'])
        left_content.pack(side='left', fill='both', expand=True, padx=(0, 8), pady=0)
        
        # Question header
        q_hdr = tk.Frame(left_content, bg=COLORS['primary_light'])
        q_hdr.pack(fill='x', padx=12, pady=(12, 8))
        
        self.q_number_label = tk.Label(q_hdr, text="Question 1/25", font=('Arial', 12, 'bold'),
                                      fg=COLORS['primary'], bg=COLORS['primary_light'])
        self.q_number_label.pack(anchor='w')
        
        # Question text
        q_text_frame = tk.Frame(left_content, bg=COLORS['white'])
        q_text_frame.pack(fill='x', padx=12, pady=(8, 10))
        
        self.q_text = tk.Label(q_text_frame, text="", wraplength=500,
                              font=('Arial', 13), fg=COLORS['text_dark'],
                              bg=COLORS['white'], justify='left')
        self.q_text.pack(fill='both', expand=True)
        
        # Options - Checkbox style with tick boxes
        options_frame = tk.Frame(left_content, bg=COLORS['white'])
        options_frame.pack(fill='both', expand=True, padx=12, pady=12)
        
        self.option_vars = [tk.StringVar() for _ in range(4)]
        self.option_buttons = []
        
        for i in range(4):
            opt_frame = tk.Frame(options_frame, bg='#f5f5f5', relief='solid', bd=1, highlightthickness=0, height=50)
            opt_frame.pack(fill='x', pady=8, ipady=8, padx=0)
            opt_frame.pack_propagate(False)
            
            # Container for checkbox + text
            check_container = tk.Frame(opt_frame, bg='#f5f5f5')
            check_container.pack(side='left', fill='both', expand=True, padx=10, pady=0)
            
            # Checkbox square
            checkbox = tk.Canvas(check_container, width=24, height=24, bg='#f5f5f5', 
                                highlightthickness=0, relief='flat', bd=0)
            checkbox.pack(side='left', padx=(0, 12), pady=0)
            self.option_buttons.append({'canvas': checkbox, 'idx': i})
            
            # Option text label
            opt_label = tk.Label(check_container, text="", font=('Arial', 12),
                               bg='#f5f5f5', fg=COLORS['text_dark'], justify='left')
            opt_label.pack(side='left', fill='both', expand=True, anchor='w')
            
            # Bind click event
            opt_frame.bind('<Button-1>', lambda e, idx=i: self.select_option(idx))
            check_container.bind('<Button-1>', lambda e, idx=i: self.select_option(idx))
            checkbox.bind('<Button-1>', lambda e, idx=i: self.select_option(idx))
            opt_label.bind('<Button-1>', lambda e, idx=i: self.select_option(idx))
            
            # Store label for updating
            self.option_buttons[-1]['label'] = opt_label
            self.option_buttons[-1]['frame'] = opt_frame
        
        # Navigation & Flag
        nav_frame = tk.Frame(left_content, bg=COLORS['light_gray'])
        nav_frame.pack(fill='x', padx=12, pady=8)
        
        prev_btn = tk.Button(nav_frame, text="← Prev", command=self.show_previous_question,
                            font=('Arial', 10, 'bold'), bg=COLORS['primary'],
                            fg=COLORS['white'], relief='flat', padx=12, pady=6,
                            activebackground=COLORS['primary_light'],
                            activeforeground=COLORS['white'])
        prev_btn.pack(side='left', padx=4)
        
        self.flag_btn = tk.Button(nav_frame, text="⚐ Flag", command=self.toggle_flag,
                                 font=('Arial', 10, 'bold'), bg=COLORS['warning'],
                                 fg=COLORS['white'], relief='flat', padx=12, pady=6,
                                 activebackground=COLORS['danger'],
                                 activeforeground=COLORS['white'])
        self.flag_btn.pack(side='left', padx=4)
        
        self.q_indicator = tk.Label(nav_frame, text="1/25", font=('Arial', 12, 'bold'),
                                   fg=COLORS['primary'], bg=COLORS['light_gray'])
        self.q_indicator.pack(side='left', expand=True, padx=12)
        
        next_btn = tk.Button(nav_frame, text="Next →", command=self.show_next_question,
                            font=('Arial', 10, 'bold'), bg=COLORS['primary'],
                            fg=COLORS['white'], relief='flat', padx=12, pady=6,
                            activebackground=COLORS['primary_light'],
                            activeforeground=COLORS['white'])
        next_btn.pack(side='right', padx=4)
        
        # Submit button
        submit_btn = tk.Button(left_content, text="SUBMIT EXAM", command=self.submit_exam,
                              font=('Arial', 12, 'bold'), bg=COLORS['danger'],
                              fg=COLORS['white'], relief='flat', padx=30, pady=10,
                              activebackground=COLORS['warning'],
                              activeforeground=COLORS['white'])
        submit_btn.pack(pady=12, fill='x', padx=12)
        
        # Right - Camera & Question Grid
        right_content = tk.Frame(content, bg=COLORS['white'], highlightthickness=1, highlightbackground=COLORS['border'])
        right_content.pack(side='right', fill='both', padx=0, pady=0)
        
        # Camera section
        cam_hdr = tk.Label(right_content, text="🎥 Proctoring", font=('Arial', 11, 'bold'),
                          bg=COLORS['primary'], fg=COLORS['white'], padx=10, pady=8)
        cam_hdr.pack(fill='x')
        
        self.camera_canvas = tk.Canvas(right_content, bg=COLORS['text_dark'],
                                      width=320, height=220,
                                      highlightthickness=0)
        self.camera_canvas.pack(padx=8, pady=8, fill='both', expand=False)
        
        status_frame = tk.Frame(right_content, bg=COLORS['success'])
        status_frame.pack(fill='x', padx=8, pady=(0, 8))
        
        self.status_label = tk.Label(status_frame, text="✓ Monitoring", font=('Arial', 12, 'bold'),
                                    bg=COLORS['success'], fg=COLORS['white'], padx=10, pady=6)
        self.status_label.pack(fill='x')
        
        # Stats panel
        stats_frame = tk.Frame(right_content, bg=COLORS['light_gray'])
        stats_frame.pack(fill='x', padx=8, pady=(0, 8))
        
        self.lookaway_label = tk.Label(stats_frame, text="Look Away: 0", font=('Arial', 11, 'bold'),
                                      bg=COLORS['light_gray'], fg=COLORS['danger'])
        self.lookaway_label.pack(anchor='w', padx=8, pady=3)
        
        # Warning message
        self.warning_label = tk.Label(stats_frame, text="", font=('Arial', 11, 'bold'),
                                     bg=COLORS['warning'], fg=COLORS['white'], padx=8, pady=4)
        self.warning_label.pack(anchor='w', padx=8, pady=1, fill='x')
        
        self.suspicious_label = tk.Label(stats_frame, text="Suspicious: 0", font=('Arial', 10),
                                        bg=COLORS['light_gray'], fg=COLORS['text_light'])
        self.suspicious_label.pack(anchor='w', padx=8, pady=1)
        
        self.alerts_label = tk.Label(stats_frame, text="Alerts: 0", font=('Arial', 10),
                                    bg=COLORS['light_gray'], fg=COLORS['text_light'])
        self.alerts_label.pack(anchor='w', padx=8, pady=(1, 3))
        
        # Question grid section
        grid_hdr = tk.Label(right_content, text="Questions", font=('Arial', 11, 'bold'),
                           bg=COLORS['primary_light'], fg=COLORS['primary'], padx=10, pady=8)
        grid_hdr.pack(fill='x')
        
        # Legend - Color guide for question status
        legend_frame = tk.Frame(right_content, bg=COLORS['light_gray'])
        legend_frame.pack(fill='x', padx=8, pady=8)
        
        legend_title = tk.Label(legend_frame, text="Status Legend:", font=('Arial', 10, 'bold'),
                               bg=COLORS['light_gray'], fg=COLORS['text_dark'])
        legend_title.pack(anchor='w', padx=4, pady=(4, 6))
        
        legend_items = [
            ('■', COLORS['answered'], 'Answered'),
            ('■', COLORS['unanswered'], 'Unanswered'),
            ('■', COLORS['flagged'], 'Flagged'),
            ('■', COLORS['review'], 'Review'),
        ]
        
        for i, (sym, color, label) in enumerate(legend_items):
            lbl = tk.Label(legend_frame, text=f'{sym} {label}', font=('Arial', 10, 'bold'),
                          fg=color, bg=COLORS['light_gray'])
            lbl.grid(row=1, column=i, padx=8, pady=4, sticky='w')
        
        # Question grid - Canvas-based for reliable color persistence on macOS
        self.grid_canvas = tk.Canvas(right_content, bg=COLORS['white'], highlightthickness=0)
        self.grid_canvas.pack(fill='both', expand=True, padx=(20, 8), pady=(6, 8))
        
        self.question_buttons = {}  # Store as dict with button ID -> data
        self.button_size = 48
        self.button_gap = 6
        
        for i in range(25):
            row = i // 5
            col = i % 5
            x1 = col * (self.button_size + self.button_gap) + 2
            y1 = row * (self.button_size + self.button_gap) + 2
            x2 = x1 + self.button_size
            y2 = y1 + self.button_size
            
            # Create canvas rectangle for button
            btn_id = self.grid_canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=COLORS['answered'],
                outline='#ccc',
                width=1
            )
            
            # Create text on top
            text_id = self.grid_canvas.create_text(
                (x1 + x2) / 2, (y1 + y2) / 2,
                text=str(i + 1),
                font=('Arial', 9, 'bold'),
                fill=COLORS['white'],
                tags=f'text_{i}'
            )
            
            self.question_buttons[i] = {
                'rect_id': btn_id,
                'text_id': text_id,
                'x1': x1, 'y1': y1,
                'x2': x2, 'y2': y2,
                'question_idx': i
            }
            
            # Bind click events
            self.grid_canvas.tag_bind(btn_id, '<Button-1>', 
                                     lambda e, idx=i: self.jump_to_question(idx))
            self.grid_canvas.tag_bind(text_id, '<Button-1>', 
                                     lambda e, idx=i: self.jump_to_question(idx))
        
        # Calculate canvas size
        width = 5 * (self.button_size + self.button_gap) + 6
        height = 5 * (self.button_size + self.button_gap) + 6
        self.grid_canvas.configure(width=width, height=height)
        
        # Status summary
        summary_frame = tk.Frame(right_content, bg=COLORS['light_gray'])
        summary_frame.pack(fill='x', padx=8, pady=(0, 8))
        
        self.answered_label = tk.Label(summary_frame, text="Answered: 0/25", 
                                      font=('Arial', 10, 'bold'), bg=COLORS['light_gray'], fg=COLORS['answered'])
        self.answered_label.pack(anchor='w', padx=8, pady=2)
        
        self.flagged_label = tk.Label(summary_frame, text="Flagged: 0", 
                                     font=('Arial', 10, 'bold'), bg=COLORS['light_gray'], fg=COLORS['flagged'])
        self.flagged_label.pack(anchor='w', padx=8, pady=(0, 2))
        
        self.update_timer()
        self.update_camera_feed()
        self.display_current_question()
    
    def jump_to_question(self, index):
        """Jump to a specific question"""
        self.exam_session.jump_to_question(index)
        self.display_current_question()
    
    def toggle_flag(self):
        """Toggle flag on current question"""
        self.exam_session.toggle_flag()
        self.update_question_buttons()
        self.display_current_question()
    
    def display_current_question(self):
        """Display current question with status"""
        current = self.exam_session.get_current_question()
        if not current:
            return
        
        current_num = self.exam_session.current_question_index + 1
        total = len(self.exam_session.questions)
        
        self.q_number_label.config(text=f"Question {current_num}/{total}")
        self.q_text.config(text=current.question_text)
        self.q_indicator.config(text=f"{current_num}/{total}")
        
        # Update flag button
        flag_text = "⚐ Unflag" if current.flagged else "⚐ Flag"
        flag_color = COLORS['flagged'] if current.flagged else COLORS['warning']
        self.flag_btn.config(text=flag_text, bg=flag_color)
        
        # Update options
        for i, option_text in enumerate(current.options):
            self.option_buttons[i]['label'].config(text=option_text)
        
        # Clear selection
        for var in self.option_vars:
            var.set('')
        
        # Show previous answer if exists
        if current.user_answer is not None:
            try:
                idx = int(current.user_answer)
                if 0 <= idx < 4:
                    self.option_vars[idx].set(str(idx))
            except:
                pass
        
        self.update_option_checkboxes()
        self.update_question_buttons()
    
    def update_question_buttons(self):
        """Update question grid button colors - Canvas-based for macOS reliability"""
        for i, btn_data in self.question_buttons.items():
            q = self.exam_session.questions[i]
            status = q.get_status()
            
            # Color map with proper text contrast
            if status == 'answered':
                bg, fg = COLORS['answered'], COLORS['white']  # Green, white text
            elif status == 'unanswered':
                bg, fg = COLORS['unanswered'], COLORS['text_dark']  # White, dark text
            elif status == 'flagged':
                bg, fg = COLORS['flagged'], COLORS['white']  # Red, white text
            else:  # review
                bg, fg = COLORS['review'], '#000000'  # Orange, black text
            
            # Update canvas rectangle color
            self.grid_canvas.itemconfig(btn_data['rect_id'], fill=bg, outline='#999')
            
            # Update text color
            self.grid_canvas.itemconfig(btn_data['text_id'], fill=fg)
        
        # Update summary
        answered = sum(1 for q in self.exam_session.questions if q.user_answer)
        flagged = sum(1 for q in self.exam_session.questions if q.flagged)
        self.answered_label.config(text=f"Answered: {answered}/25")
        self.flagged_label.config(text=f"Flagged: {flagged}")
    
    def select_option(self, idx):
        """Select an option with tick box"""
        # Clear all other options first
        for i in range(4):
            if i != idx:
                self.option_vars[i].set('')
        
        # Set the selected option
        self.option_vars[idx].set(str(idx))
        current = self.exam_session.get_current_question()
        if current:
            current.user_answer = str(idx)
        self.update_option_checkboxes()
        self.update_question_buttons()
    
    def update_option_checkboxes(self):
        """Update checkbox appearance based on selection"""
        selected_idx = -1
        try:
            for var in self.option_vars:
                val = var.get()
                if val and val.strip():
                    selected_idx = int(val)
                    break
        except:
            pass
        
        for btn_data in self.option_buttons:
            canvas = btn_data['canvas']
            idx = btn_data['idx']
            
            # Clear canvas
            canvas.delete('all')
            
            if idx == selected_idx:
                # Draw checked box - filled with primary color
                canvas.create_rectangle(2, 2, 22, 22, fill=COLORS['primary'], outline=COLORS['primary'], width=1)
                # Draw white tick mark
                canvas.create_line(6, 12, 10, 16, fill='white', width=2.5)
                canvas.create_line(10, 16, 20, 6, fill='white', width=2.5)
            else:
                # Draw unchecked box - white with border
                canvas.create_rectangle(2, 2, 22, 22, fill='white', outline='#999', width=1.5)
            
            # Force canvas update
            canvas.update_idletasks()
    
    def on_answer_selected(self):
        """Record answer (for compatibility)"""
        current = self.exam_session.get_current_question()
        if current:
            for i, var in enumerate(self.option_vars):
                try:
                    if var.get():
                        current.user_answer = str(i)
                        break
                except:
                    pass
            self.update_question_buttons()
    
    def show_next_question(self):
        if self.exam_session.next_question():
            self.display_current_question()
    
    def show_previous_question(self):
        if self.exam_session.previous_question():
            self.display_current_question()
    
    def update_timer(self):
        """Update timer"""
        if self.exam_started and self.time_remaining > 0:
            mins, secs = divmod(self.time_remaining, 60)
            timer_text = f"{mins:02d}:{secs:02d}"
            self.timer_label.config(text=timer_text)
            
            if self.time_remaining > 900:
                color = COLORS['success']
            elif self.time_remaining > 300:
                color = COLORS['warning']
            else:
                color = COLORS['danger']
            
            self.timer_label.config(fg=color)
            self.time_remaining -= 1
            self.root.after(1000, self.update_timer)
        elif self.exam_started and self.time_remaining <= 0:
            self.submit_exam()
    
    def update_camera_feed(self):
        """Update camera display"""
        if self.camera_feed and self.exam_started:
            frame = self.camera_feed.process_frame()
            
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (320, 240))
                
                image = Image.fromarray(frame)
                photo = ImageTk.PhotoImage(image)
                
                self.camera_canvas.create_image(0, 0, anchor='nw', image=photo)
                self.camera_canvas.image = photo
            
            self.lookaway_label.config(
                text=f"Look Away: {self.exam_session.look_away_count}"
            )
            self.suspicious_label.config(
                text=f"Suspicious: {self.exam_session.suspicious_activity_count}"
            )
            self.alerts_label.config(
                text=f"Alerts: {self.exam_session.cheating_detected_count}"
            )
            
            # Check for look-away warnings
            look_away_count = self.exam_session.look_away_count
            if look_away_count >= 12:
                # End exam - 3 warnings exceeded
                self.warning_label.config(text="⚠ Session Terminated: Excessive Look-Away!", 
                                         bg=COLORS['danger'])
                self.exam_started = False
                self.submit_exam()
                return
            elif look_away_count >= 8:
                # Third warning
                self.warning_label.config(text="⚠ WARNING 3/3: Next look-away ends exam!", 
                                         bg=COLORS['danger'])
            elif look_away_count >= 4:
                # Second warning
                self.warning_label.config(text="⚠ WARNING 2/3: Maintain eye contact", 
                                         bg=COLORS['warning'])
            else:
                self.warning_label.config(text="")
            
            # Refresh question button colors to prevent them from fading
            self.update_question_buttons()
            
            self.root.after(100, self.update_camera_feed)
    
    def submit_exam(self):
        """Submit exam"""
        if self.camera_feed:
            self.camera_feed.release()
        
        self.exam_started = False
        
        report = self.exam_session.get_session_report()
        score = report['score']
        total = report['total_marks']
        percentage = (score / total * 100) if total > 0 else 0
        
        self.show_results_screen(score, total, percentage, report)
    
    def show_results_screen(self, score, total, percentage, report):
        """Results screen"""
        self.clear_window()
        
        # Check if exam was terminated due to excessive look-aways
        terminated = report.get('look_away_count', 0) >= 12
        
        header_bg = COLORS['danger'] if terminated else COLORS['primary']
        header = tk.Frame(self.root, bg=header_bg, height=70)
        header.pack(fill='x', padx=0, pady=0)
        header.pack_propagate(False)
        
        header_text = "⛔ Session Terminated" if terminated else "📊 Results"
        tk.Label(header, text=header_text, font=('Arial', 20, 'bold'),
                fg=COLORS['white'], bg=header_bg,
                padx=20).pack(side='left', pady=15)
        
        content = tk.Frame(self.root, bg=COLORS['dark_bg'])
        content.pack(fill='both', expand=True, padx=40, pady=40)
        
        # Termination message
        if terminated:
            termination_card = tk.Frame(content, bg=COLORS['danger'], relief='solid', bd=1)
            termination_card.pack(fill='x', pady=(0, 30), ipady=15, padx=20)
            
            tk.Label(termination_card, text="⚠️ Your exam session has been terminated!", 
                    font=('Arial', 14, 'bold'), fg=COLORS['white'], bg=COLORS['danger']).pack(pady=8)
            tk.Label(termination_card, 
                    text=f"Reason: Excessive look-away incidents ({report.get('look_away_count', 0)} detected)\nPlease maintain eye contact during exam.", 
                    font=('Arial', 11), fg=COLORS['white'], bg=COLORS['danger'], justify='center').pack(pady=8)
        
        score_card = tk.Frame(content, bg=COLORS['white'], highlightthickness=1, highlightbackground=COLORS['border'])
        score_card.pack(fill='x', pady=(0, 30) if not terminated else (0, 30))
        
        score_display = tk.Frame(score_card, bg=COLORS['light_gray'])
        score_display.pack(fill='x', padx=30, pady=30)
        
        tk.Label(score_display, text=f"{score}/{total}",
                font=('Arial', 64, 'bold'), fg=COLORS['primary'],
                bg=COLORS['light_gray']).pack()
        
        percentage_color = COLORS['success'] if percentage >= 40 else COLORS['danger']
        tk.Label(score_display, text=f"{percentage:.1f}%", font=('Arial', 36, 'bold'),
                fg=percentage_color, bg=COLORS['light_gray']).pack()
        
        status_text = "✓ PASSED" if percentage >= 40 else "✗ FAILED"
        status_color = COLORS['success'] if percentage >= 40 else COLORS['danger']
        tk.Label(score_display, text=status_text, font=('Arial', 16, 'bold'),
                fg=status_color, bg=COLORS['light_gray']).pack(pady=10)
        
        details_card = tk.Frame(content, bg=COLORS['white'], highlightthickness=1, highlightbackground=COLORS['border'])
        details_card.pack(fill='both', expand=True, pady=30)
        
        details_text = f"""
EXAM REPORT

Roll: {report['roll_no']} | Duration: {int(report['duration'])}s | Score: {report['score']}/{report['total_marks']}

PERFORMANCE
─────────────────────────────────────
• Questions Answered: {report['questions_answered']}/{report['questions_total']}
• Questions Flagged: {report['questions_flagged']}
• Correct Answers: {report['score']}
• Passing %: {percentage:.1f}%

PROCTORING REPORT
─────────────────────────────────────
• Times Looked Away: {report['look_away_count']}
• Suspicious Activities: {report['suspicious_activities']}
• Cheating Alerts: {report['cheating_incidents']}
"""
        
        txt = tk.Label(details_card, text=details_text, font=('Arial', 11),
                      bg=COLORS['white'], fg=COLORS['text_dark'],
                      justify='left', padx=40, pady=30)
        txt.pack(fill='both', expand=True)
        
        exit_btn = tk.Button(content, text="EXIT EXAM", command=self.root.quit,
                            font=('Arial', 12, 'bold'), bg=COLORS['primary'],
                            fg=COLORS['white'], relief='flat', padx=40, pady=15,
                            activebackground=COLORS['primary_light'],
                            activeforeground=COLORS['white'])
        exit_btn.pack(pady=20)
    
    def load_default_questions(self):
        """Load questions from config"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
                questions_data = config.get('exams', [{}])[0].get('questions', [])
            
            questions = []
            for q_data in questions_data:
                question = ExamQuestion(
                    qid=q_data.get('qid'),
                    question_text=q_data.get('question'),
                    options=q_data.get('options', []),
                    correct_answer=q_data.get('correct_answer'),
                    marks=q_data.get('marks', 1)
                )
                questions.append(question)
            
            return questions[:25]
        except:
            return [ExamQuestion(i, f"Q{i}", ["A", "B", "C", "D"], "0", marks=1)
                   for i in range(1, 26)]
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


def main():
    root = tk.Tk()
    app = ProctraAIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
