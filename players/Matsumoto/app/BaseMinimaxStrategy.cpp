#include "BaseMinimaxStrategy.hpp"

Move BaseMinimaxStrategy::selectMove(const Board& board, int player) {
    using Clock = std::chrono::steady_clock;
    auto start = Clock::now();

    Move bestMove = board.get_legal_moves(player).front();
    int   bestScore = std::numeric_limits<int>::min();

    for (int depth = 1; depth <= MAX_DEPTH; ++depth) {
        bool timedOut = false;
        int alpha = std::numeric_limits<int>::min();
        int beta  = std::numeric_limits<int>::max();

        // ルートムーブ順序づけ
        auto moves = board.get_legal_moves(player);
        std::sort(moves.begin(), moves.end(),
            [&](auto const& a, auto const& b){
                return quickEval(board, player, a)
                     > quickEval(board, player, b);
            });

        std::function<int(const Board&,int,int,int,int)> dfs;
        dfs = [&](const Board& b, int d, int curr, int a, int bnd) -> int {
            if (Clock::now() - start > TIME_LIMIT) {
                timedOut = true;
                return 0;
            }
            if (d == 0) return evaluateBoard(b, player);

            auto lm = b.get_legal_moves(curr);
            std::sort(lm.begin(), lm.end(),
                [&](auto const& x, auto const& y){
                    return quickEval(b, curr, x)
                         > quickEval(b, curr, y);
                });

            if (lm.empty()) return evaluateBoard(b, player);

            if (curr == player) {
                int maxEval = std::numeric_limits<int>::min();
                for (auto const& mv : lm) {
                    Board nb = b; nb.apply_move(mv, curr);
                    int v = dfs(nb, d-1, -curr, a, bnd);
                    maxEval = std::max(maxEval, v);
                    a = std::max(a, v);
                    if (a >= bnd || timedOut) break;
                }
                return maxEval;
            } else {
                int minEval = std::numeric_limits<int>::max();
                for (auto const& mv : lm) {
                    Board nb = b; nb.apply_move(mv, curr);
                    int v = dfs(nb, d-1, -curr, a, bnd);
                    minEval = std::min(minEval, v);
                    bnd = std::min(bnd, v);
                    if (bnd <= a || timedOut) break;
                }
                return minEval;
            }
        };

        for (auto const& mv : moves) {
            if (Clock::now() - start > TIME_LIMIT) { timedOut = true; break; }
            Board nb = board; nb.apply_move(mv, player);
            int score = dfs(nb, depth-1, -player, alpha, beta);
            if (!timedOut && score > bestScore) {
                bestScore = score;
                bestMove  = mv;
            }
            alpha = std::max(alpha, bestScore);
            if (timedOut) break;
        }
        if (timedOut) break;
    }

    return bestMove;
}
