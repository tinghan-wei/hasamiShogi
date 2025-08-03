#include "AI.hpp"

AI::AI(std::unique_ptr<IAIStrategy> s)
    : strat(std::move(s)) {}

Move AI::select_move(const Board& board, int player) {
    return strat->selectMove(board, player);
}
