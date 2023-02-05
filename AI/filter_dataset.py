'''
used to filter out un-needed data and unwanted games from the all_chess_games.txt
and create chess_moves.txt which is what I will use to train the AI

chess_moves.txt is formatted like so:

winner,moves...
W,W1.d4,B1.d5,W2.c4,B2.e6,W3.Nc3,B3.Nf6,W4.cxd5,B4.exd5,W5.Bg5,B5.Be7,W6.e3,B6.Ne4,W7.Bxe7,B7.Nxc3,W8.Bxd8,B8.Nxd1,W9.Bxc7,B9.Nxb2,W10.Rb1,B10.Nc4,W11.Bxc4,B11.dxc4,W12.Ne2,B12.O-O,W13.Nc3,B13.b6,W14.d5,B14.Na6,W15.Bd6,B15.Rd8,W16.Ba3,B16.Bb7,W17.e4,B17.f6,W18.Ke2,B18.Nc7,W19.Rhd1,B19.Ba6,W20.Ke3,B20.Kf7,W21.g4,B21.g5,W22.h4,B22.h6,W23.Rh1,B23.Re8,W24.f3,B24.Bb7,W25.hxg5,B25.fxg5,W26.d6,B26.Nd5+,W27.Nxd5,B27.Bxd5,W28.Rxh6,B28.c3,W29.d7,B29.Re6,W30.Rh7+,B30.Kg8,W31.Rbh1,B31.Bc6,W32.Rh8+,B32.Kf7,W33.Rxa8,B33.Bxd7,W34.Rh7+

winner can be: B (Black), W (White), D (Draw)

King = K, Queen = Q, Bishop = B, Knight = N, Rook = R, Pawn = no notation.
Capturing an enemy piece sees an "x" placed between the piece moved and the square the captured piece was upon.
When the opponent’s king is threatened by check, a "+" sign is added to the end of the notation.
Castling kingside is written as "O-O". Castling queenside is notated with "O-O-O"
https://www.ichess.net/blog/chess-notation/
'''

counter = 0
with open("chess_moves.txt", "a") as fileW:
    fileW.write("winner,moves...\n")

with open("all_chess_games.txt", 'r') as file:
    next(file)
    next(file)
    next(file)
    next(file)
    next(file)
    # 1.t 2.date 3.result 4.welo 5.belo 6.len 7.date_c 8.resu_c 9.welo_c 10.belo_c 11.edate_c 12.setup 13.fen 14.resu2_c 15.oyrange 16.bad_len 17.game...
    for i in file.readlines():
        line = i.split(" ")
        
        if line[11] == "setup_true": continue

        to_write = ""
        
        if line[2] == "1/2-1/2":   #draw
            to_write += "D" + ","
        
        elif line[2] == "1-0":  #white
            to_write += "W" + ","
        
        elif line[2] == "0-1":  #black
            to_write += "B" + ","
        
        for eh in line[17:]:
            to_write += eh + ","
        
        to_write = to_write[:-3] + "\n"
        
        if len(to_write) < 30: continue
        
        with open("chess_moves.txt", "a") as fileW:
            fileW.write(to_write)
            counter += 1

print(f"wrote {counter} games")
#this resulted in 3,515,301 games
