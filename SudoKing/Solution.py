def parse_input():
    grid = []
    for _ in range(13):
        line = input().strip()
        if line.startswith("+"):
            continue
        row = [c for c in line if c.isdigit() or c == '.']
        grid.append([int(c) if c != '.' else 0 for c in row])
    return grid

def is_valid(grid, r, c, num):
    if num in grid[r]:
        return False
    for i in range(9):
        if grid[i][c] == num:
            return False
    sr, sc = (r // 3) * 3, (c // 3) * 3
    for i in range(sr, sr + 3):
        for j in range(sc, sc + 3):
            if grid[i][j] == num:
                return False
    return True

def solve(grid):
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                for num in range(1, 10):
                    if is_valid(grid, r, c, num):
                        grid[r][c] = num
                        if solve(grid):
                            return True
                        grid[r][c] = 0
                return False
    return True

def print_grid(grid):
    for i in range(9):
        if i % 3 == 0:
            print("+-------+-------+-------+")
        row = []
        for j in range(9):
            if j % 3 == 0:
                row.append("|")
            row.append(str(grid[i][j]))
        row.append("|")
        print(" ".join(row))
    print("+-------+-------+-------+")

grid = parse_input()
solve(grid)
print_grid(grid)