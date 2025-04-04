# 🎓 Research Assistant: AI-Powered Academic Profile Analyzer

<p align="center">
  <img src="https://your-image-url-here.com/logo.png" alt="Research Assistant Logo" width="200"/>
</p>

<p align="center">
  <a href="#project-overview">Overview</a> •
  <a href="#features">Features</a> •
  <a href="#technology-stack">Tech Stack</a> •
  <a href="#backend-api">Backend</a> •
  <a href="#flutter-app">Flutter App</a> •
  <a href="#ai-integration">AI Integration</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

## 🌟 Project Overview

The Research Assistant is an innovative tool designed to analyze and summarize academic profiles. It combines a powerful backend API with a user-friendly Flutter mobile application, leveraging AI to provide comprehensive insights into researchers' work, impact, and potential future directions.

## 🚀 Features

- 📊 **Academic Profile Analysis**: Detailed summaries of researchers' work, including main research areas, key contributions, and impact.
- 📚 **Publication Tracking**: Track and analyze publications, citation metrics, and research trends.
- 🧠 **AI-Powered Insights**: Utilize advanced AI models to generate nuanced analyses and predictions.
- 🎯 **Multi-Level Summaries**: Provide summaries tailored to different expertise levels (beginner, intermediate, expert).
- 📈 **Data Visualization**: Present research metrics and trends through intuitive charts and graphs.
- 📱 **Cross-Platform Mobile App**: Access all features through a sleek Flutter-based mobile application.

## 💻 Technology Stack

| Component | Technologies |
|-----------|--------------|
| Backend   | Python, FastAPI |
| AI/ML     | CrewAI, Ollama, Custom NLP models |
| Database  | [Your database choice] |
| Frontend  | Flutter |
| API Docs  | Swagger/OpenAPI |
| Deployment| [Your deployment platform] |

## 🖥️ Backend API

The backend is built with Python and FastAPI, providing a robust and scalable foundation for the Research Assistant.

### 🛠️ Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/research-assistant.git
   cd research-assistant/backend
   ```

2. Set up a virtual environment:
   ``` bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### 🔗 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /search_author` | Search for an author and analyze their profile |
| `GET /paper/{paper_id}` | Retrieve details of a specific paper |
| `POST /summarize` | Generate a summary of provided research text |

### 🧩 Key Components

- `paper_search_service.py`: Handles author searches and paper retrieval
- `crew_service.py`: Manages AI-powered analysis using CrewAI
- `rag_service.py`: Implements Retrieval-Augmented Generation for enhanced AI responses

## 📱 Flutter App

The mobile application is built with Flutter, providing a cross-platform solution for iOS and Android.

### 🛠️ Flutter App Setup

1. Navigate to the Flutter app directory:
   ```bash
   cd ../app
   ```

2. Get Flutter dependencies:
   ```bash
   flutter pub get
   ```

3. Run the app:
   ```bash
   flutter run
   ```

### 📁 App Structure

- `lib/screens/`: Contains all app screens (e.g., Home, Search, Profile Analysis)
- `lib/widgets/`: Reusable UI components
- `lib/services/`: API integration and data management
- `lib/models/`: Data models for author profiles, papers, etc.

### 🌟 Key App Features

- 🔍 Author search functionality
- 📊 Profile analysis display with customizable detail levels
- 📚 Publication list and details
- 📈 Data visualization of research metrics

## 🧠 AI Integration

The project leverages advanced AI models and techniques:

- **CrewAI**: For generating comprehensive profile analyses
- **Ollama**: Local AI model integration for faster processing
- **Custom NLP Models**: For specialized text analysis tasks

## 📊 Data Sources

- Google Scholar API

## 🔮 Future Enhancements

- 🌐 Integration with additional academic databases
- 🤝 Enhanced collaboration network analysis
- 🔔 Real-time update notifications for tracked researchers

## 🤝 Contributing

We welcome contributions to the Research Assistant project! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
