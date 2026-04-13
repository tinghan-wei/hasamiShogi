# visualize.py
# Real-time Hasami Shogi visualizer using Pygame.

import pygame
import time
import pickle
import copy
from hasamiShogi import HasamiShogi, BLACK, WHITE, EMPTY

CELL_SIZE = 60       # pixels per square
DELAY = 0.5          # seconds between moves
MARGIN = 40          # margin for coordinates

# colors
BG_COLOR = (200, 200, 200)
GRID_COLOR = (0, 0, 0)
BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)

def visualize(moves, cell_size=CELL_SIZE, delay=DELAY):
    """Display a sequence of moves by replaying the game."""
    pygame.init()
    game = HasamiShogi()
    board_size = 9
    window_size = board_size * cell_size + 2 * MARGIN
    screen = pygame.display.set_mode((window_size, window_size))
    pygame.display.set_caption("Hasami Shogi Visualizer")

    # Display initial board
    draw_board(screen, game.board, cell_size)
    time.sleep(delay)

    running = True
    for move in moves:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
        if not running:
            break

        # Apply the move
        r1, c1, r2, c2 = move
        game.apply_move(r1, c1, r2, c2, game.turn)
        
        # Draw the board after the move
        draw_board(screen, game.board, cell_size)
        time.sleep(delay)

    pygame.quit()

def draw_board(screen, board, cell_size=CELL_SIZE):
    """Draw the board with pieces and coordinates."""
    board_size = len(board)
    
    # draw background
    screen.fill(BG_COLOR)
    
    # draw grid and pieces
    for r in range(board_size):
        for c in range(board_size):
            x, y = MARGIN + c * cell_size, MARGIN + r * cell_size
            rect = pygame.Rect(x, y, cell_size, cell_size)
            pygame.draw.rect(screen, WHITE_COLOR, rect)
            pygame.draw.rect(screen, GRID_COLOR, rect, 1)
            piece = board[r][c]
            if piece == BLACK:
                pygame.draw.circle(screen, BLACK_COLOR, rect.center, cell_size//2 - 5)
            elif piece == WHITE:
                pygame.draw.circle(screen, WHITE_COLOR, rect.center, cell_size//2 - 5)
                pygame.draw.circle(screen, GRID_COLOR, rect.center, cell_size//2 - 5, 2)
    
    # Draw coordinate labels
    font = pygame.font.Font(None, 24)
    
    # Column labels (0-8)
    for c in range(board_size):
        x = MARGIN + c*cell_size + cell_size//2
        # Top
        text = font.render(str(c), True, (0,0,0))
        text_rect = text.get_rect(center=(x, MARGIN//2))
        screen.blit(text, text_rect)
        # Bottom
        text = font.render(str(c), True, (0,0,0))
        text_rect = text.get_rect(center=(x, MARGIN + board_size*cell_size + MARGIN//2))
        screen.blit(text, text_rect)
    
    # Row labels (0-8)
    for r in range(board_size):
        y = MARGIN + r*cell_size + cell_size//2
        # Left
        text = font.render(str(r), True, (0,0,0))
        text_rect = text.get_rect(center=(MARGIN//2, y))
        screen.blit(text, text_rect)
        # Right
        text = font.render(str(r), True, (0,0,0))
        text_rect = text.get_rect(center=(MARGIN + board_size*cell_size + MARGIN//2, y))
        screen.blit(text, text_rect)

    pygame.display.flip()

if __name__ == "__main__":
    # Load a pickled history list of moves (each a tuple of (r1, c1, r2, c2))
    with open("history.pkl", "rb") as f:
        history = pickle.load(f)
    visualize(history)
