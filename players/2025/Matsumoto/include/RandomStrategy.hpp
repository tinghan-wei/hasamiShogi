#pragma once
#include "IAIStrategy.hpp"
#include <random>

class RandomStrategy : public IAIStrategy {
    std::mt19937 rng{std::random_device{}()};
public:
    Move selectMove(const Board& board, int player) override {
        auto moves = board.get_legal_moves(player);
        std::uniform_int_distribution<size_t> d(0, moves.size()-1);
        return moves[d(rng)];
    }
};
