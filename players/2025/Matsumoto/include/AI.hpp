#pragma once
#include <memory>
#include "IAIStrategy.hpp"

class AI {
    std::unique_ptr<IAIStrategy> strat;
public:
    AI(std::unique_ptr<IAIStrategy> s);
    Move select_move(const Board& board, int player);
};
