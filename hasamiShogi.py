import copy

BOARD_SIZE = 9
EMPTY, BLACK, WHITE = '.', 'B', 'W'
DIRECTIONS = [(1,0),(-1,0),(0,1),(0,-1)]

class HasamiShogi:
    def __init__(self):
        self.board = [[EMPTY]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        for c in range(BOARD_SIZE):
            self.board[0][c] = BLACK
            self.board[-1][c] = WHITE
        # track captures: how many pieces each color has captured
        self.captures = {BLACK: 0, WHITE: 0}
        # pending victory condition state
        self.pending_leader = None
        self.turn = BLACK

    def set_board(self, board_list):
        """
        Set the board state directly for testing.
        Expects a list of BOARD_SIZE lists/strings, each of length BOARD_SIZE,
        containing only '.', 'B', or 'W'.
        """
        if len(board_list) != BOARD_SIZE:
            raise ValueError(f"Board must have {BOARD_SIZE} rows")
        new_board = []
        for r, row in enumerate(board_list):
            if len(row) != BOARD_SIZE:
                raise ValueError(f"Row {r} must have {BOARD_SIZE} columns")
            row_list = list(row)
            for c, cell in enumerate(row_list):
                if cell not in (EMPTY, BLACK, WHITE):
                    raise ValueError(f"Invalid piece '{cell}' at ({r},{c})")
            new_board.append(row_list)
        self.board = new_board
        # track captures: how many pieces each color has captured
        self.captures = {BLACK: 0, WHITE: 0}
        # pending victory condition state
        self.pending_leader = None
        self.turn = BLACK

    def serialize(self):
        """
        Return a string representation of the board with coordinate labels:
        - Columns labeled 0..8 at top and bottom
        - Rows labeled 0..8 on both left and right of each row
        """
        lines = []
        # Top column labels
        header = '   ' + ' '.join(str(c) for c in range(BOARD_SIZE))
        lines.append(header)
        # Board rows with side labels
        for r in range(BOARD_SIZE):
            row_str = ' '.join(self.board[r])
            lines.append(f"{r}  {row_str}  {r}")
        # Bottom column labels
        lines.append(header)
        return '\n'.join(lines)

    def in_bounds(self, r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def is_clear_path(self, r1, c1, r2, c2):
        """Return True if all squares strictly between (r1,c1) and (r2,c2) are EMPTY."""
        # must be straight-line
        if r1 == r2:
            step = 1 if c2 > c1 else -1
            for c in range(c1 + step, c2, step):
                if self.board[r1][c] != EMPTY:
                    return False
            return True
        elif c1 == c2:
            step = 1 if r2 > r1 else -1
            for r in range(r1 + step, r2, step):
                if self.board[r][c1] != EMPTY:
                    return False
            return True
        else:
            return False

    def is_legal_move(self, r1, c1, r2, c2, me):
        opp = BLACK if me == WHITE else WHITE
        # 1. In‑bounds
        if not (self.in_bounds(r1, c1) and self.in_bounds(r2, c2)):
            return False
        # 2. Must be moving your own piece to an empty square
        if self.board[r1][c1] != me or self.board[r2][c2] != EMPTY:
            return False
        # 3. Must move along row or column, and actually move
        if not ((r1 == r2 and c1 != c2) or (c1 == c2 and r1 != r2)):
            return False
        # 4. Path must be clear
        if not self.is_clear_path(r1, c1, r2, c2):
            return False
        # 5. No suicide, except when capturing
        for dr, dc in DIRECTIONS:
            r_pos, c_pos = r2 + dr, c2 + dc
            r_neg, c_neg = r2 - dr, c2 - dc
            if (self.in_bounds(r_pos, c_pos) and self.in_bounds(r_neg, c_neg) and
                self.board[r_pos][c_pos] == opp and self.board[r_neg][c_neg] == opp):
                
                boardCopy = copy.deepcopy(self.board)
                total = 0
                for dr1, dc1 in DIRECTIONS:
                    total += self.capture_from(r2, c2, dr1, dc1, me, opp)
                total += self.remove_dead_groups(opp)
                self.board = copy.deepcopy(boardCopy)
                if total == 0:
                    return False
        return True
    
    def capture_from(self, r0, c0, dr, dc, me, opp):
        r, c = r0 + dr, c0 + dc
        captured = []
        while self.in_bounds(r, c) and self.board[r][c] == opp:
            captured.append((r, c))
            r += dr; c += dc
        if self.in_bounds(r, c) and self.board[r][c] == me and captured:
            for rr, cc in captured:
                self.board[rr][cc] = EMPTY
            return len(captured)
        return 0

    def remove_dead_groups(self, color):
        # Go-like capture: any connected group of 'color' with no liberties
        visited = set()
        dead = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if (r, c) not in visited and self.board[r][c] == color:
                    # BFS to find the group
                    queue = [(r, c)]
                    group = [(r, c)]
                    visited.add((r, c))
                    has_liberty = False
                    while queue:
                        cr, cc = queue.pop()
                        for dr, dc in DIRECTIONS:
                            nr, nc = cr + dr, cc + dc
                            if self.in_bounds(nr, nc):
                                if self.board[nr][nc] == EMPTY:
                                    has_liberty = True
                                elif self.board[nr][nc] == color and (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    queue.append((nr, nc))
                                    group.append((nr, nc))
                    if not has_liberty:
                        dead.extend(group)
        # remove dead and return count
        for (dr, dc) in dead:
            self.board[dr][dc] = EMPTY
        return len(dead)
    
    def generate_legal_moves(self, me):
        """
        Generate all legal sliding moves for player 'me'.
        Returns a list of tuples (r1, c1, r2, c2).
        """
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == me:
                    for dr, dc in DIRECTIONS:
                        nr, nc = r + dr, c + dc
                        while self.in_bounds(nr, nc) and self.board[nr][nc] == EMPTY:
                            if self.is_legal_move(r, c, nr, nc, me):
                                moves.append((r, c, nr, nc))
                            nr += dr; nc += dc
        return moves

    def apply_move(self, r1, c1, r2, c2, me):
        opp = BLACK if me == WHITE else WHITE
        if not self.is_legal_move(r1, c1, r2, c2, me):
            raise ValueError(f"Illegal move: from ({r1},{c1}) to ({r2},{c2})")
        # perform slide
        self.board[r1][c1] = EMPTY
        self.board[r2][c2] = me
        # track captures
        total = 0
        for dr, dc in DIRECTIONS:
            total += self.capture_from(r2, c2, dr, dc, me, opp)
            #print(self.serialize())
        total += self.remove_dead_groups(opp)
        #print(self.serialize())
        self.captures[me] += total
        
        # update pending_leader in case of leading 3 captures
        cm, co = self.captures[me], self.captures[opp]
        lead = cm - co
        if lead >= 3 and self.pending_leader == None:
            self.pending_leader = me
        elif lead >= -2 and self.pending_leader == opp:
            self.pending_leader = None

        # record last mover
        self.last_move = (r1,c1,r2,c2)
        self.turn = opp

    def is_game_over(self):
        # player to play next
        opp = self.turn
        # player who just moved
        me = BLACK if opp == WHITE else WHITE
        cm = self.captures[me]
        # 1. First to 5 captures
        if cm >= 5:
            return me
        elif self.pending_leader is opp:
            return self.pending_leader
        return None