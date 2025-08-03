#ifndef SHOGI_H
#define SHOGI_H

#include <stdbool.h>

#define BOARD_SIZE 9
#define EMPTY '.'
#define BLACK 'B'
#define WHITE 'W'

// 指し手
typedef struct {
    int r1, c1, r2, c2;
} Move;

// ゲーム状態
typedef struct {
    char board[BOARD_SIZE][BOARD_SIZE];
    char turn;
    char my_color;
    int captures[256]; // 'B' と 'W' のインデックスでアクセス
} GameState;

void init_game(GameState* game, char my_color);
bool is_legal_move(GameState* game, const Move* move);
void apply_move(GameState* game, const Move* move);
int generate_legal_moves(GameState* game, Move legal_moves[]);
void get_state_string(const GameState* game, char* buffer);
void copy_game_state(GameState* dest, const GameState* src);
char is_game_over(GameState* game);

#endif // SHOGI_H