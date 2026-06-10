// include/MinimaxStrategy.hpp
#pragma once
#include "BaseMinimaxStrategy.hpp"

class MinimaxStrategy : public BaseMinimaxStrategy {
protected:
    int evaluateBoard(const Board& b, int player) const override;
    int quickEval    (const Board& b, int player, const Move& m) const override;
};
