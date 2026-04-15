// app/main.cpp

#include <iostream>
#include <string>
#include "board.hpp"
#include "AI.hpp"
#include "EnhancedMinimaxStrategy.hpp"

Move parse_move(const std::string& s) {
    return Move(s[0]-'0', s[1]-'0', s[2]-'0', s[3]-'0');
}

std::string format_move(const Move& m) {
    std::string s;
    s += char('0' + m.fromY);
    s += char('0' + m.fromX);
    s += char('0' + m.toY);
    s += char('0' + m.toX);
    return s;
}

int main(){
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    // 1) ハンドシェイク
    std::string line;
    std::getline(std::cin, line);             // アリーナからの「OK?」等
    std::cout << "MyHasamiAI_V1\n" << std::flush;

    // 2) 色受信
    std::string color_line;
    std::getline(std::cin, color_line);
    int my_color  = (color_line == "Black" ? PLAYER_1 : PLAYER_2);
    int opp_color = -my_color;

    // 盤面＆AI初期化
    Board board;
    board.reset();
    AI ai(std::make_unique<EnhancedMinimaxStrategy>());

    // ３枚差勝利候補フラグ (0:なし, PLAYER_1 or PLAYER_2)
    int threeDiffOwner = 0;

    // 3) 先手なら初手を打つ
    if (my_color == PLAYER_1) {
        Move m = ai.select_move(board, my_color);
        board.apply_move(m, my_color);
        std::cout << format_move(m) << "\n" << std::flush;
    }

    // 4) 対局ループ
    while (true) {
        // --- 相手の手受信・適用 ---
        std::string opp_s;
        if (!std::getline(std::cin, opp_s)) break;
        if (opp_s.empty() || opp_s.rfind("GAME_OVER",0)==0) break;
        Move opp_m = parse_move(opp_s);
        board.apply_move(opp_m, opp_color);

        // --- 終了判定 after opponent move ---
        {
            int p1   = board.count_pieces(PLAYER_1);
            int p2   = board.count_pieces(PLAYER_2);
            int cap1 = 9 - p1;
            int cap2 = 9 - p2;
            // 先に5枚
            if (cap1 >= 5 || cap2 >= 5) break;
            // ３枚差ロジック
            int diff = cap1 - cap2;  
            if (diff >= 3) {
                if (threeDiffOwner == PLAYER_1) break;
                threeDiffOwner = PLAYER_1;
            }
            else if (diff <= -3) {
                if (threeDiffOwner == PLAYER_2) break;
                threeDiffOwner = PLAYER_2;
            }
            else {
                threeDiffOwner = 0;
            }
        }

        // --- 自分の手生成・適用・出力 ---
        Move my_m = ai.select_move(board, my_color);
        board.apply_move(my_m, my_color);
        std::cout << format_move(my_m) << "\n" << std::flush;

        // --- 終了判定 after our move ---
        {
            int p1   = board.count_pieces(PLAYER_1);
            int p2   = board.count_pieces(PLAYER_2);
            int cap1 = 9 - p1;
            int cap2 = 9 - p2;
            if (cap1 >= 5 || cap2 >= 5) break;
            int diff = cap1 - cap2;
            if (diff >= 3) {
                if (threeDiffOwner == PLAYER_1) break;
                threeDiffOwner = PLAYER_1;
            }
            else if (diff <= -3) {
                if (threeDiffOwner == PLAYER_2) break;
                threeDiffOwner = PLAYER_2;
            }
            else {
                threeDiffOwner = 0;
            }
        }
    }

    return 0;
}
