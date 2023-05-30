#!/usr/bin/python3.6
import discord
import math
import random
import logging
import json
from datetime import datetime,timedelta
import asyncio

logging.basicConfig(level=logging.INFO)

TOKEN = 'INSERT TOKEN HERE'
userGames = []

def generateGrid(x,y,mines):
    grid = []
    for i in range(x):
        grid.append([0] * y)
    grid = generateMines(grid,mines)
    return grid

def generateMines(grid, mines):
    for x in range(mines):
        num1 = math.floor(random.random() * len(grid))
        num2 = math.floor(random.random() * len(grid[0]))
        while grid[num1][num2] != 0:
            num1 = math.floor(random.random() * len(grid))
            num2 = math.floor(random.random() * len(grid[0]))
        grid[num1][num2] = 1
    return grid

def displayGrid(grid):
    string = ""
    for x in range(len(grid)):
        for y in range(len(grid[x])):
            if grid[x][y] == 0 or grid[x][y] == 1:
                string += ":blue_square:"
            #elif grid[x][y] == 1:
             #   string += ":red_circle:"
            elif grid[x][y] == 2:
                adjacent = countAdjacent(grid,x,y)
                if adjacent == 0:
                    string += ":green_square:"
                elif adjacent == 1:
                    string += ":one:"
                elif adjacent == 2:
                    string += ":two:"
                elif adjacent == 3:
                    string += ":three:"
                elif adjacent == 4:
                    string += ":four:"
                elif adjacent == 5:
                    string += ":five:"
                elif adjacent == 6:
                    string += ":six:"
                elif adjacent == 7:
                    string+=":seven:"
                else:
                    string+=":eight:"
            elif grid[x][y] == 3 or grid[x][y] == 5:
                #string += ":triangular_flag_on_post:"
                string += ":flag_white:"
            elif grid[x][y] == 4:
                string += ":fire:"
            elif grid[x][y] == 6:
                string+=":x:"
            elif grid[x][y] == 7:
                string+=":bomb:"
            elif grid[x][y] == 8:
                string+=":flag_white:"
        string += "\n"
    return(string)      

