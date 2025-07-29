import hasamiShogi

game = hasamiShogi.HasamiShogi()

board = [
    "BBBB.BBBB",
    ".........",
    ".........",
    ".........",
    ".........",
    ".........",
    ".........",
    ".........",
    "WWWWWWWWW"
]
game.set_board(board)
print(game.serialize())

game.apply_move(8,4,0,4, hasamiShogi.WHITE)
print(game.serialize())