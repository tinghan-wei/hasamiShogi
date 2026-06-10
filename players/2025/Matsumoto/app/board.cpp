#include "board.hpp"
#include <iomanip>

Board::Board() {
    reset();
}

void Board::reset() {
    for (int y = 0; y < BOARD_SIZE; ++y)
        for (int x = 0; x < BOARD_SIZE; ++x)
            board[y][x] = PLAYER_NONE;

    for (int x = 0; x < BOARD_SIZE; ++x) {
        board[0][x] = PLAYER_1;
        board[BOARD_SIZE - 1][x] = PLAYER_2;
    }
}

int Board::get_piece(int y, int x) const {
    return board[y][x];
}

int Board::width() const {
    return BOARD_SIZE;
}

int Board::height() const {
    return BOARD_SIZE;
}

void Board::print() const {
    std::cout << "  ";
    for (int x = 0; x < BOARD_SIZE; ++x)
        std::cout << x << " ";
    std::cout << "\n";

    for (int y = 0; y < BOARD_SIZE; ++y) {
        std::cout << y << " ";
        for (int x = 0; x < BOARD_SIZE; ++x) {
            char c = '.';
            if (board[y][x] == PLAYER_1) c = 'X';
            else if (board[y][x] == PLAYER_2) c = 'O';
            std::cout << c << " ";
        }
        std::cout << "\n";
    }
}

// 盤面にある駒数を数える
int Board::count_pieces(int player) const {
    int count = 0;
    for (int y = 0; y < BOARD_SIZE; ++y)
        for (int x = 0; x < BOARD_SIZE; ++x)
            if (board[y][x] == player)
                ++count;
    return count;
}

// 勝敗判定
int Board::check_winner(int turn, int turn_count) const {
    int p1 = count_pieces(PLAYER_1);
    int p2 = count_pieces(PLAYER_2);

    if (p1 < 5) return PLAYER_2;
    if (p2 < 5) return PLAYER_1;
    if (turn_count > 500) return 9; // draw

    return 0; // ongoing
}

// 合法手を探す
std::vector<Move> Board::get_legal_moves(int player) const {
    std::vector<Move> moves;

    for (int y = 0; y < BOARD_SIZE; ++y) {
        for (int x = 0; x < BOARD_SIZE; ++x) {
            if (board[y][x] != player) continue;

            // 縦・横移動（飛車ルール）
            const int dirs[4][2] = {
                {0, 1}, {0, -1}, {1, 0}, {-1, 0}
            };

            for (auto [dy, dx] : dirs) {
                int ny = y + dy, nx = x + dx;
                while (ny >= 0 && ny < BOARD_SIZE && nx >= 0 && nx < BOARD_SIZE) {
                    if (board[ny][nx] != PLAYER_NONE) break;
                    moves.emplace_back(y, x, ny, nx);
                    ny += dy;
                    nx += dx;
                }
            }
        }
    }

    return moves;
}

void Board::apply_move(const Move& move, int player) {
    board[move.toY][move.toX] = player;
    board[move.fromY][move.fromX] = PLAYER_NONE;

    // 🔥 挟み処理ここから
    const int dirs[4][2] = {
        {0, 1}, {0, -1}, {1, 0}, {-1, 0}
    };

    for (const auto& dir : dirs) {
        int dy = dir[0], dx = dir[1];
        int cy = move.toY + dy;
        int cx = move.toX + dx;

        // 隣が盤外 or 自駒 or 空ならcontinue
        if (cy < 0 || cy >= BOARD_SIZE || cx < 0 || cx >= BOARD_SIZE) continue;
        if (board[cy][cx] != -player) continue;

        int ey = cy + dy;
        int ex = cx + dx;

        if (ey < 0 || ey >= BOARD_SIZE || ex < 0 || ex >= BOARD_SIZE) continue;
        if (board[ey][ex] == player) {
            // 敵駒を除去！
            board[cy][cx] = PLAYER_NONE;
        }
    }
}