client = discord.Client()

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith('/'):
        msg = message.content[1:].lower()
        args = msg.split()
        command = args[0]
        del args[0]

        if command == 'help':
            embed = discord.Embed(color=0x4A769A)
            embed.add_field(name="Minesweeper bot guide", value="""Use the command `/minesweeper` to start a new game. You can use optional parameters for the grid size and number of mines, e.g. `/minesweeper 6x7 10`.\n\nUpon starting a new game, you will be given a grid of blue squares. You can uncover squares by typing in coordinates separated by a space, e.g. `5 4`. If there are mines in any of the 8 squares surrounding a given square, it will show a number indicating the number of mines it is adjacent to, otherwise it will turn green. The goal of the game is to place a flag on each square containing a mine, but you will only have as many flags as the number of mines present, so if you fail to place them all correctly, or accidentally step on a mine, it's game over.""", inline=False)
            embed.add_field(name="Example grid", value=""":green_square::green_square::green_square:\n:one::one::one:\n:one::blue_square::one:\n\nIn the grid shown above, all the squares have been revealed except for one, and based on the placement of the numbers, this must be where the mine is located. This square has the coordinates `3 2`, so all that needs to be done to win this game is to do `flag 3 2`.""", inline=False)
            await message.channel.send(embed=embed)

        if command == 'minesweeper':
            if message.author.id in userGames:
                embed = discord.Embed(color=0x4A769A)
                embed.add_field(name="You already have a game in progress!", value="Use `quit` to exit the current game before beginning a new one")
                await message.channel.send(embed=embed)
                return
            if args != []:
                custominput = handleCustomInput(args)
                if custominput == None:
                    embed = discord.Embed(color=0x4A769A)
                    embed.add_field(name="Invalid input", value="""To create a custom game, enter a grid size in the format `numberxnumber` and/or a number of mines as a single digit. If you're using both optional parameters, the grid size must come first.\n\nThe numbers for grid size must also be between 3 and 12, and the number of mines must not be greater than or equal to the number of tiles on your grid.""")
                    return await message.channel.send(embed=embed)
                elif len(custominput) == 3:
                    GRIDX = custominput[0]
                    GRIDY = custominput[1]
                    NUM_MINES = custominput[2]
                elif len(custominput) == 2:
                    GRIDX = custominput[0]
                    GRIDY = custominput[1]
                    NUM_MINES = 5
                else:
                    NUM_MINES = custominput[0]
                    GRIDX = 8
                    GRIDY = 8
            else:   
                NUM_MINES = 5
                GRIDX = 8
                GRIDY = 8
            userGames.append(message.author.id)
            game = generateGrid(GRIDX,GRIDY,NUM_MINES)
            await message.channel.send(embed=generateEmbed(game))
            #first move - initialise game
            uinput = False
            while uinput == False:
                def pred(m):
                    return m.author == message.author and m.channel == message.channel
                msg = await client.wait_for('message', check=pred)
                if msg:
                    if msg.content.lower().startswith("quit") or msg.content.lower().startswith("exit"):
                        await message.channel.send(embed=generateEmbed(game, None, True, False, True))
                        userGames.remove(message.author.id)
                        return
                    try:
                        x,y = handleInput(game,msg.content.split())
                    except:
                        embed = discord.Embed(color=0x4A769A)
                        embed.add_field(name="Invalid input", value="Enter two coordinates separated by a space, e.g. `2 3`, or quit the game with `quit`.")
                        await message.channel.send(embed=embed)
                        continue
                    while game[x][y] != 0:
                        game = generateGrid(GRIDX,GRIDY,NUM_MINES)
                    game[x][y] = 2
                    game = revealSquares(game,x,y)
                    uinput = True
            gameOver = False
            gameWon = False
            uinput = False
            forceQuit = False
            flags = NUM_MINES
            await message.channel.send(embed=generateEmbed(game,flags))
            while gameOver == False:
                while uinput == False:
                    def pred(m):
                        return m.author == message.author and m.channel == message.channel
                    msg = await client.wait_for('message', check=pred)
                    if msg:
                        inputlist = msg.content.lower().split()
                        if inputlist[0] == "quit" or inputlist[0] == "exit":
                            gameOver = True
                            forceQuit = True
                            uinput = True
                            userGames.remove(message.author.id)
                        if inputlist[0] == "flag":
                            inputlist.pop(0)
                            try:
                                x,y = handleInput(game,inputlist)
                            except:
                                embed = discord.Embed(color=0x4A769A)
                                embed.add_field(name="Invalid input", value="Place a flag on a square by starting your message with `flag` followed by two coordinates, e.g. `flag 4 2`.")
                                await message.channel.send(embed=embed)
                                continue
                            if game[x][y] == 1:
                                game[x][y] = 3
                                flags-=1
                            elif game[x][y] == 3:
                                game[x][y] = 1
                                flags+=1
                            elif game[x][y] == 5:
                                game[x][y] = 0
                                flags+=1
                            elif game[x][y] == 0:
                                game[x][y] = 5
                                flags-=1
                            elif game[x][y] == 8:
                                game[x][y] = 2
                                flags+=1
                            elif game[x][y] == 2:
                                game[x][y] = 8
                                flags-=1
                            if checkForWin(game, NUM_MINES) == True:
                                gameOver = True
                                gameWon = True
                            if flags == 0:
                                gameOver = True
                            uinput = True
                        if uinput == False:     
                            try:
                                x,y = handleInput(game,inputlist)
                            except:
                                embed = discord.Embed(color=0x4A769A)
                                embed.add_field(name="Invalid input", value="Enter two coordinates separated by a space, e.g. `2 3`, or place a flag on a square by starting your message with `flag` followed by two coordinates, e.g. `flag 4 2`.")
                                await message.channel.send(embed=embed)
                                continue
                            if game[x][y] == 0:
                                game[x][y] = 2
                                game = revealSquares(game,x,y)
                                uinput = True
                            elif game[x][y] == 1:
                                game[x][y] = 4
                                uinput = True
                                gameOver = True
                            else:
                                embed = discord.Embed(color=0x4A769A)
                                embed.add_field(name="Invalid input", value="You can't uncover a square that has already been uncovered or flagged.")
                                await message.channel.send(embed=embed)
                                continue
                        if uinput == True:
                            if gameOver == False:
                                await message.channel.send(embed=generateEmbed(game, flags, gameOver, gameWon, forceQuit))
                                uinput = False
                            else:
                                game = showMines(game)
                                await message.channel.send(embed=generateEmbed(game, flags, gameOver, gameWon, forceQuit))
                                userGames.remove(message.author.id)
                        else:
                            continue
                                                   

