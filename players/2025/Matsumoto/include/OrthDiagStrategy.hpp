// include/OrthDiagStrategy.hpp
#pragma once
#include "BaseMinimaxStrategy.hpp"
#include <cmath>

class OrthDiagStrategy : public BaseMinimaxStrategy {
protected:
    // ① 縦横連結＋② 斜め連結＋③ 中心制御
    int evaluateBoard(const Board& b, int player) const override;
    // ムーブ順序づけはとりあえず可動度差だけ
    int quickEval(const Board& b, int player, const Move& m) const override;
};
