# EduVerse AI 🚀
### Advanced AI-Powered Personalized Learning Workspace for Children

EduVerse AI is a next-generation adaptive education platform designed to make learning immersive, accessible, and highly personalized for kids. Built on the robust **Django (Python)** framework and integrated with Google's **Gemini AI**, it translates real-time student learning patterns into a customizable digital twin.

---

## 🌟 Core Features

### 1. Personal AI Tutor Workspace
* **Adaptive Dialogue Engine**: Buddy AI dynamically adjusts its teaching strategy (switching between direct hints, detailed visual explanations, or extra praise) depending on the child's mastery levels.
* **Hands-Free Speech Controls**: Employs the browser Web Speech API for real-time dictation (Speech-to-Text) and friendly text-to-speech reading with kid-focused vocal pitch adjustment.

### 2. Interactive SVG Canvas Playground
* **Dynamic Fraction Slices**: Leverages trigonometry to slice SVG circles into fraction parts dynamically.
* **Orbits & Solar Systems**: Draws concentric orbital tracks with orbiting planet spheres revolving using CSS rotation keyframes.
* **Coding Block sequences**: Displays Scratch-style programming loop configurations.

### 3. Spaced Repetition Flashcards & Quizzes
* **SM-2 Spaced Repetition Engine**: Calculates card review intervals based on child familiarity rating inputs, maximizing memory retention.
* **Adaptive Quizzes**: Generates 5-question quizzes that become harder or easier automatically based on immediate answer correctness.

### 4. Coin Shop & Visual Themes
* **Streak & Level Indicators**: Tracks daily study streaks and levels to gamify the learning routine.
* **Visual Theme Customizations**: Allows children to buy profile avatars and visual skins (e.g., Space Explorer or Magic Kingdom) with coins earned by completing planner tasks.

### 5. Parent Room & AI Pedagogical Advisor
* **Mastery Metrics charts**: Displays progress visual graphs powered by Chart.js.
* **Offline Advisor recommendations**: Scans digital twin learning struggles in `LearningMemory` and outputs actionable offline learning tips for parents to try with their children.

---

## 🛠️ Technology Stack

* **Backend & Database**: 
  * **Django (Python)**: Handles session caching, views logic, APIs, and auth wrappers.
  * **Django ORM**: Maps data structures to a SQLite database.
* **Artificial Intelligence**:
  * **Google Gemini AI Client**: Powers cognitive dialogue generation and digital twin evaluation.
* **Frontend Interface**:
  * **HTML5 & CSS Variables**: Theme variables enabling glassmorphic design skins.
  * **Bootstrap 5**: Grid responsive alignments.
  * **Chart.js**: Metrics rendering.
* **Accessibility**:
  * **OpenDyslexic Font helper**: Integrated toggle helper to adapt page layouts for readers with dyslexia.

---

## 🚀 Setup & Installation Instructions

Follow these steps to run the Django server locally on your computer:

### 1. Prerequisites
Ensure you have **Python 3.10+** and **Git** installed.

### 2. Clone the Repository
```bash
git clone https://github.com/saurabhprime01/EduVerse-AI.git
cd EduVerse-AI
```

### 3. Create a Virtual Environment & Install Dependencies
```bash
# Create environment
python -m venv .venv

# Activate environment (Windows PowerShell)
.venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 4. Configure Environment Credentials
Create a `.env` file in the project root directory and add your Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=django_secret_key_here
DEBUG=True
```

### 5. Run Database Migrations
```bash
python manage.py migrate
```

### 6. Start the Development Server
```bash
python manage.py runserver
```
Visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your web browser to access the live application!

---

## 🔑 Seeded Demo Credentials

To check dashboard charts and learning twin records right away, log in with these seeded accounts:

### 1. Student Account
* **Username**: `alex`
* **Password**: `eduverse123`

### 2. Parent Account
* **Username**: `parent`
* **Password**: `eduverse123`