def generateEmbed(grid, flags=None, gameOver=False, gameWon=False, forceQuit=False):
    embed = discord.Embed(title="Playing a game of Minesweeper!", description=displayGrid(grid), color=0x4A769A)
    if gameOver == False:
        if flags==None:
            embed.add_field(name="Uncover a square!", value="Use two coordinates to reveal a square, e.g. `2 3` is the square second from the top and three from the left.", inline=False)
        else:
            embed.add_field(name="Flags remaining: " + str(flags), value="Reveal another square, or add `flag` to the beginning of your message to place a flag on the given square (or remove it if there's already a flag there). You can also end the game with `quit`.", inline=False)
    else:
        if forceQuit == True:
            embed.add_field(name="Game over!", value="You gave up. Guess those mines are just going to stay there forever.", inline=False)
        elif gameWon == False:
            if flags > 0:
                embed.add_field(name="You stepped on a mine!", value="You lose the game.", inline=False)
            else:
                embed.add_field(name="You failed to flag all the mines correctly!", value="You lose the game.", inline=False)
        else:
            embed.add_field(name="You flagged all the mines successfully!", value="You win!", inline=False)
    return embed

def handleInput(grid, i):
    if len(i) != 2:
        return None
    try:
        x = int(i[0])
        y = int(i[1])
    except ValueError:
        return None
    if x < 1 or x > len(grid) or y < 1 or y > len(grid[0]):
        return None
    x-=1
    y-=1
    return x,y

def handleCustomInput(i):
    if len(i) == 2:
        try:
            gsize = i[0].split('x')
            gx = int(gsize[0])
            gy = int(gsize[1])
        except:
            return None
        try:
            mines = int(i[1])
        except:
            return None
        if gx < 3 or gx > 12 or gy < 3 or gy > 12 or mines >= gx*gy or mines < 1:
            return None
        return [gx,gy,mines]
    elif len(i) == 1:
        try:
            mines = int(i[0])
        except:
            try:
                gsize = i[0].split('x')
                gx = int(gsize[0])
                gy = int(gsize[1])
            except:
                return None
            if gx < 3 or gx > 12 or gy < 3 or gy > 12:
                return None
            return [gx,gy]
        if mines >= 64 or mines < 1:
            return None
        return [mines]
                  
                            
def convertAdjacent(grid,x,y):
    clear = []
    for a in range(x-1,x+2):
        if a < 0 or a > len(grid)-1:
            continue
        for b in range(y-1,y+2):
            if b < 0 or b > len(grid[0])-1:
                continue
            if grid[a][b] == 0:
                grid[a][b] = 2
                if countAdjacent(grid,a,b) == 0:
                    clear.append([a,b])
    return grid, clear

def revealSquares(grid,x,y):
    if countAdjacent(grid,x,y) != 0:
        grid[x][y] = 2
        return grid
    newgrid, check = convertAdjacent(grid,x,y)
    while check != []:
        for a in check:
            newgrid,check2 = convertAdjacent(newgrid,a[0],a[1])
            check.remove(a)
            if check2 == []:
                continue
            for b in check2:
                check.append(b)
    return newgrid  

def countAdjacent(grid,x,y):
    adjacent = 0
    for a in range(x-1,x+2):
        if a < 0 or a > len(grid)-1:
            continue
        for b in range(y-1,y+2):
            if b < 0 or b > len(grid[0])-1:
                continue
            if grid[a][b] == 1 or grid[a][b] == 3 or grid[a][b] == 7 or grid[a][b] == 4:
                adjacent+=1
    return adjacent

def checkForWin(grid, mines):
    flagCount = 0
    for x in grid:
        for y in x:
            if y == 3:
                flagCount+=1
    if flagCount == mines:
        return True
    else:
        return False

def showMines(grid):
    for x in range(len(grid)):
        for y in range(len(grid[x])):
            if grid[x][y] == 1:
                grid[x][y] = 7
            elif grid[x][y] == 5:
                grid[x][y] = 6
    return grid
                    
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(activity=discord.Game(name="/minesweeper"))
    
client.run(TOKEN, bot=True, reconnect=True)
