#include "shogi.h"
#include <string.h>
#include <stdio.h>

const int DIRS[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};

bool is_in_bounds(int r, int c) {
    return r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE;
}

// 駒を動かした時に発生する捕獲をチェックし、盤面に反映して捕獲数を返す
// apply_moveとis_legal_moveの両方から使えるように独立した関数にする
int check_and_perform_captures(GameState* game, int r_move, int c_move) {
    char me = game->board[r_move][c_move];
    if (me == EMPTY) return 0;
    char opp = (me == BLACK) ? WHITE : BLACK;
    int total_captured = 0;

    for (int i = 0; i < 4; ++i) {
        int dr = DIRS[i][0];
        int dc = DIRS[i][1];
        
        // 挟む先の駒を探す
        int r_sandwicher = r_move + dr;
        int c_sandwicher = c_move + dc;
        while(is_in_bounds(r_sandwicher, c_sandwicher) && game->board[r_sandwicher][c_sandwicher] == opp) {
            r_sandwicher += dr;
            c_sandwicher += dc;
        }

        if (is_in_bounds(r_sandwicher, c_sandwicher) && game->board[r_sandwicher][c_sandwicher] == me) {
            // 挟み成功。間の駒を捕獲する
            int r_cap = r_move + dr;
            int c_cap = c_move + dc;
            while (r_cap != r_sandwicher || c_cap != c_sandwicher) {
                game->board[r_cap][c_cap] = EMPTY;
                total_captured++;
                r_cap += dr;
                c_cap += dc;
            }
        }
    }
    return total_captured;
}

// 2点間のパスが空いているかチェック
bool is_path_clear(GameState* game, int r1, int c1, int r2, int c2) {
    if (r1 == r2) {
        int step = (c2 > c1) ? 1 : -1;
        for (int c = c1 + step; c != c2; c += step) {
            if (game->board[r1][c] != EMPTY) return false;
        }
    } else { // c1 == c2
        int step = (r2 > r1) ? 1 : -1;
        for (int r = r1 + step; r != r2; r += step) {
            if (game->board[r][c1] != EMPTY) return false;
        }
    }
    return true;
}

// 合法手かどうかを判定
bool is_legal_move(GameState* game, const Move* move) {
    if (!is_in_bounds(move->r1, move->c1) || !is_in_bounds(move->r2, move->c2)) return false;
    if (game->board[move->r1][move->c1] != game->turn) return false;
    if (game->board[move->r2][move->c2] != EMPTY) return false;
    if ((move->r1 != move->r2) && (move->c1 != move->c2)) return false; // 直線でない
    if ((move->r1 == move->r2) && (move->c1 == move->c2)) return false; // 動いていない
    if (!is_path_clear(game, move->r1, move->c1, move->r2, move->c2)) return false;

    // ここから自殺手のチェックロジック
    char me = game->turn;
    char opp = (me == BLACK) ? WHITE : BLACK;
    int r2 = move->r2;
    int c2 = move->c2;

    bool is_potential_suicide = false;
    // 水平方向に挟まれる可能性
    if (is_in_bounds(r2, c2 - 1) && game->board[r2][c2 - 1] == opp &&
        is_in_bounds(r2, c2 + 1) && game->board[r2][c2 + 1] == opp) {
        is_potential_suicide = true;
    }
    // 垂直方向に挟まれる可能性
    if (is_in_bounds(r2 - 1, c2) && game->board[r2 - 1][c2] == opp &&
        is_in_bounds(r2 + 1, c2) && game->board[r2 + 1][c2] == opp) {
        is_potential_suicide = true;
    }

    if (is_potential_suicide) {
        // 自殺手の可能性がある場合、捕獲が発生するかシミュレーションする
        GameState temp_game;
        copy_game_state(&temp_game, game);
        
        // 仮の盤面で手を動かす
        temp_game.board[move->r1][move->c1] = EMPTY;
        temp_game.board[r2][c2] = me;

        // この手で捕獲が発生するかチェック
        int captures_from_move = check_and_perform_captures(&temp_game, r2, c2);

        if (captures_from_move == 0) {
            // 捕獲が0なら、この手は違法な自殺手
            return false;
        }
    }
    return true;
}

