# EduFlow LMS - Empower Your Learning

EduFlow is a next-generation Learning Management System (LMS) built with Django, designed to provide a premium, gamified, and highly interactive learning experience. It combines a robust backend architecture with a modern, glassmorphism-inspired UI.

## Features

- **Gamified Learning**: Earn XP, level up, maintain learning streaks, and unlock achievements as you progress.
- **Interactive Dashboards**: Real-time progress tracking, upcoming deadlines, and personalized recommendations.
- **AI-Powered Assistance (EduAI)**: Built-in intelligent tutor to answer questions, explain concepts, and provide feedback.
- **Community Discussions**: Dedicated forums for courses and lessons to foster peer-to-peer learning.
- **Dynamic Quizzes & Assessments**: Test your knowledge with immediate grading and detailed explanations.
- **Automated Certification**: Generate downloadable, professional PDF certificates upon course completion.
- **Rich Media Support**: Integrated video players, document viewers, and code snippets.
- **Premium UI/UX**: Responsive design with vibrant gradients, smooth micro-animations, and a cohesive custom design system.

## Tech Stack

- **Backend**: Python, Django
- **Frontend**: HTML5, CSS3 (Vanilla Custom Framework), JavaScript
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Icons**: Lucide Icons
- **Fonts**: Inter (Google Fonts)

## Getting Started

### Prerequisites

- Python 3.10+
- pip (Python package installer)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/harideskzone-hue/eduflow-lms.git
   cd eduflow-lms
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Copy `.env.example` to `.env` and configure your local settings.
   ```bash
   cp .env.example .env
   ```

5. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create a Superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```
   Navigate to `http://localhost:8000` in your browser.

## Project Structure

- `accounts/`: User authentication and custom user models.
- `profiles/`: Gamification, XP tracking, and learner portfolios.
- `courses/`: Course management, categories, and syllabus.
- `materials/`: Lesson content, video, and text resources.
- `quizzes/`: Assessments, questions, and grading logic.
- `discussions/`: Course forums and Q&A.
- `ai/`: Integration for the EduAI learning assistant.
- `certificates/`: PDF generation for course completion.
- `templates/`: Django HTML templates.
- `static/`: Custom CSS framework, JavaScript, and images.
