---

## 📌 Project Julliana: An AI-Powered Mental Health Companion

### 🧠 Overview

**Project Julliana** is a conversational AI chatbot designed to provide mental health support, guidance, and resources. It uses **Natural Language Processing (NLP)** and **Machine Learning** to simulate empathetic conversations, helping users feel supported in times of stress, anxiety, or loneliness.

⚠️ *Disclaimer: Julliana is **not a substitute for professional medical advice**. In case of an emergency, please contact a licensed mental health professional or hotline in your region.*

---

### ✨ Features

* 🤖 AI-powered chatbot with NLP (trained on mental health–related data).
* 💬 User-friendly conversational interface via web app (Flask).
* 🔐 User authentication (register, login, profile management).
* 📊 Tracks user interactions for improved chatbot responses.
* 📚 Integration with local mental health resources and hotlines.

---

### 🛠️ Tech Stack

* **Frontend:** HTML, CSS, Bootstrap
* **Backend:** Python (Flask)
* **Database:** SQLite / MySQL
* **AI/ML:** TensorFlow, NLTK
* **Other:** Flask-Mail for email alerts

---

### 🚀 Installation & Setup

1. Clone the repo:

   ```bash
   git clone https://github.com/YOUR_USERNAME/Project-Julliana.git
   cd Project-Julliana
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate   # on Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables in `.env`:

   ```ini
   SECRET_KEY=your_secret_key
   SQLALCHEMY_DATABASE_URI=sqlite:///users.db
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_password
   ```

5. Initialize the database:

   ```bash
   flask shell
   >>> from ChatbotWebsite import db
   >>> db.create_all()
   >>> exit()
   ```

6. Run the app:

   ```bash
   python run.py
   ```

7. Open in browser: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

### 🌍 Mental Health Resources (Kenya)

* **Befrienders Kenya** – 0722 178 177 / [befrienderskenya.org](https://www.befrienderskenya.org/)
* **Chiromo Hospital Group Helpline** – 0709 901 000
* **Red Cross Kenya Helpline** – 1199
* **Amani Counselling Centre** – 0733 755 000
* **Mental 360** – [mental360.co](https://mental360.co/)

---

### 📖 License

This project is licensed under the MIT License.

---

