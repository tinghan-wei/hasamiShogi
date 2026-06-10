#include "EnhancedMinimaxStrategy.hpp"
#include <algorithm>

int EnhancedMinimaxStrategy::evaluateBoard(const Board& b, int player) const {
    int opp    = -player;
    int size   = b.height();
    int center = size/2;
    int score  = 0;

    // 駒数差
    score += 100 * (b.count_pieces(player) - b.count_pieces(opp));
    // mobility
    score += 5 * (int(b.get_legal_moves(player).size())
                - int(b.get_legal_moves(opp).size()));

    // threats
    int threats = 0;
    for (auto& m : b.get_legal_moves(player)) {
        int dy = m.toY - m.fromY, dx = m.toX - m.fromX;
        int ry = m.toY + dy, rx = m.toX + dx;
        if (0 <= ry && ry < size && 0 <= rx && rx < size
            && b.get_piece(ry,rx) == opp) {
            ++threats;
        }
    }
    score += 10 * threats;

    // 連結度：縦横／斜め別重み
    const int orth_w = 10, diag_w = 3;
    static const int dirs8[8][2] = {
        { 1, 0},{-1, 0},{ 0, 1},{ 0,-1},
        { 1, 1},{ 1,-1},{-1, 1},{-1,-1}
    };
    for (int y=0;y<size;++y){
        for (int x=0;x<size;++x){
            if (b.get_piece(y,x)!=player) continue;
            for (auto& d:dirs8){
                int ny=y+d[0], nx=x+d[1];
                if (ny<0||ny>=size||nx<0||nx>=size) continue;
                if (b.get_piece(ny,nx)==player) {
                    score += (d[0]==0||d[1]==0)? orth_w : diag_w;
                }
            }
            // 中心制御
            int dist = std::abs(y-center)+std::abs(x-center);
            score += (center*2 - dist);
        }
    }

    return score;
}

int EnhancedMinimaxStrategy::quickEval(const Board& b, int player, const Move& m) const {
    Board nb = b; nb.apply_move(m, player);
    int myMob  = nb.get_legal_moves(player).size();
    int oppMob = nb.get_legal_moves(-player).size();
    return (myMob - oppMob) * 2;
}
