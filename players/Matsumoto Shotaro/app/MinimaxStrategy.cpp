// app/MinimaxStrategy.cpp
#include "MinimaxStrategy.hpp"

// 軽量評価：駒数差×10 + mobility 差
int MinimaxStrategy::quickEval(const Board& b, int player, const Move& m) const {
    Board nb = b; nb.apply_move(m, player);
    int myMob  = nb.get_legal_moves(player).size();
    int oppMob = nb.get_legal_moves(-player).size();
    return (nb.count_pieces(player) - nb.count_pieces(-player)) * 10
         + (myMob - oppMob);
}

// フル評価：駒数差×100 のみ（シンプル）
int MinimaxStrategy::evaluateBoard(const Board& b, int player) const {
    return 100 * (b.count_pieces(player) - b.count_pieces(-player));
}
