#pragma once
#include "board.hpp"

struct IAIStrategy {
    virtual Move selectMove(const Board& board, int player) = 0;
    virtual ~IAIStrategy() = default;
};
