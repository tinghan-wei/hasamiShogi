// main.c (修正版)

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "shogi.h"
#include "alphabeta.h" 

void parse_move(const char* str, int* r1, int* c1, int* r2, int* c2);
void run_ai();

int main() {
    srand(time(NULL));
    run_ai();
    return 0;
}

void run_ai() {
    char line[256];
    GameState game;
    // my_color, opp_color は不要なので削除

    // arena.pyとの通信ループ
    while (fgets(line, sizeof(line), stdin) != NULL) {
        line[strcspn(line, "\n")] = 0; // 改行文字を削除

        if (strcmp(line, "OK?") == 0) {
            printf("MCTS_C_AI\n");
            fflush(stdout);
        } else if (strcmp(line, "Black") == 0) {
            // 'B' (黒) でゲームを初期化
            init_game(&game, BLACK);
            
            Move best_move = find_best_move(&game);
            apply_move(&game, &best_move);
            printf("%d%d%d%d\n", best_move.r1, best_move.c1, best_move.r2, best_move.c2);
            fflush(stdout);

        } else if (strcmp(line, "White") == 0) {
            // 'W' (白) でゲームを初期化
            init_game(&game, WHITE);

        } else if (strncmp(line, "GAME_OVER", 9) == 0) {
            break;

        } else if (strlen(line) == 4 && strspn(line, "0123456789") == 4) {
            Move opp_move;
            parse_move(line, &opp_move.r1, &opp_move.c1, &opp_move.r2, &opp_move.c2);
            apply_move(&game, &opp_move);
            
            Move my_move = find_best_move(&game);
            apply_move(&game, &my_move);
            printf("%d%d%d%d\n", my_move.r1, my_move.c1, my_move.r2, my_move.c2);
            fflush(stdout);
        }
    }
}

// parse_move関数は変更なし
void parse_move(const char* str, int* r1, int* c1, int* r2, int* c2) {
    *r1 = str[0] - '0';
    *c1 = str[1] - '0';
    *r2 = str[2] - '0';
    *c2 = str[3] - '0';
}