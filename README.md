# Spyfall (for LINE)
After having created a Tic-Tac-Toe Bot for LINE, 
I decided to continue my efforts by recreating the game Spyfall as a bot on LINE.

## how it works
After you add the bot to a LINE group, you first join the game by typing 'join'.
<p align="center"><img src=images/join.jpeg alt="join game" width=500></p>
Once everyone's joined, the bot messages your role and location to you directly.
<p align="center"><img src=images/role.jpeg alt="role message" width=500></p>
From there you just vote for the player you think is the spy.
If the spy was found, they can still win by guess the location correctly.
<p align="center"><img src=images/win.jpeg alt="win message" width=500></p>
Play till one of the win conditions is met, then the bot will automatically leave.

## other features
Different from the actual game, I've added secret locations (secrets.txt) that can be added
as a potential location using a secret word

I also added a developer mode, where you can add new locations to the secrets.txt file and
also delete locations that you've added.

You can add the bot as a LINE friend and start playing by scanning the QR Code below!
<p align="center"><img src=images/spyfall_qr_code.png alt="QR Code" width=500></p>