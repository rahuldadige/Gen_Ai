# Adaptive Chess Bot with AI Commentary

Play chess with an opponent that doesn’t just *move* — it adapts, comments, and guides. This project combines the power of **Stockfish** (for world-class chess moves) and **Google Gemini** (for natural AI interaction) to create an engaging, human-like chess experience.

---

## ✨ Features

* 🎮 **Interactive Chess GUI** – Built with Tkinter and custom piece sprites.
* ♟️ **Adaptive Difficulty** – AI strength scales up or down depending on how well you play.
* 🧠 **Smart Suggestions** – Get real-time move recommendations from Gemini.
* 🎙️ **AI Commentary** – Understand *why* a move was good or bad.
* ✅ **Move Judgment** – Instantly see whether your move was strong, weak, or risky.
* 📜 **Game History** – Track all moves and board states.
* 🔄 **Pawn Promotion Dialog** – Choose how to promote pawns.
* 🌙 **User Toggles** – Turn commentary, suggestions, or judgment on/off anytime.
* 💬 **In-App Chat** – Talk to the Gemini assistant directly.

---

## 🛠️ Tech Stack

* **Frontend/GUI:** Tkinter, Pillow
* **Game Logic:** python-chess
* **Chess Engine:** Stockfish
* **AI Assistant:** Google Gemini API
* **Language:** Python 3.x

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/rahuldadige/Gen_Ai.git
cd Gen_Ai
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Get Stockfish

* Download Stockfish from: [https://stockfishchess.org/download/](https://stockfishchess.org/download/)
* Update the `STOCKFISH_PATH` in `app.py` to point to your Stockfish binary.

### 4. Set Up Gemini API

Create a `.env` file with:

```env
GOOGLE_API_KEY=your_api_key_here
```

### 5. Run the App

```bash
python app.py
```

---

## 🎮 How to Use

* Click pieces to see legal moves (dots appear on valid squares).
* Play your move → AI responds.
* Use buttons to toggle **Suggestions**, **Commentary**, or **Move Judgment**.
* Chat with Gemini anytime in the side panel.
* Experience AI that *learns* your skill level: win more → it plays stronger, lose more → it eases up.

---

## 🐞 Troubleshooting

* **Stockfish not found?** Double-check the `STOCKFISH_PATH`.
* **Gemini errors?** Ensure your API key is valid and `.env` is set up.
* **Missing images?** Verify the `images/` folder is present and paths are correct.

---

## 🌱 Roadmap

* Add online multiplayer.
* Include voice-based commentary.
* Store match history with analytics.
* Deploy as a web app.

---

## 🙌 Acknowledgments

* [python-chess](https://python-chess.readthedocs.io/)
* [Stockfish](https://stockfishchess.org/)
* [Google Gemini](https://ai.google/)

---

## 📜 License

MIT License (feel free to adapt and build upon this work).
