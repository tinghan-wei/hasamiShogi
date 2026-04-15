// alphabeta.h

#ifndef ALPHABETA_H
#define ALPHABETA_H

#include "shogi.h"

// AIが何手先まで読むか（探索の深さ）。大きくすると強くなるが、思考時間が増える。
// 4でも結構強いですが、PCの性能に応じて調整してください。
#define SEARCH_DEPTH 5

#define MOBILITY_WEIGHT 0.8   // 機動力の価値
#define POSITIONAL_WEIGHT 0.5 // 駒の配置の価値

// 最善手を見つけるメイン関数
Move find_best_move(GameState* root_state);

#endif // ALPHABETA_H