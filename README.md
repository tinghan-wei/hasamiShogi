# はさみ将棋

AI プレイヤーとトーナメント対戦環境を備えた、はさみ将棋の Python 実装です。

## 概要

はさみ将棋は、9×9 の盤面で行う 2 人用のボードゲームです。このプロジェクトには以下が含まれます。

* **ゲームエンジン**: 基本ルールおよびゲームロジックの実装
* **トーナメント環境**: 複数の AI プレイヤーを対戦させるためのフレームワーク
* **AI プレイヤー**: ランダムプレイヤーや学生が実装した AI
* **可視化**: Pygame を用いた対局表示
* **テストスイート**: ゲームの仕組みを検証するユニットテスト

## ゲームルール

はさみ将棋は 9×9 の盤面で行われ、以下のようなルールがあります。

* 黒駒は最上段（0 行目）から開始する
* 白駒は最下段（8 行目）から開始する
* プレイヤーは交互に、駒を縦または横に動かす
* 駒は、相手の駒で両側から挟まれると取られる
* 一方のプレイヤーの駒数が相手より 3 枚以上多くなった場合、相手にはその差を 3 枚以内に縮めるための最後の 1 手が与えられる。それができなければ、その時点で負けとなる
* あるいは、一方のプレイヤーが相手より 5 枚以上多くなった時点で即勝利となる

## プロジェクト構成

```text
.
├── hasamiShogi.py          # ゲームエンジン
├── arena.py                # プレイヤー対戦用のトーナメント環境
├── visualize.py            # 対局記録を用いたゲーム可視化
├── hasamiTest.py           # ユニットテスト
├── randomPlayer.py         # ランダムプレイヤー
└── players/                # AI プレイヤー実装のディレクトリ
    ├── Itoh.py
    ├── Tanimoto.py
    ├── Yamada.py
    ├── Shimizu.py
    └── Kumon/              # C/C++
        ├── alphabeta.c
        ├── alphabeta.h
        ├── my_ai.c
        └── shogi.c
    └── Matsumoto/          # C++
        ├── app/            # ソースファイル
        └── include/        # ヘッダファイル
```

## 主なファイル

### 中核コンポーネント

* **hasamiShogi.py**: 盤面状態、合法手生成、手の妥当性判定、勝敗条件を実装するゲームエンジン
* **arena.py**: 可視化機能付きでプレイヤー同士の対戦を管理するトーナメントシステム
* **visualize.py**: 対局記録からゲームを観戦するための Pygame ベース GUI

### テスト

* **hasamiTest.py**: ゲームロジックを検証するためのユニットテスト

### プレイヤー

* **randomPlayer.py**: 合法手の中からランダムに指す基準用プレイヤー
* **players/**: 各学生によるさまざまな戦略の AI 実装を含むディレクトリ

## インストール

### 必要環境

* Python 3.x
* pygame（可視化用）

### セットアップ

```bash
pip install pygame
```

C/C++ のプレイヤーモジュールについては、それぞれのビルド方法に従って必要に応じてコンパイルしてください。

## 使い方

### 2 人のプレイヤーで対戦を実行する

```bash
python arena.py <player1_module> <player2_module>
```

例:

```bash
python arena.py "python randomPlayer.py" "python randomPlayer.py"
python arena.py "python players/Itoh.py" "python players/Tanimoto.py"
```

### テストを実行する

```bash
python hasamiTest.py
```

## ゲーム通信プロトコル

プレイヤーは、以下のプロトコルに従って stdin/stdout を通じて arena とやり取りします。

1. Arena が送信する: `OK?`
2. プレイヤーが応答する: `<PlayerName>`
3. Arena が送信する: `<Color>`（Black または White）
4. プレイヤーは、`r1c1r2c2` の 4 桁文字列形式で指し手を受け取る（開始位置 row-col から終了位置 row-col へ）
5. プレイヤーは同じ形式で指し手を出力する
6. ゲーム終了時には次が送信される: `GAME_OVER <Winner>`


# Hasami Shogi

A Python implementation of Hasami Shogi (Japanese chess variant) with AI players and tournament arena.

## Overview

Hasami Shogi is a two-player abstract strategy board game played on a 9×9 board. This project provides:

- **Game Engine**: Core rules and game logic implementation
- **Tournament Arena**: Framework for multiple AI players to compete
- **AI Players**: Various student-implemented AI strategies ranging from random to advanced minimax algorithms
- **Visualization**: Pygame-based visual display of games
- **Testing Suite**: Comprehensive unit tests for game mechanics

## Game Rules

Hasami Shogi is played on a 9×9 board with:
- Black pieces starting on the top row (row 0)
- White pieces starting on the bottom row (row 8)
- Players alternate turns moving pieces horizontally or vertically
- Pieces are captured when surrounded on opposite sides by opponent pieces
- When one player has at least three more pieces than their opponent, the opponent has one more turn to reduce the gap to within three pieces. If the opponent is unable to do so, the opponent loses the game.
- Alternatively, whichever player has five or more pieces than their opponent wins immediately.

## Project Structure

```
.
├── hasamiShogi.py          # Core game engine
├── arena.py                # Tournament arena for player matches
├── visualize.py            # Game visualization using play records
├── hasamiTest.py           # Unit tests
├── randomPlayer.py         # Simple random move player
└── players/                # Directory of AI player implementations
    ├── Itoh.py
    ├── Tanimoto.py
    ├── Yamada.py
    ├── Shimizu.py
    └── Kumon/   # C/C++
        ├── alphabeta.c
        ├── alphabeta.h
        ├── my_ai.c
        └── shogi.c
    └── Matsumoto/ # C++
        ├── app/           # Source files
        └── include/       # Header files
```

## Key Files

### Core Components

- **hasamiShogi.py**: Game engine implementing board state, move generation, move validation, and victory conditions
- **arena.py**: Tournament system that orchestrates matches between players with visualization
- **visualize.py**: Pygame-based GUI for watching games from records

### Testing

- **hasamiTest.py**: Unit tests for game logic validation

### Players

- **randomPlayer.py**: Baseline player making random legal moves
- **players/**: Directory containing AI implementations by different students using various strategies:

## Installation

### Requirements

- Python 3.x
- pygame (for visualization)

### Setup

```bash
pip install pygame
```

For C/C++ player modules, compile as needed using their respective build systems.

## Usage

### Run a Match Between Two Players

```bash
python arena.py <player1_module> <player2_module>
```

Example:
```bash
python arena.py "python randomPlayer.py" "python randomPlayer.py"
python arena.py "python players/Itoh.py" "python players/Tanimoto.py"
```

### Run Tests
```bash
python hasamiTest.py
```

## Game Communication Protocol

Players interact with the arena through stdin/stdout using this protocol:

1. Arena sends: `OK?`
2. Player responds with: `<PlayerName>`
3. Arena sends: `<Color>` (Black or White)
4. Player receives moves as 4-digit strings: `r1c1r2c2` (from row-col to row-col)
5. Player outputs moves in same format
6. Game ends with: `GAME_OVER <Winner>`
 