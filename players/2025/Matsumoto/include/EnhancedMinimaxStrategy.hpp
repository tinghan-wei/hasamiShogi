#pragma once
#include "BaseMinimaxStrategy.hpp"
#include <cmath>

class EnhancedMinimaxStrategy : public BaseMinimaxStrategy {
protected:
    int evaluateBoard(const Board& b, int player) const override;
    int quickEval    (const Board& b, int player, const Move& m) const override;
};
