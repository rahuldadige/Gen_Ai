import tkinter as tk
from tkinter import messagebox, Frame, Text, Scrollbar
from PIL import Image, ImageTk
import chess
import chess.engine
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Adaptive Chess Bot")
        self.board = chess.Board()
        self.previous_move = None  # Store last move
        
        # Add AI feature flags
        self.show_commentary = tk.BooleanVar(value=False)
        self.show_suggestions = tk.BooleanVar(value=True)
        self.show_move_judgment = tk.BooleanVar(value=False)
        
        # Set Stockfish path
        self.STOCKFISH_PATH = r"C:\Users\RAhul\Downloads\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"
        
        # Track game history
        self.move_history = []  # Store all moves in the game
        self.position_history = []  # Store FEN positions after each move
        
        # Track wins for adaptive AI
        self.user_wins = 0
        self.ai_wins = 0
        self.consecutive_user_wins = 0
        self.consecutive_ai_wins = 0
        self.draws = 0
        
        # Track move quality for dynamic adjustment
        self.user_move_quality = []  # Store accuracy of recent moves
        self.recent_game_results = []  # Store recent game outcomes
        
        # Flag to control suggestion visibility (as BooleanVar)
        self.show_suggestions = tk.BooleanVar(value=True)

        # AI ELO rating for Stockfish (set to a minimum of 1320)
        self.ai_elo = 1320  # Default AI ELO (can be adjusted for difficulty)
        self.min_elo = 800   # Minimum difficulty
        self.max_elo = 3000  # Maximum difficulty

        # Initialize Gemini API
        self.initialize_gemini_api()

        # Define colors and dimensions to match the screenshot
        self.SQUARE_SIZE = 60
        self.LABEL_SIZE = 20
        self.BOARD_SIZE = self.SQUARE_SIZE * 8
        self.LIGHT_SQUARE = "#F0D9B5"  # Light beige
        self.DARK_SQUARE = "#B58863"   # Dark brown
        self.HIGHLIGHT_COLOR = "#FFFF00"  # Yellow highlight for selected square
        self.MOVE_HIGHLIGHT = "#A3D8F4"  # Light blue highlight for possible moves
        self.BG_COLOR = "#2C3E50"  # Dark blue-gray background
        
        # Configure the root window
        self.root.configure(bg=self.BG_COLOR)
        self.root.resizable(False, False)
        
        # Load images
        self.piece_images = {}
        self.load_images()
        
        # Create main frame with minimal padding to match screenshot
        main_frame = Frame(root, bg=self.BG_COLOR, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create board frame
        board_frame = Frame(main_frame, bg=self.BG_COLOR)
        board_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # Create chat frame
        chat_frame = Frame(main_frame, bg=self.BG_COLOR)
        chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create chat display
        self.chat_display = Text(chat_frame, wrap=tk.WORD, height=20, width=40, bg="#34495E", fg="white")
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Create chat input
        self.chat_input = Text(chat_frame, wrap=tk.WORD, height=3, width=40, bg="#34495E", fg="white")
        self.chat_input.pack(fill=tk.X, pady=(0, 5))
        
        # Create send button
        send_button = tk.Button(chat_frame, text="Send", command=self.send_message, bg="#3498DB", fg="white")
        send_button.pack(side=tk.RIGHT)
        
        # Create suggestion button
        suggestion_button = tk.Button(chat_frame, text="Get Suggestion", command=self.get_ai_suggestion, bg="#2ECC71", fg="white")
        suggestion_button.pack(side=tk.LEFT)
        
        # Chess canvas
        self.canvas = tk.Canvas(board_frame, width=self.BOARD_SIZE, height=self.BOARD_SIZE,
                               highlightthickness=0)
        self.canvas.pack()

        # Info panel layout that matches the screenshot
        info_frame = Frame(main_frame, bg=self.BG_COLOR, pady=10)
        info_frame.pack(fill=tk.X)
        
        # Initialize Stockfish engine
        self.initialize_stockfish()
        
        # User info (left side as in screenshot)
        self.user_label = tk.Label(info_frame, text=f"You (White): {self.user_wins} wins", 
                                  fg="white", bg=self.BG_COLOR, font=("Arial", 10))
        self.user_label.pack(side=tk.LEFT)
        
        # AI info (right side as in screenshot)
        self.ai_label = tk.Label(info_frame, text=f"AI (Black): {self.ai_wins} wins | ELO: {self.ai_elo}", 
                                fg="white", bg=self.BG_COLOR, font=("Arial", 10))
        self.ai_label.pack(side=tk.RIGHT)
        
        # Status label centered as in screenshot
        status_frame = Frame(main_frame, bg=self.BG_COLOR, pady=5)
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(status_frame, text="Game Status: White to move", fg="white", 
                                   bg=self.BG_COLOR, font=("Arial", 12, "bold"))
        self.status_label.pack()
        
        # Tips frame with label and toggle button
        tips_frame = Frame(main_frame, bg=self.BG_COLOR, pady=5)
        tips_frame.pack(fill=tk.X)
        
        # Create a header frame to contain the label and toggle button
        tips_header_frame = Frame(tips_frame, bg=self.BG_COLOR)
        tips_header_frame.pack(fill=tk.X)
        
        # Suggested Move label on the left
        tips_label = tk.Label(tips_header_frame, text="Suggested Move:", fg="white", 
                            bg=self.BG_COLOR, font=("Arial", 11), anchor=tk.W)
        tips_label.pack(side=tk.LEFT)
        
        # Add toggle button on the right
        self.toggle_var = tk.BooleanVar(value=False)  # Default to off
        self.toggle_button = tk.Checkbutton(tips_header_frame, text="Show", 
                                          variable=self.toggle_var, 
                                          command=self.toggle_suggestions,
                                          fg="white", bg=self.BG_COLOR, 
                                          selectcolor="#1A2638", 
                                          activebackground=self.BG_COLOR,
                                          activeforeground="white")
        self.toggle_button.pack(side=tk.RIGHT)
        
        # Monospaced textbox for move suggestions
        self.textbox = tk.Text(tips_frame, height=1, width=50, 
                              bg="#1A2638", fg="white", font=("Consolas", 10))
        self.textbox.pack(fill=tk.X)
        
        # Initially hide the suggestion text
        self.textbox.insert(tk.END, "Suggestions are turned off")

        # Create AI features frame (add this after the tips_frame)
        ai_features_frame = Frame(main_frame, bg=self.BG_COLOR, pady=5)
        ai_features_frame.pack(fill=tk.X)
        
        # Add checkboxes for AI features
        tk.Checkbutton(ai_features_frame, text="Live Commentary", 
                      variable=self.show_commentary,
                      command=self.toggle_commentary,
                      fg="white", bg=self.BG_COLOR,
                      selectcolor="#1A2638",
                      activebackground=self.BG_COLOR,
                      activeforeground="white").pack(side=tk.LEFT, padx=5)
                      
        tk.Checkbutton(ai_features_frame, text="Move Suggestions", 
                      variable=self.show_suggestions,
                      command=self.toggle_suggestions,
                      fg="white", bg=self.BG_COLOR,
                      selectcolor="#1A2638",
                      activebackground=self.BG_COLOR,
                      activeforeground="white").pack(side=tk.LEFT, padx=5)
                      
        tk.Checkbutton(ai_features_frame, text="Move Judgment", 
                      variable=self.show_move_judgment,
                      command=self.toggle_judgment,
                      fg="white", bg=self.BG_COLOR,
                      selectcolor="#1A2638",
                      activebackground=self.BG_COLOR,
                      activeforeground="white").pack(side=tk.LEFT, padx=5)

        # Add manual difficulty adjustment slider
        difficulty_frame = Frame(main_frame, bg=self.BG_COLOR, pady=5)
        difficulty_frame.pack(fill=tk.X)
        
        tk.Label(difficulty_frame, text="Manual ELO Adjustment:", 
                fg="white", bg=self.BG_COLOR, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        self.difficulty_slider = tk.Scale(difficulty_frame, from_=self.min_elo, to=self.max_elo,
                                         orient=tk.HORIZONTAL, bg=self.BG_COLOR, fg="white",
                                         highlightthickness=0, length=200,
                                         command=self.manual_difficulty_adjustment)
        self.difficulty_slider.set(self.ai_elo)
        self.difficulty_slider.pack(side=tk.LEFT, padx=5)
        
        tk.Label(difficulty_frame, text="(Overrides auto-adjustment)", 
                fg="#95A5A6", bg=self.BG_COLOR, font=("Arial", 8, "italic")).pack(side=tk.LEFT, padx=5)

        self.draw_board()

        # Bind mouse click event
        self.canvas.bind("<Button-1>", self.on_click)
        self.selected_square = None

    def initialize_gemini_api(self):
        """Initialize the Gemini API with proper configuration"""
        try:
            GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
            if not GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            print("Configuring Gemini API...")
            genai.configure(api_key=GOOGLE_API_KEY)
            
            # Get available models
            print("Checking available models...")
            for m in genai.list_models():
                print(f"Found model: {m.name}")
            
            print("Creating Gemini model...")
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Try different model versions in order of preference
            model_versions = [
                'gemini-2.5-flash',
                'gemini-2.5-pro',
                'gemini-2.0-flash',
                'gemini-2.0-flash-001',
                'gemini-flash-latest',
                'gemini-pro-latest'
            ]
            self.model = None
            last_error = None
            
            for model_name in model_versions:
                try:
                    print(f"Trying model: {model_name}")
                    self.model = genai.GenerativeModel(model_name=model_name,
                                                   generation_config=generation_config,
                                                   safety_settings=safety_settings)
                    print(f"✅ Configured {model_name}")
                    break
                except Exception as e:
                    print(f"Failed to initialize {model_name}: {str(e)}")
                    last_error = e
                    continue
            
            if self.model is None:
                raise Exception(f"Failed to initialize any model. Last error: {str(last_error)}")
            
            print("✅ Gemini API connection successful!")
        except Exception as e:
            error_msg = f"Error configuring Gemini API: {str(e)}"
            print(f"❌ {error_msg}")
            messagebox.showerror("Error", f"Failed to initialize AI model: {str(e)}")

    def toggle_suggestions(self):
        """Toggle the visibility of move suggestions."""
        if self.show_suggestions.get():
            self.show_best_move_tip()  # Show suggestion immediately when turned on
        else:
            self.textbox.delete(1.0, tk.END)
            self.textbox.insert(tk.END, "Suggestions are turned off")

    def load_images(self):
        """Loads chess piece images and resizes them."""
        pieces = {
            "p": "pawn", "n": "knight", "b": "bishop",
            "r": "rook", "q": "queen", "k": "king"
        }
        colors = {"b": "black", "w": "white"}

        for piece, name in pieces.items():
            for color, color_name in colors.items():
                path = f"images/{color_name}-{name}.png"
                try:
                    print(f"🔍 Loading {path}...")
                    img = Image.open(path).convert("RGBA")  
                    img = img.resize((int(self.SQUARE_SIZE * 0.9), int(self.SQUARE_SIZE * 0.9)), Image.LANCZOS)  # Resize
                    self.piece_images[f"{piece}{color}"] = ImageTk.PhotoImage(img)
                except Exception as e:
                    print(f"❌ Error loading {path}: {e}")

    def draw_board(self):
        """Draws the chess board and pieces."""
        self.canvas.delete("all")
        colors = [self.LIGHT_SQUARE, self.DARK_SQUARE]

        # Draw board squares
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                x1, y1 = col * self.SQUARE_SIZE, row * self.SQUARE_SIZE
                x2, y2 = x1 + self.SQUARE_SIZE, y1 + self.SQUARE_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                
                # Add small coordinate labels inside squares
                if row == 7:  # Bottom row (files a-h)
                    file_label = chr(97 + col)  # a-h
                    self.canvas.create_text(x1 + 8, y2 - 8, text=file_label, 
                                          fill="black" if color == self.LIGHT_SQUARE else "white",
                                          font=("Arial", 8), anchor=tk.SW)
                
                if col == 0:  # Leftmost column (ranks 1-8)
                    rank_label = str(8 - row)  # 8-1
                    self.canvas.create_text(x1 + 8, y1 + 8, text=rank_label,
                                          fill="black" if color == self.LIGHT_SQUARE else "white", 
                                          font=("Arial", 8), anchor=tk.NW)

        # Highlight previous move as in screenshot (light blue squares)
        if self.previous_move:
            from_square = self.previous_move.from_square
            to_square = self.previous_move.to_square
            
            from_col, from_row = chess.square_file(from_square), 7 - chess.square_rank(from_square)
            to_col, to_row = chess.square_file(to_square), 7 - chess.square_rank(to_square)
            
            # Highlight previous move squares with a semi-transparent overlay
            self.canvas.create_rectangle(
                from_col * self.SQUARE_SIZE, from_row * self.SQUARE_SIZE,
                (from_col+1) * self.SQUARE_SIZE, (from_row+1) * self.SQUARE_SIZE,
                fill="#A3D8F4", stipple="gray50"
            )
            
            self.canvas.create_rectangle(
                to_col * self.SQUARE_SIZE, to_row * self.SQUARE_SIZE,
                (to_col+1) * self.SQUARE_SIZE, (to_row+1) * self.SQUARE_SIZE,
                fill="#A3D8F4", stipple="gray50"
            )

        # Draw pieces
        for square, piece in self.board.piece_map().items():
            row, col = divmod(square, 8)
            piece_key = f"{piece.symbol().lower()}{'b' if piece.color else 'w'}"
            if piece_key in self.piece_images:
                self.canvas.create_image(
                    col * self.SQUARE_SIZE + self.SQUARE_SIZE//2, 
                    (7 - row) * self.SQUARE_SIZE + self.SQUARE_SIZE//2, 
                    image=self.piece_images[piece_key]
                )

        # Update status based on current game state
        turn_color = "White" if self.board.turn == chess.WHITE else "Black"
        status = f"Game Status: {turn_color} to move"
        
        if self.board.is_check():
            status += " (CHECK)"
        
        self.status_label.config(text=status)
        
        # Update win counters
        self.user_label.config(text=f"You (White): {self.user_wins} wins")
        self.ai_label.config(text=f"AI (Black): {self.ai_wins} wins | ELO: {self.ai_elo}")

    def on_click(self, event):
        """Handles piece selection and movement."""
        col = event.x // self.SQUARE_SIZE
        row = event.y // self.SQUARE_SIZE
        square = chess.square(col, 7 - row)

        piece = self.board.piece_at(square)

        if self.selected_square is None:
            # Select a piece if it's the player's turn
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                print(f"🔵 Selected {chess.square_name(square)}")
                self.highlight_moves(square)
            else:
                print("❌ Not your piece!")
        else:
            # Check if clicking the same square (deselect)
            if self.selected_square == square:
                self.selected_square = None
                self.draw_board()
                return
                
            # Move the selected piece if it's a valid move
            move = chess.Move(self.selected_square, square)
            
            # Check for promotion
            if self.is_pawn_promotion(move):
                move = self.handle_promotion(move)
                if not move:  # User canceled promotion
                    self.selected_square = None
                    self.draw_board()
                    return
            
            if move in self.board.legal_moves:
                print(f"✅ Moving {chess.square_name(self.selected_square)} → {chess.square_name(square)}")
                
                # Store previous move before making new one
                self.previous_move = move

                self.board.push(move)
                self.selected_square = None  # Reset selection
                self.draw_board()
                
                # Evaluate the move and adjust AI difficulty immediately
                move_quality = self.evaluate_move_quality(move)
                if move_quality is not None:
                    self.adjust_ai_difficulty_dynamic(move_quality)
                
                # Add AI features after move
                if self.show_commentary.get():
                    self.get_game_commentary()
                if self.show_move_judgment.get():
                    self.judge_last_move()
                if self.show_suggestions.get():
                    self.show_best_move_tip()
                    
                self.root.after(500, self.ai_move)
                
                # After a successful move, update game history
                self.update_game_history(move)
            else:
                print("❌ Invalid move!")
                self.selected_square = None  # Reset selection
                self.draw_board()

    def is_pawn_promotion(self, move):
        """Check if move is a pawn promotion."""
        piece = self.board.piece_at(move.from_square)
        if not piece or piece.piece_type != chess.PAWN:
            return False
            
        # Check if pawn is moving to the last rank
        if (self.board.turn == chess.WHITE and chess.square_rank(move.to_square) == 7) or \
           (self.board.turn == chess.BLACK and chess.square_rank(move.to_square) == 0):
            return True
        return False
    
    def handle_promotion(self, move):
        """Handle pawn promotion with a dialog."""
        promotion_window = tk.Toplevel(self.root)
        promotion_window.title("Promote Pawn")
        promotion_window.resizable(False, False)
        promotion_window.transient(self.root)
        promotion_window.grab_set()
        promotion_window.configure(bg=self.BG_COLOR)
        
        # Center the window
        x = self.root.winfo_x() + self.root.winfo_width()//2 - 150
        y = self.root.winfo_y() + self.root.winfo_height()//2 - 100
        promotion_window.geometry(f"300x120+{x}+{y}")
        
        tk.Label(promotion_window, text="Choose piece for promotion:", 
                font=("Arial", 12), bg=self.BG_COLOR, fg="white").pack(pady=10)
        
        promotion_piece = tk.StringVar(value="q")  # Default to queen
        
        frame = Frame(promotion_window, bg=self.BG_COLOR)
        frame.pack(fill=tk.X, padx=10)
        
        pieces = [("Queen", "q"), ("Rook", "r"), ("Bishop", "b"), ("Knight", "n")]
        for text, value in pieces:
            rb = tk.Radiobutton(frame, text=text, value=value, variable=promotion_piece,
                              bg=self.BG_COLOR, fg="white", selectcolor="black",
                              activebackground=self.BG_COLOR, activeforeground="white")
            rb.pack(side=tk.LEFT, expand=True)
        
        result = [None]  # Use list to store result across closures
        
        def on_ok():
            result[0] = chess.Move(move.from_square, move.to_square, promotion=chess.Piece.from_symbol(promotion_piece.get()).piece_type)
            promotion_window.destroy()
            
        def on_cancel():
            result[0] = None
            promotion_window.destroy()
        
        button_frame = Frame(promotion_window, bg=self.BG_COLOR)
        button_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(button_frame, text="OK", command=on_ok, width=10,
                bg="#3498DB", fg="white").pack(side=tk.LEFT, padx=10, expand=True)
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=10,
                bg="#E74C3C", fg="white").pack(side=tk.RIGHT, padx=10, expand=True)
        
        # Wait for the window to close
        self.root.wait_window(promotion_window)
        return result[0]

    def highlight_moves(self, square):
        """Highlights possible moves with light blue dots."""
        self.draw_board()

        # Highlight the selected square
        col, row = chess.square_file(square), 7 - chess.square_rank(square)
        self.canvas.create_rectangle(
            col * self.SQUARE_SIZE, row * self.SQUARE_SIZE,
            (col+1) * self.SQUARE_SIZE, (row+1) * self.SQUARE_SIZE,
            outline="#FFFF00", width=3
        )

        # Get all legal moves for this piece
        for move in self.board.legal_moves:
            if move.from_square == square:
                to_square = move.to_square
                to_col, to_row = chess.square_file(to_square), 7 - chess.square_rank(to_square)

                # If there's a piece at destination, highlight the square
                if self.board.piece_at(to_square):
                    self.canvas.create_rectangle(
                        to_col * self.SQUARE_SIZE, to_row * self.SQUARE_SIZE,
                        (to_col+1) * self.SQUARE_SIZE, (to_row+1) * self.SQUARE_SIZE,
                        outline=self.MOVE_HIGHLIGHT, width=3
                    )
                else:
                    # Draw a small dot for valid moves, matching screenshot color
                    x, y = to_col * self.SQUARE_SIZE + self.SQUARE_SIZE//2, to_row * self.SQUARE_SIZE + self.SQUARE_SIZE//2
                    self.canvas.create_oval(x-8, y-8, x+8, y+8, fill=self.MOVE_HIGHLIGHT, outline="")

    def ai_move(self):
        """AI makes a move using Stockfish with ELO scaling."""
        if not self.board.is_game_over():
            if not self.engine:
                try:
                    # Try to reinitialize the engine if it's not available
                    self.initialize_stockfish()
                except Exception as e:
                    print("❌ Could not initialize Stockfish:", e)
                    return

            try:
                # Configure engine with safety checks
                try:
                    self.engine.configure({"UCI_LimitStrength": True})
                    self.engine.configure({"UCI_Elo": self.ai_elo})
                except Exception as config_error:
                    print("⚠️ Could not configure engine strength, using default settings")
                    
                # AI makes a move with timeout protection
                result = self.engine.play(self.board, chess.engine.Limit(time=1))
                if result.move:
                    self.previous_move = result.move  # Store the AI's move
                    self.board.push(result.move)
                    self.draw_board()
                    
                    # Add AI features after AI move
                    if hasattr(self, 'show_commentary') and isinstance(self.show_commentary, tk.BooleanVar) and self.show_commentary.get():
                        self.get_game_commentary()
                    if hasattr(self, 'show_move_judgment') and isinstance(self.show_move_judgment, tk.BooleanVar) and self.show_move_judgment.get():
                        self.judge_last_move()
                    if hasattr(self, 'show_suggestions') and isinstance(self.show_suggestions, tk.BooleanVar) and self.show_suggestions.get():
                        self.show_best_move_tip()
                        
                    self.check_game_status()
                    
                    # After AI makes a move, update game history
                    self.update_game_history(result.move)
                else:
                    print("⚠️ AI did not return a move")

            except chess.engine.EngineTerminatedError:
                print("❌ Engine terminated, attempting to restart...")
                try:
                    self.initialize_stockfish()
                except Exception as e:
                    print("❌ Could not restart engine:", e)
                
            except Exception as e:
                print("❌ Error during AI move:", e)
                messagebox.showerror("Error", "An error occurred with the AI engine. The game will continue without AI moves.")
                try:
                    if self.engine:
                        self.engine.quit()
                except Exception:
                    pass  # Ignore errors during cleanup

    def show_best_move_tip(self):
        """Displays the best move suggestion for the human player."""
        try:
            print("Attempting to show best move tip...")
            print(f"Suggestions enabled: {self.show_suggestions.get()}")
            
            if not self.show_suggestions.get():
                print("Suggestions are turned off")
                return
            
            print("Getting best move...")
            best_move = self.get_best_human_move()
            if best_move == chess.Move.null():
                print("No valid move found")
                return
            
            print(f"Best move found: {best_move}")
            
            from_square = chess.square_name(best_move.from_square)
            to_square = chess.square_name(best_move.to_square)
            
            # Get the piece type
            piece = self.board.piece_at(best_move.from_square)
            if piece:
                piece_name = "Pawn" if piece.piece_type == chess.PAWN else chess.piece_name(piece.piece_type).capitalize()
                
                # Format exactly as in the screenshot
                move_text = f"Best move: {piece_name} from {from_square} to {to_square}"
                
                # Clear and update textbox
                self.textbox.delete(1.0, tk.END)
                self.textbox.insert(tk.END, move_text)
        except Exception as e:
            print(f"⚠️ Error showing best move tip: {e}")
            return

    def get_best_human_move(self):
        """Uses Stockfish to analyze and return the best move for the human player."""
        try:
            if self.engine and not self.board.is_game_over():
                # Analyze the current position for the best human move
                result = self.engine.play(self.board, chess.engine.Limit(time=1))
                return result.move if result and result.move else chess.Move.null()
            return chess.Move.null()
        except Exception as e:
            print(f"⚠️ Error analyzing position: {e}")
            return chess.Move.null()

    def check_game_status(self):
        """Check if the game is over and update win counts."""
        if self.board.is_checkmate():
            if self.board.turn == chess.WHITE:  # AI wins
                self.ai_wins += 1
                self.consecutive_ai_wins += 1
                self.consecutive_user_wins = 0
                self.recent_game_results.append('ai_win')
                winner = "AI (Black)"
            else:  # User wins
                self.user_wins += 1
                self.consecutive_user_wins += 1
                self.consecutive_ai_wins = 0
                self.recent_game_results.append('user_win')
                winner = "You (White)"

            # Keep only last 10 game results
            if len(self.recent_game_results) > 10:
                self.recent_game_results.pop(0)

            # Update labels immediately
            self.user_label.config(text=f"You (White): {self.user_wins} wins")
            self.ai_label.config(text=f"AI (Black): {self.ai_wins} wins | ELO: {self.ai_elo}")
            
            messagebox.showinfo("Game Over", f"Checkmate! {winner} wins.")
            self.reset_game()

        elif self.board.is_stalemate():
            messagebox.showinfo("Game Over", "Stalemate! It's a draw.")
            self.draws += 1
            self.recent_game_results.append('draw')
            if len(self.recent_game_results) > 10:
                self.recent_game_results.pop(0)
        elif self.board.is_insufficient_material():
            messagebox.showinfo("Game Over", "Insufficient material! It's a draw.")
            self.draws += 1
        elif self.board.is_fifty_moves():
            messagebox.showinfo("Game Over", "Fifty-move rule! It's a draw.")
            self.draws += 1
        elif self.board.is_repetition():
            messagebox.showinfo("Game Over", "Threefold repetition! It's a draw.")
            self.draws += 1

    def evaluate_move_quality(self, move):
        """Evaluate the quality of user's move compared to best move."""
        try:
            if not self.engine:
                return None

            quality = 0.5
            
            # Create a board position BEFORE the move
            temp_board = self.board.copy()
            temp_board.pop()  # Undo the move that was just made
            
            # Get the best move for this position
            result = self.engine.play(temp_board, chess.engine.Limit(time=0.3))
            best_move = result.move
            
            # Compare user move with best move
            if move == best_move:
                quality = 1.0
                self.user_move_quality.append(quality)  # Perfect move
                print("⭐ Perfect move!")
            else:
                # Evaluate position after best move
                temp_board.push(best_move)
                best_eval = self.engine.analyse(temp_board, chess.engine.Limit(time=0.2))
                temp_board.pop()
                
                # Evaluate position after user move
                temp_board.push(move)
                user_eval = self.engine.analyse(temp_board, chess.engine.Limit(time=0.2))
                
                # Calculate quality (0.0 to 1.0)
                try:
                    best_score = best_eval.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE)).relative.score(mate_score=10000) or 0
                    user_score = user_eval.get('score', chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE)).relative.score(mate_score=10000) or 0
                    diff = abs(best_score - user_score)
                    quality = max(0.0, 1.0 - (diff / 300.0))  # Normalize difference
                    self.user_move_quality.append(quality)
                    
                    if quality >= 0.8:
                        print(f"✅ Excellent move quality: {quality:.1%}")
                    elif quality >= 0.5:
                        print(f"👍 Good move quality: {quality:.1%}")
                    else:
                        print(f"⚠️ Move quality: {quality:.1%}")
                except:
                    self.user_move_quality.append(0.5)  # Neutral if can't evaluate
            
            # Keep only last 20 moves
            if len(self.user_move_quality) > 20:
                self.user_move_quality.pop(0)

            return quality
                
        except Exception as e:
            print(f"⚠️ Could not evaluate move quality: {e}")
            # Don't crash, just skip this evaluation
            return None

    def adjust_ai_difficulty_dynamic(self, move_quality=None):
        """Adjust AI difficulty immediately after each move."""
        if move_quality is None:
            if not self.user_move_quality:
                return
            recent_quality = self.user_move_quality[-1]
        else:
            recent_quality = move_quality

        if len(self.user_move_quality) >= 3:
            recent_quality = sum(self.user_move_quality[-3:]) / min(3, len(self.user_move_quality))

        old_elo = self.ai_elo

        # Adjust based on the latest move quality, with a small rolling average
        if recent_quality >= 0.90:
            delta = 15
            print(f"⭐ Strong move detected ({recent_quality:.1%}); increasing difficulty")
        elif recent_quality >= 0.75:
            delta = 10
            print(f"✅ Good move detected ({recent_quality:.1%}); nudging difficulty up")
        elif recent_quality >= 0.55:
            delta = 0
            print(f"➖ Neutral move detected ({recent_quality:.1%}); keeping difficulty steady")
        elif recent_quality >= 0.40:
            delta = -10
            print(f"⚠️ Weak move detected ({recent_quality:.1%}); easing difficulty")
        else:
            delta = -20
            print(f"📉 Very weak move detected ({recent_quality:.1%}); easing difficulty more")

        self.ai_elo = max(self.min_elo, min(self.max_elo, self.ai_elo + delta))
        
        # Ensure ELO stays within bounds
        self.ai_elo = max(self.min_elo, min(self.max_elo, self.ai_elo))
        
        if old_elo != self.ai_elo:
            print(f"🎯 AI ELO adjusted: {old_elo} → {self.ai_elo}")
            
            try:
                self.ai_label.config(text=f"AI (Black): {self.ai_wins} wins | ELO: {self.ai_elo}")
                
                # Show notification to user if chat display exists
                if hasattr(self, 'chat_display') and self.chat_display:
                    if self.ai_elo > old_elo:
                        self.chat_display.insert(tk.END, f"\n🔼 AI difficulty increased to ELO {self.ai_elo}\n")
                    else:
                        self.chat_display.insert(tk.END, f"\n🔽 AI difficulty decreased to ELO {self.ai_elo}\n")
                    self.chat_display.see(tk.END)
            except Exception as e:
                print(f"⚠️ Could not update UI: {e}")

    def reset_game(self):
        """Reset the game after checkmate or draw."""
        self.board.reset()
        self.selected_square = None
        self.previous_move = None
        self.draw_board()
        
        self.status_label.config(text="Game Status: White to move")
        
        # Clear the textbox
        self.textbox.delete(1.0, tk.END)
        
        # Only show suggestions if they're turned on
        if self.show_suggestions.get():
            self.show_best_move_tip()
        else:
            self.textbox.insert(tk.END, "Suggestions are turned off")

    def close_engine(self):
        """Safely close the Stockfish engine."""
        try:
            if self.engine:
                self.engine.quit()
                print("🔻 Closing engine...")
        except Exception as e:
            print("❌ Error closing Stockfish engine:", e)

    def on_close(self):
        """Handles closing the application."""
        self.close_engine()
        self.root.destroy()

    def update_game_history(self, move):
        """Update the game history after each move"""
        self.move_history.append(str(move))
        self.position_history.append(self.board.fen())

    def get_game_context(self):
        """Get formatted game context for Gemini API"""
        context = "Game History:\n"
        for i, (move, position) in enumerate(zip(self.move_history, self.position_history)):
            turn = "White" if i % 2 == 0 else "Black"
            context += f"Move {i+1}. {turn}: {move} (Position: {position})\n"
        context += f"\nCurrent Position: {self.board.fen()}\n"
        context += f"Current Turn: {'White' if self.board.turn else 'Black'}"
        return context

    def get_ai_suggestion(self):
        """Get a suggested move from Gemini AI with full game context"""
        try:
            # Create a prompt with full game context
            context = self.get_game_context()
            prompt = f"""As a chess expert, analyze this position briefly:

{context}

Provide only:
1. Best move in standard notation (e.g., e2e4)
2. One sentence explanation why this move is good.
Be concise."""
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            
            # Check if response was blocked
            if not response.candidates or not response.candidates[0].content.parts:
                print(f"⚠️ Response blocked. Reason: {response.candidates[0].finish_reason if response.candidates else 'Unknown'}")
                self.chat_display.insert(tk.END, "\n⚠️ AI suggestion unavailable (response filtered)\n")
                self.chat_display.see(tk.END)
                return
            
            suggestion = response.text
            
            # Display the suggestion in the chat
            self.chat_display.insert(tk.END, f"\n💡 AI Suggestion: {suggestion}\n")
            self.chat_display.see(tk.END)
            
        except Exception as e:
            print(f"⚠️ Could not get AI suggestion: {e}")
            messagebox.showerror("Error", f"Failed to get AI suggestion: {str(e)}")
    
    def send_message(self):
        """Send a message to the AI and get a response with full game context"""
        try:
            # Get the message from the input
            message = self.chat_input.get("1.0", tk.END).strip()
            if not message:
                return
                
            # Display user message
            self.chat_display.insert(tk.END, f"\nYou: {message}\n")
            self.chat_input.delete("1.0", tk.END)
            
            # Create a prompt with full game context
            context = self.get_game_context()
            prompt = f"""You are a chess assistant. Current game state:

{context}

User: {message}

Provide a brief, direct response in 1-2 sentences."""
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            
            # Check if response was blocked
            if not response.candidates or not response.candidates[0].content.parts:
                finish_reason = response.candidates[0].finish_reason if response.candidates else 'Unknown'
                self.chat_display.insert(tk.END, f"\n⚠️ Response unavailable (filtered: {finish_reason})\n")
                self.chat_display.see(tk.END)
                return
            
            ai_response = response.text
            
            # Display AI response
            self.chat_display.insert(tk.END, f"\n🤖 AI: {ai_response}\n")
            self.chat_display.see(tk.END)
            
        except Exception as e:
            print(f"⚠️ Chat error: {e}")
            self.chat_display.insert(tk.END, f"\n⚠️ Error: Could not get response\n")
            self.chat_display.see(tk.END)

    def initialize_stockfish(self):
        """Initialize the Stockfish chess engine"""
        try:
            print(f"Loading Stockfish from: {self.STOCKFISH_PATH}")
            if not os.path.exists(self.STOCKFISH_PATH):
                raise FileNotFoundError(f"Stockfish executable not found at: {self.STOCKFISH_PATH}")
            
            # Try to initialize the engine with a timeout
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.STOCKFISH_PATH, timeout=5.0)
                # Test the engine with a simple command
                self.engine.ping()
                print("✅ Stockfish engine loaded successfully!")
            except Exception as engine_error:
                raise Exception(f"Engine initialization failed: {str(engine_error)}")
                
        except Exception as e:
            print(f"❌ Error loading Stockfish: {str(e)}")
            messagebox.showerror("Error", f"Stockfish engine could not be loaded: {str(e)}\nPlease verify the path: {self.STOCKFISH_PATH}")
            self.engine = None

    def toggle_commentary(self):
        """Toggle live game commentary"""
        if self.show_commentary.get():
            self.get_game_commentary()
        else:
            self.chat_display.insert(tk.END, "\nCommentary turned off\n")
            self.chat_display.see(tk.END)

    def toggle_judgment(self):
        """Toggle move judgment"""
        if self.show_move_judgment.get():
            self.judge_last_move()
        else:
            self.chat_display.insert(tk.END, "\nMove judgment turned off\n")
            self.chat_display.see(tk.END)

    def manual_difficulty_adjustment(self, value):
        """Manually adjust AI difficulty via slider"""
        try:
            self.ai_elo = int(float(value))
            self.ai_label.config(text=f"AI (Black): {self.ai_wins} wins | ELO: {self.ai_elo}")
            print(f"🎚️ Manual ELO adjustment: {self.ai_elo}")
        except Exception as e:
            print(f"⚠️ Error adjusting difficulty: {e}")

    def get_game_commentary(self):
        """Get real-time commentary about the current game state"""
        try:
            if not hasattr(self, 'model') or not self.model:
                print("⚠️ Gemini model not initialized")
                return
                
            context = self.get_game_context()
            prompt = f"""You are a chess commentator. Provide brief commentary on this game:

{context}

Provide 2-3 sentences about the current position, tactics, or strategy."""
            
            response = self.model.generate_content(prompt)
            
            # Check if response was blocked
            if not response.candidates or not response.candidates[0].content.parts:
                print(f"⚠️ Response blocked. Reason: {response.candidates[0].finish_reason if response.candidates else 'Unknown'}")
                if hasattr(self, 'chat_display') and self.chat_display:
                    self.chat_display.insert(tk.END, "\n⚠️ Commentary unavailable (response filtered)\n")
                    self.chat_display.see(tk.END)
                return
            
            commentary = response.text
            
            if hasattr(self, 'chat_display') and self.chat_display:
                self.chat_display.insert(tk.END, f"\n💬 Commentary: {commentary}\n")
                self.chat_display.see(tk.END)
            
        except Exception as e:
            print(f"⚠️ Could not generate commentary: {e}")
            if hasattr(self, 'chat_display') and self.chat_display:
                self.chat_display.insert(tk.END, "\n⚠️ Commentary error\n")
                self.chat_display.see(tk.END)

    def judge_last_move(self):
        """Judge the last move made in the game"""
        try:
            if not self.previous_move:
                return
            
            if not hasattr(self, 'model') or not self.model:
                print("⚠️ Gemini model not initialized")
                return
                
            context = self.get_game_context()
            prompt = f"""Evaluate this chess move:

Game context: {context}
Last move: {self.previous_move}

Rate the move (Excellent/Good/Questionable/Poor) and explain in one sentence."""
            
            response = self.model.generate_content(prompt)
            
            # Check if response was blocked
            if not response.candidates or not response.candidates[0].content.parts:
                print(f"⚠️ Response blocked. Reason: {response.candidates[0].finish_reason if response.candidates else 'Unknown'}")
                if hasattr(self, 'chat_display') and self.chat_display:
                    self.chat_display.insert(tk.END, "\n⚠️ Move judgment unavailable\n")
                    self.chat_display.see(tk.END)
                return
            
            judgment = response.text
            
            if hasattr(self, 'chat_display') and self.chat_display:
                self.chat_display.insert(tk.END, f"\n⚖️ Move Judgment: {judgment}\n")
                self.chat_display.see(tk.END)
            
        except Exception as e:
            print(f"⚠️ Could not judge move: {e}")
            if hasattr(self, 'chat_display') and self.chat_display:
                self.chat_display.insert(tk.END, "\n⚠️ Judgment error\n")
                self.chat_display.see(tk.END)

if __name__ == "__main__":
    print("Starting chess application...")
    try:
        print("Initializing Tkinter...")
        root = tk.Tk()
        print("Configuring root window...")
        root.configure(bg="#2C3E50")
        print("Creating ChessGUI instance...")
        gui = ChessGUI(root)
        
        # Bind the window close button (cross) to our custom on_close method
        print("Setting up window close handler...")
        root.protocol("WM_DELETE_WINDOW", gui.on_close)
        
        print("Starting main loop...")
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        import traceback
        traceback.print_exc()
