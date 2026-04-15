// app/OrthDiagStrategy.cpp
#include "OrthDiagStrategy.hpp"
#include <algorithm>

int OrthDiagStrategy::evaluateBoard(const Board& b, int player) const {
    int size   = b.height();
    int center = size / 2;
    int opp    = -player;
    int score  = 0;

    // --- 駒数差（基本） ---
    score += 100 * (b.count_pieces(player) - b.count_pieces(opp));

    // --- 可動度差をちょいプラス ---
    int myMob  = b.get_legal_moves(player).size();
    int oppMob = b.get_legal_moves(opp).size();
    score += 5 * (myMob - oppMob);

    // --- (1) 縦横連結度 ---
    const int orth_w = 10;
    static const int dirs4[4][2] = {
        { 1, 0}, {-1, 0}, { 0, 1}, { 0,-1}
    };
    for (int y = 0; y < size; ++y) {
        for (int x = 0; x < size; ++x) {
            if (b.get_piece(y,x) != player) continue;
            for (auto& d : dirs4) {
                int ny = y + d[0], nx = x + d[1];
                if (ny<0||ny>=size||nx<0||nx>=size) continue;
                if (b.get_piece(ny,nx) == player)
                    score += orth_w;
            }
        }
    }

    // --- (2) 斜め連結度 ---
    const int diag_w = 3;
    static const int dirsDiag[4][2] = {
        { 1, 1}, { 1,-1}, {-1, 1}, {-1,-1}
    };
    for (int y = 0; y < size; ++y) {
        for (int x = 0; x < size; ++x) {
            if (b.get_piece(y,x) != player) continue;
            for (auto& d : dirsDiag) {
                int ny = y + d[0], nx = x + d[1];
                if (ny<0||ny>=size||nx<0||nx>=size) continue;
                if (b.get_piece(ny,nx) == player)
                    score += diag_w;
            }
        }
    }

    // --- (3) 中心制御 ---
    for (int y = 0; y < size; ++y) {
        for (int x = 0; x < size; ++x) {
            if (b.get_piece(y,x) == player) {
                int dist = std::abs(y-center) + std::abs(x-center);
                score += (center*2 - dist);
            }
        }
    }

     // ── 即時捕獲リスクペナルティ ──
    auto oppMoves = b.get_legal_moves(opp);
    int lossTotal = 0;
    for (auto& m : oppMoves) {
        Board nb = b; nb.apply_move(m, opp);
        lossTotal += (b.count_pieces(player) - nb.count_pieces(player));
    }
    score -= 50 * lossTotal;

    // ── 移動後の局所安全度ペナルティ ──
    // 「自駒が相手に隣接し、かつ背後が空いている」ようなリスクを重視
    const int SAFETY_PENALTY = 100;
    for (int y = 0; y < size; ++y) {
        for (int x = 0; x < size; ++x) {
            if (b.get_piece(y,x) != player) continue;
            // ４方向に敵隣接＆逆方向空きチェック
            static const int d4[4][2] = {{1,0},{-1,0},{0,1},{0,-1}};
            for (auto& d : d4) {
                int iy = y + d[0], ix = x + d[1];
                int by = y - d[0], bx = x - d[1];
                if (iy<0||iy>=size||ix<0||ix>=size) continue;
                if (b.get_piece(iy,ix) == opp
                 && by>=0&&by<size&&bx>=0&&bx<size
                 && b.get_piece(by,bx) == PLAYER_NONE) {
                    score -= SAFETY_PENALTY;
                }
            }
        }
    }

    return score;
}

int OrthDiagStrategy::quickEval(const Board& b, int player, const Move& m) const {
    Board nb = b; nb.apply_move(m, player);
// 軽量評価にも安全度ペナルティを追加
    int myMob  = nb.get_legal_moves(player).size();
    int oppMob = nb.get_legal_moves(-player).size();
    int s = (myMob - oppMob) * 2;
    // 移動した駒が隣接リスクあるなら少し減点
    int ry = m.toY, rx = m.toX;
    static const int d4[4][2] = {{1,0},{-1,0},{0,1},{0,-1}};
    for (auto& d : d4) {
        int iy = ry + d[0], ix = rx + d[1];
        if (iy<0||iy>=nb.height()||ix<0||ix>=nb.width()) continue;
        if (nb.get_piece(iy,ix) == -player) s -= 50;
    }
    return s;
}
