# ProctraAI - AI-Powered Secure Exam Platform

A professional, secure, AI-enabled online exam proctoring platform built with Python and Tkinter. Features real-time face and eye detection, look-away tracking, JEE-style exam interface, and comprehensive proctoring analytics.

## 🎯 Features

### Core Exam Functionality
- **25 MCQ Exam** - General Knowledge & Science format
- **30-Minute Timer** - Countdown with automatic submission
- **JEE-Style Interface** - 5x5 question grid navigation
- **Progress Tracking** - Real-time status indicators
- **Question Management**
  - Mark questions as Answered/Unanswered/Flagged/Review
  - Color-coded buttons for quick navigation
  - Resume previous answers
  - Flag questions for later review

### AI Proctoring & Security
- **Real-Time Face Detection** - AI-powered face recognition
- **Eye Tracking** - Detects when student looks away from screen
- **Look-Away Monitoring**
  - Threshold: 4 frames (~133ms) for tolerance
  - Warning system: 3 warnings before termination
  - Auto-terminates exam after 12 look-aways
- **Activity Logging** - Records suspicious activities
- **Live Camera Feed** - 320x240 video monitoring

### User Interface
- **Modern, Professional Design**
  - Lavender & white color theme
  - Responsive layout (camera + grid on right, questions on left)
  - Real-time status panel
- **Beautiful Login Screen**
  - Centered card design with shadow effect
  - Smooth focus/blur effects
  - Color-coded alerts
- **Professional Results Screen**
  - Score display with percentage
  - Pass/Fail status
  - Detailed analytics and incident reports

### Professional Features
- **Demo Credentials**: Roll=123, Passcode=exam123
- **Scoring System** - 1 mark per question, -0.25 negative marking
- **Session Reports**
  - Total questions: 25
  - Correct/incorrect answers
  - Look-away incidents
  - Suspicious activities detected
  - Session duration

## 🛠️ Technical Stack

- **Language**: Python 3.12+
- **GUI Framework**: Tkinter (built-in, cross-platform)
- **Computer Vision**: OpenCV (cv2)
- **Image Processing**: Pillow (PIL)
- **Numerical Computing**: NumPy
- **Face Detection**: Haar Cascade Classifiers (OpenCV)

## 📋 Requirements

```
opencv-python>=4.8.0
Pillow>=10.0.0
numpy>=1.24.0
```

## ⚙️ Installation

### Windows/macOS/Linux

1. **Clone or Download** the repository
   ```bash
   cd /path/to/ProctraAI
   ```

