import unittest
import hasamiShogi

game = hasamiShogi.HasamiShogi()

class TestHasamiShogi(unittest.TestCase):
    def test_victory(self):
        board = [
            ".BBB....B",
            ".........",
            ".........",
            ".......B.",
            "....BBBW.",
            "B........",
            ".........",
            ".........",
            "WWWWWWW.W"
        ]
        game.set_board(board)
        game.apply_move(8,3,4,3, hasamiShogi.WHITE)
        player = game.is_game_over()
        self.assertEqual(player, None)

        game.apply_move(0,8,4,8, hasamiShogi.BLACK)
        player = game.is_game_over()
        self.assertEqual(player, hasamiShogi.WHITE)

        board = [
            #012345678
            ".BBB....B", # 0
            ".........", # 1
            ".........", # 2
            ".......BW", # 3
            "....BBBW.", # 4
            "B........", # 5
            ".........", # 6
            ".........", # 7
            "WWWWWWW.."
        ]
        game.set_board(board)
        # W leads by 3
        game.apply_move(8,3,4,3, hasamiShogi.WHITE)
        player = game.is_game_over()
        self.assertEqual(player, None)

        # B captures 1 to undo the lead
        game.apply_move(5,0,5,7, hasamiShogi.BLACK)
        player = game.is_game_over()
        self.assertEqual(player, None)

        # W captures 1 again to get the lead again
        game.apply_move(8,6,3,6, hasamiShogi.WHITE)
        player = game.is_game_over()
        self.assertEqual(player, None)

        # B cannot capture back, W wins
        game.apply_move(0,8,2,8, hasamiShogi.BLACK)
        player = game.is_game_over()
        self.assertEqual(player, hasamiShogi.WHITE)

    def test_corner(self):
        board = [
            #012345678
            "WWWB.WB.W",
            ".BB...B.B",
            ".........",
            ".........",
            "......B..",
            ".........",
            "B........",
            ".........",
            "........."
        ]
        game.set_board(board)
        game.apply_move(1,6,1,7, hasamiShogi.BLACK)
        self.assertEqual(game.board[0][7], hasamiShogi.EMPTY)
        self.assertEqual(game.board[0][8], hasamiShogi.WHITE)
        
        # white captures after first move
        game.apply_move(0,8,0,7, hasamiShogi.WHITE)
        game.apply_move(1,8,0,8, hasamiShogi.BLACK)
        self.assertEqual(game.board[0][7], hasamiShogi.WHITE)

        # black captures back
        game.apply_move(4,6,0,6, hasamiShogi.BLACK)
        self.assertEqual(game.board[0][7], hasamiShogi.EMPTY)
        
        game.apply_move(0,5,1,5, hasamiShogi.WHITE)
        game.apply_move(6,0,1,0, hasamiShogi.BLACK)
        self.assertEqual(game.board[0][0], hasamiShogi.EMPTY)
        self.assertEqual(game.board[0][1], hasamiShogi.EMPTY)
        self.assertEqual(game.board[0][2], hasamiShogi.EMPTY)
        player = game.is_game_over()

        game.apply_move(1,5,2,5, hasamiShogi.WHITE)
        # print(game.serialize())
        player = game.is_game_over()
        self.assertEqual(player, hasamiShogi.BLACK)

    def test_real(self):
        board = [
        ".BB..BBB.",
        "W...B....",
        ".........",
        ".........",
        ".........",
        "B........",
        "W........",
        "........W",
        "..WWWWWW."]
        game.set_board(board)
        game.captures[hasamiShogi.WHITE] = 2
        game.apply_move(1,0,4,0, hasamiShogi.WHITE)
        player = game.is_game_over()
        self.assertEqual(player, None)
        game.apply_move(0,1,1,1, hasamiShogi.BLACK)
        player = game.is_game_over()
        self.assertEqual(player, hasamiShogi.WHITE)

if __name__ == '__main__':
    unittest.main()
