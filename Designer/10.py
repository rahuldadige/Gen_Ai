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
        
        # Flag to control suggestion visibility
        self.show_suggestions = True

        # AI ELO rating for Stockfish (set to a minimum of 1320)
        self.ai_elo = 1320  # Default AI ELO (can be adjusted for difficulty)

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
        self.ai_label = tk.Label(info_frame, text=f"AI (Black): {self.ai_wins} wins", 
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
                "temperature": 0.9,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 2048,
            }
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Try different model versions in order of preference
            model_versions = ['gemini-1.5-pro', 'gemini-1.5-pro-latest', 'gemini-pro']
            self.model = None
            last_error = None
            
            for model_name in model_versions:
                try:
                    print(f"Trying model: {model_name}")
                    self.model = genai.GenerativeModel(model_name=model_name,
                                                   generation_config=generation_config,
                                                   safety_settings=safety_settings)
                    # Test the model
                    response = self.model.generate_content('Test connection')
                    print(f"Successfully connected to {model_name}")
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
        self.ai_label.config(text=f"AI (Black): {self.ai_wins} wins")

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
        if not self.board.is_game_over() and self.engine:
            try:
                self.engine.configure({"UCI_LimitStrength": True})
                self.engine.configure({"UCI_Elo": self.ai_elo})

                # AI makes a move
                result = self.engine.play(self.board, chess.engine.Limit(time=1))
                self.previous_move = result.move  # Store the AI's move
                self.board.push(result.move)
                self.draw_board()
                
                # Add AI features after AI move
                if self.show_commentary.get():
                    self.get_game_commentary()
                if self.show_move_judgment.get():
                    self.judge_last_move()
                if self.show_suggestions.get():
                    self.show_best_move_tip()
                    
                self.check_game_status()
                
                # After AI makes a move, update game history
                self.update_game_history(result.move)

            except Exception as e:
                print("❌ Error during AI move:", e)
                messagebox.showerror("Error", "An error occurred with the AI engine.")
                self.engine.quit()  # Quit the engine if an error occurs

    def show_best_move_tip(self):
        """Displays the best move suggestion for the human player."""
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
            
            self.textbox.insert(tk.END, move_text)

    def get_best_human_move(self):
        """Uses Stockfish to analyze and return the best move for the human player."""
        if self.engine and not self.board.is_game_over():
            try:
                # Analyze the current position for the best human move
                result = self.engine.play(self.board, chess.engine.Limit(time=1))
                return result.move
            except Exception as e:
                print("❌ Error analyzing the position:", e)
                return chess.Move.null()
        return chess.Move.null()

    def check_game_status(self):
        """Check if the game is over and update win counts."""
        if self.board.is_checkmate():
            if self.board.turn == chess.WHITE:  # AI wins
                self.ai_wins += 1
                winner = "AI (Black)"
            else:  # User wins
                self.user_wins += 1
                winner = "You (White)"

            # Update labels immediately
            self.user_label.config(text=f"You (White): {self.user_wins} wins")
            self.ai_label.config(text=f"AI (Black): {self.ai_wins} wins")
            
            messagebox.showinfo("Game Over", f"Checkmate! {winner} wins.")
            
            # Adjust AI difficulty based on results
            self.adjust_ai_difficulty()

        elif self.board.is_stalemate():
            messagebox.showinfo("Game Over", "Stalemate! It's a draw.")
        elif self.board.is_insufficient_material():
            messagebox.showinfo("Game Over", "Insufficient material! It's a draw.")
        elif self.board.is_fifty_moves():
            messagebox.showinfo("Game Over", "Fifty-move rule! It's a draw.")
        elif self.board.is_repetition():
            messagebox.showinfo("Game Over", "Threefold repetition! It's a draw.")

    def adjust_ai_difficulty(self):
        """Adjust AI difficulty based on game results."""
        # If player is winning too much, increase AI difficulty
        if self.user_wins > self.ai_wins + 2:
            self.ai_elo = min(3000, self.ai_elo + 100)
            print(f"🔼 Increasing AI difficulty to ELO {self.ai_elo}")
        # If AI is winning too much, decrease difficulty
        elif self.ai_wins > self.user_wins + 2:
            self.ai_elo = max(1320, self.ai_elo - 100)
            print(f"🔽 Decreasing AI difficulty to ELO {self.ai_elo}")

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
            suggestion = response.text
            
            # Display the suggestion in the chat
            self.chat_display.insert(tk.END, f"\nAI Suggestion: {suggestion}\n")
            self.chat_display.see(tk.END)
            
        except Exception as e:
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
            ai_response = response.text
            
            # Display AI response
            self.chat_display.insert(tk.END, f"\nAI: {ai_response}\n")
            self.chat_display.see(tk.END)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {str(e)}")

    def initialize_stockfish(self):
        """Initialize the Stockfish chess engine"""
        try:
            print(f"Loading Stockfish from: {self.STOCKFISH_PATH}")
            if not os.path.exists(self.STOCKFISH_PATH):
                raise FileNotFoundError(f"Stockfish executable not found at: {self.STOCKFISH_PATH}")
            
            self.engine = chess.engine.SimpleEngine.popen_uci(self.STOCKFISH_PATH)
            print("✅ Stockfish engine loaded successfully!")
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

    def get_game_commentary(self):
        """Get real-time commentary about the current game state"""
        try:
            context = self.get_game_context()
            prompt = f"""As a chess commentator, provide a brief, engaging commentary about the current game state:

{context}

Focus on:
1. Current position evaluation
2. Key tactical or strategic elements
3. Potential threats or opportunities
Keep it concise and engaging."""
            
            response = self.model.generate_content(prompt)
            commentary = response.text
            
            self.chat_display.insert(tk.END, f"\nCommentary: {commentary}\n")
            self.chat_display.see(tk.END)
            
        except Exception as e:
            print(f"Error getting commentary: {e}")

    def judge_last_move(self):
        """Judge the last move made in the game"""
        try:
            if not self.previous_move:
                return
                
            context = self.get_game_context()
            prompt = f"""As a chess expert, evaluate the last move made in this game:

{context}

Last move: {self.previous_move}

Provide a brief evaluation:
1. Is it a good move? (Excellent/Good/Questionable/Poor)
2. One sentence explanation why
Keep it concise."""
            
            response = self.model.generate_content(prompt)
            judgment = response.text
            
            self.chat_display.insert(tk.END, f"\nMove Judgment: {judgment}\n")
            self.chat_display.see(tk.END)
            
        except Exception as e:
            print(f"Error judging move: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="#2C3E50")
    gui = ChessGUI(root)
    
    # Bind the window close button (cross) to our custom on_close method
    root.protocol("WM_DELETE_WINDOW", gui.on_close)
    
    root.mainloop()
