#pragma once
#include "IAIStrategy.hpp"
#include "board.hpp"
#include <chrono>
#include <functional>
#include <limits>
#include <algorithm>
#include <vector>

class BaseMinimaxStrategy : public IAIStrategy {
protected:
    virtual int evaluateBoard(const Board& b, int player) const = 0;
    virtual int quickEval    (const Board& b, int player, const Move& m) const = 0;

    static constexpr int MAX_DEPTH     = 6;
    static constexpr std::chrono::seconds TIME_LIMIT{30};

public:
    Move selectMove(const Board& board, int player) override;
};
