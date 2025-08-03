#pragma once
#include <vector>
#include <iostream>

constexpr int BOARD_SIZE = 9;       // 盤面サイズ

// Player識別ID？
constexpr int PLAYER_NONE = 0;
constexpr int PLAYER_1 = 1;
constexpr int PLAYER_2 = -1;

struct Move {
    int fromY, fromX;
    int toY, toX;
    Move(int fy, int fx, int ty, int tx)
        : fromY(fy), fromX(fx), toY(ty), toX(tx) {}
};

class Board {
private:
    int board[BOARD_SIZE][BOARD_SIZE];

public:
    Board();
    void reset();
    void print() const;
    std::vector<Move> get_legal_moves(int player) const;
    void apply_move(const Move& move, int player);
    int count_pieces(int player) const;
    int check_winner(int turn, int turn_count) const;

    int get_piece(int y, int x) const;
    int width() const;
    int height() const;
};