2. **Create Virtual Environment** (Recommended)
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python3 exam_app.py
   ```

## 🚀 Usage

### Starting the Exam
1. Launch the app: `python3 exam_app.py`
2. Enter credentials (Demo: Roll=123, Code=exam123)
3. Begin exam (30 minutes)

### During Exam
- **Select Answers**: Click on checkbox next to option (shows purple tick when selected)
- **Navigate Questions**: Click question number in grid (0-24)
- **Flag Questions**: Click "⚐ Flag" to mark for review
- **Previous/Next**: Use navigation buttons or question grid
- **Monitor**: Face detection runs continuously in top-right corner

### Warning System
- **4 Look-Aways**: ⚠️ WARNING 1/3 (in orange)
- **8 Look-Aways**: ⚠️ WARNING 2/3 - "Maintain eye contact" (red)
- **12 Look-Aways**: ⛔ **Exam Auto-Terminates** - Session ends with warning

### Exam Submission
- Automatic submission at 30:00
- Manual submission: Click "Submit" button
- Results show: Score, Percentage, Status (Pass/Fail at 40%)

## 📊 Color Theme

| Element | Color | Hex |
|---------|-------|-----|
| Primary (Lavender) | Deep Lavender | #7C5BA6 |
| Light Lavender | Light Lavender | #B19CD9 |
| Very Light Lavender | Background | #E6D9F0 |
| White | Clean Background | #FFFFFF |
| Success | Green | #06D6A0 |
| Warning | Orange | #FFB703 |
| Danger | Red | #D62828 |

## 🎮 Question Grid Interface

- **5x5 Grid** - 25 questions
- **Color Coding**:
  - 🟢 Green - Answered
  - ⚪ White - Unanswered
  - 🔴 Red - Flagged
  - 🟠 Orange - Review

## 📷 Camera Setup

- **Resolution**: 320x240 (optimized for face detection)
- **Update Rate**: 100ms (10 FPS monitoring)
- **Cascade**: haarcascade_frontalface_default.xml
- **Eye Detection**: haarcascade_eye.xml

### Camera Requirements
- USB Webcam or built-in camera
- Proper lighting recommended
- Clear view of face (not obstructed)
- Stable internet (if cloud-based future version)

## 📁 Project Structure

```
ProctraAI/
├── exam_app.py           # Main application file (850+ lines)
├── config.json           # Exam questions and configuration
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── .venv/               # Virtual environment (local)
```

## 🔧 Configuration

### Exam Settings (in `config.json`)
```json
{
  "exam": {
    "name": "General Knowledge & Science",
    "duration": 30,
    "total_questions": 25,
    "marks_per_question": 1,
    "negative_marking": 0.25
  },
  "questions": [...]
}
```

### Look-Away Settings (in `exam_app.py`)
- **Threshold**: Line 113 - `look_away_threshold = 4`
- **Warning Levels**: Line 847-862 in `update_camera_feed()`
- **Termination Limit**: 12 look-aways

## 🔐 Security Features

- **Face Verification** - Ensures test-taker is present
- **Continuous Monitoring** - Real-time face detection
- **Look-Away Tracking** - Detects exam violations
- **Activity Logging** - Records all incidents
- **Auto-Termination** - Enforces proctoring rules
- **Session Reports** - Detailed analytics for review

## 📈 Exam Scoring

- **Pass**: 40% and above
- **Fail**: Below 40%
- **Marks/Question**: 1 mark
- **Total Marks**: 25
- **Negative Marking**: -0.25 for wrong answers

**Example**:
- 20 Correct: 20 marks (80%)
- 10 Correct, 15 Wrong: 10 - (15 × 0.25) = 6.25 marks (25%)

## 🎓 Academic Use

Perfect for:
- Online exams and assessments
- Competitive exam preparation (JEE, GATE, etc.)
- Remote proctored testing
- Skill evaluation platforms
- Educational institutions

## 🔄 AI Model Integration

The `AIProctorPlaceholder` class (Line 44-65) is ready for custom AI models:

```python
class AIProctorPlaceholder:
    def load_model(self, model_path):
        # Load your trained model here
        pass
    
    def detect_suspicious_activity(self, frame):
        # Implement custom detection logic
        pass
    
    def detect_cheating(self, frame):
        # Implement cheating detection
        pass
```

**To integrate your model**:
1. Implement the three methods above
2. Update model paths in `__init__` method of `ProctraAIApp`
3. Call methods in `process_frame()` method

## 🐛 Troubleshooting

### Camera Not Working
- Check camera permissions (macOS requires "Camera" permission in Settings)
- Verify camera is not in use by another app
- Try restarting the application

### Face Detection Issues
- Improve lighting in your room
- Position face closer to camera
- Ensure face is clearly visible (no obstruction)
- Background objects on shelves are now filtered automatically

### Tkinter Not Found (Linux)
```bash
sudo apt-get install python3-tk
```

### Performance Issues
- Close other applications
- Check camera resolution settings
- Verify system RAM (2GB minimum recommended)

## 📝 License

Open source - Modify and use as needed

## 👨‍💻 Developer Notes

### Adding Custom Exam Questions
Edit `config.json` with your question set - maintains compatibility with all features

### Modifying Timer
Change `self.exam_duration = 30` in `show_exam_screen()` method (default: 30 minutes)

### Adjusting Proctoring Sensitivity
- Look-away threshold: Line 113
- Warning levels: Line 847-862
- Face detection parameters: Line 217-237

## 🌟 Future Enhancements

- ✅ Web-based version (Flask/Django)
- ✅ Database integration for question banks
- ✅ Admin dashboard for exam management
- ✅ Advanced AI models for behavior analysis
- ✅ Multi-exam support
- ✅ Detailed student reports and analytics
- ✅ Integration with Learning Management Systems (LMS)

## 📞 Support

For issues or questions:
1. Check troubleshooting section
2. Verify all dependencies are installed
3. Ensure Python 3.10+ is installed
4. Check camera/microphone permissions

## 🎉 Key Features Summary

| Feature | Status |
|---------|--------|
| JEE-Exam Style Interface | ✅ Complete |
| Real-Time Face Detection | ✅ Complete |
| Eye Tracking | ✅ Complete |
| Look-Away Warnings | ✅ Complete |
| Question Navigation | ✅ Complete |
| Timer & Auto-Submit | ✅ Complete |
| Results & Analytics | ✅ Complete |
| Cross-Platform Support | ✅ Complete |
| Professional UI/UX | ✅ Complete |
| AI Model Ready | ✅ Ready |

---

**ProctraAI** - Secure, Professional, AI-Powered Exam Proctoring

*Made with ❤️ for secure online education*
