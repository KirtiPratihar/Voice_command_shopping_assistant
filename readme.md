# 🎙️ Voice Command Shopping Assistant

A full-stack, voice-activated shopping list manager featuring intelligent intent extraction, smart product suggestions, and a modern Liquid Glass UI. 

This project was built to deliver a seamless, hands-free shopping experience by combining browser-based speech recognition with an advanced NLP pipeline (Large Language Model + robust local fallback) to accurately parse user commands, manage inventory, and tailor recommendations based on user preferences.

## 🚀 Live Demo & Repository
- **Live Application:** [Insert Vercel/Hosted URL here]
- **Repository:** [https://github.com/KirtiPratihar/Voice_command_shopping_assistant.git](https://github.com/KirtiPratihar/Voice_command_shopping_assistant.git)

---

## 🏗️ System Architecture & Workflow

The application uses a decoupled architecture: a Next.js frontend handling the Liquid Glass UI and voice capture, and a FastAPI Python backend managing the NLP parsing, inventory lookup, and smart suggestions.

```mermaid
graph TD
    A[User Voice Command] -->|Web Speech API| B(Next.js Frontend)
    B -->|POST /voice-command| C{FastAPI Backend}
    
    C --> D[LLM Intent Extraction]
    D -- Fails/Offline --> E[Local Fallback Parser]
    D -- Success --> F[Intent Parsed]
    E --> F
    
    F --> G{Action Router}
    G -->|Add/Remove| H[Inventory Matcher]
    
    H --> I[(Mock Inventory JSON)]
    I --> J{Preference Engine}
    J -->|Budget| K[Filter Rating > 4.0 & Low Price]
    J -->|Premium| L[Filter Premium Tag & Rating > 4.5]
    
    K --> M[Final Selection & Explanation]
    L --> M
    
    M --> N[JSON Response]
    N --> O(Next.js Frontend UI)
    O --> P[Visual Feedback & List Update]

✨ Core Features
1. Advanced Voice Recognition & NLP
Seamless Voice Input: Utilizes the Web Speech API (webkitSpeechRecognition) for fast, zero-cost transcription directly in the browser.

Hybrid Intent Parsing: The backend utilizes a Large Language Model (LLM) to extract the core product, quantity, and intent (Add/Remove) from natural language (e.g., parsing "I want to buy two cartons of milk" to {"item": "milk", "quantity": 2, "action": "add"}).

Robust Local Fallback: If the LLM is unavailable or fails, a custom regex-based extract_core_product function strips filler words, spelled-out numbers, and unit words to guarantee a successful database query.

2. Smart Suggestions & Preference Engine
Dynamic Inventory Matching: Queries a deterministic, programmatically generated catalog of 2,200+ items stored in data/mock_inventory.json.

Preference-Based Routing: Users can toggle between "Budget" and "Premium" modes.

Premium: The engine specifically targets items tagged 'premium' with a strict quality floor (Rating ≥ 4.0).

Budget: Prioritizes lower-cost items while maintaining a quality standard.

Intelligent Substitutions: If an exact match isn't found, the system provides contextual alternatives and explains why the substitution was made (e.g., "Chose Local Whole Milk because it meets your budget preference...").

3. Shopping List Management
Automated Categorization: Items added to the list are automatically categorized (e.g., Dairy, Produce, Snacks) based on their database metadata.

Full CRUD via Voice: Users can add, modify, or remove items solely through spoken commands.

4. Modern UI/UX
Liquid Glass Interface: Built with Tailwind CSS leveraging backdrop-blur and semi-transparent layers for a minimalist, modern aesthetic.

Real-time Visual Feedback: The interface provides instantaneous visual cues regarding microphone status, parsed intent, and updated list items.

🛠️ Technical Stack
Frontend:

Next.js (React)

Tailwind CSS (Liquid Glass UI styling)

Web Speech API

Backend:

FastAPI (Python)

GenAI / LLM API (for intent parsing)

Custom Regex/NLP Fallback Scripts

JSON-based Mock Database

⚙️ Local Setup & Installation
Prerequisites
Node.js (v18+)

Python (3.9+)

Git

Backend Setup (FastAPI)
Navigate to the backend directory:

Bash
cd backend
Create and activate a virtual environment:

Bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install dependencies:

Bash
pip install -r requirements.txt
Run the server:

Bash
uvicorn main:app --reload
Frontend Setup (Next.js)
Navigate to the frontend directory:

Bash
cd frontend
Install dependencies:

Bash
npm install
Start the development server:

Bash
npm run dev

👤 Author
Kirti Pratihar