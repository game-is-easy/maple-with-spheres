from discord_bot import DiscordBotManager
# from gameUI import *
# from comboKeys import *
from jobs.MapleJob import MapleJob
from jobs.ExpMages import IL


class Controller:
    def __init__(self, rune_cd=900):
        self.dcbot = DiscordBotManager()
        self.dcbot.start_bot()
        self.character = None
        self.rune_cd = rune_cd

    def initiate_character(self, character: 'MapleJob'):
        self.character = character

    def loop(self):
        self.character.loop(self.rune_cd, self.dcbot)


if __name__ == '__main__':
    # map_name = "Top Deck Passage 6"
    map_name = "Sunken Ruins 4"
    rune_cd = 900

    controller = Controller(rune_cd)
    character = IL(map_name)
    character.cor = True
    controller.initiate_character(character)
    controller.loop()