// 盤面に手を適用し、駒の捕獲処理を行う
void apply_move(GameState* game, const Move* move) {
    char me = game->board[move->r1][move->c1];
    char opp = (me == BLACK) ? WHITE : BLACK;
    
    game->board[move->r2][move->c2] = me;
    game->board[move->r1][move->c1] = EMPTY;
    
    int total_captured = 0;
    
    // 挟み込みによる捕獲
    for (int i = 0; i < 4; ++i) {
        int dr = DIRS[i][0];
        int dc = DIRS[i][1];
        int r = move->r2 + dr;
        int c = move->c2 + dc;
        
        Move captured_pieces[BOARD_SIZE];
        int n_captured = 0;
        
        while (is_in_bounds(r, c) && game->board[r][c] == opp) {
            captured_pieces[n_captured++] = (Move){r, c, 0, 0};
            r += dr;
            c += dc;
        }
        
        if (is_in_bounds(r, c) && game->board[r][c] == me && n_captured > 0) {
            for (int j = 0; j < n_captured; ++j) {
                game->board[captured_pieces[j].r1][captured_pieces[j].c1] = EMPTY;
                total_captured++;
            }
        }
    }
    game->captures[me] += total_captured;
    game->turn = opp;
}

// 合法手をすべて生成する
int generate_legal_moves(GameState* game, Move legal_moves[]) {
    int count = 0;
    for (int r = 0; r < BOARD_SIZE; ++r) {
        for (int c = 0; c < BOARD_SIZE; ++c) {
            if (game->board[r][c] == game->turn) {
                // 上下左右に移動を試す
                for (int i = 0; i < 4; ++i) {
                    int dr = DIRS[i][0];
                    int dc = DIRS[i][1];
                    int nr = r + dr;
                    int nc = c + dc;
                    while (is_in_bounds(nr, nc) && game->board[nr][nc] == EMPTY) {
                        Move move = {r, c, nr, nc};
                        if (is_legal_move(game, &move)) {
                            legal_moves[count++] = move;
                        }
                        nr += dr;
                        nc += dc;
                    }
                }
            }
        }
    }
    return count;
}


// ゲームの初期化
void init_game(GameState* game, char my_color) {
    memset(game->board, EMPTY, sizeof(game->board));
    for (int c = 0; c < BOARD_SIZE; ++c) {
        game->board[0][c] = BLACK;
        game->board[BOARD_SIZE - 1][c] = WHITE;
    }
    game->turn = BLACK;
    game->my_color = my_color;
    game->captures[BLACK] = 0;
    game->captures[WHITE] = 0;
}

// 盤面を文字列に変換する (Qテーブルのキーとして使用)
void get_state_string(const GameState* game, char* buffer) {
    int index = 0;
    for (int r = 0; r < BOARD_SIZE; ++r) {
        for (int c = 0; c < BOARD_SIZE; ++c) {
            buffer[index++] = game->board[r][c];
        }
    }
    buffer[index] = '\0';
}

void copy_game_state(GameState* dest, const GameState* src) {
    memcpy(dest, src, sizeof(GameState));
}

char is_game_over(GameState* game) {
    if (game->captures[BLACK] >= 8) return BLACK;
    if (game->captures[WHITE] >= 8) return WHITE;
    
    // 手番のプレイヤーが動かせる駒がない場合も負け
    Move legal_moves[300];
    if (generate_legal_moves(game, legal_moves) == 0) {
        return (game->turn == BLACK) ? WHITE : BLACK;
    }
    
    return EMPTY; // ゲームは続行
}