from discord_bot import DiscordBotManager
import threading
# from gameUI import *
# from comboKeys import *
from jobs.MapleJob import MapleJob
from jobs.ExpMages import IL


class App:
    def __init__(self, CharacterJob, map_name, cor=False, using_booster=False, always_using_booster=False, rune_cd=900):
        # Start the Discord bot immediately (it stays alive and listens for commands)
        self.CharacterJob = CharacterJob
        self.map_name = map_name
        self.cor = cor
        self.using_booster = using_booster
        self.always_using_booster = always_using_booster
        self.dcbot = DiscordBotManager()
        self.dcbot.start_bot()
        self.character = None
        self.rune_cd = rune_cd

    def initiate_character(self):
        self.character = self.CharacterJob(self.map_name)
        self.character.cor = self.cor
        self.character.using_booster = self.using_booster
        self.character.always_using_booster = self.always_using_booster

    def main(self):
        """Main controller entrypoint.

        This is what the Discord bot starts/stops via !start_main / !stop_main.
        """
        if self.character is None:
            raise RuntimeError("Character not initialized. Call initiate_character(...) before starting.")

        self.dcbot.grind_stop_event.clear()
        self.character.loop(self.rune_cd, self.dcbot, self.dcbot.grind_stop_event)

    def register_with_bot(self):
        """Register this controller with the Discord bot so it can be started/stopped."""
        self.dcbot.set_initiate_character_fn(self.initiate_character)
        self.dcbot.set_grind_fn(self.main)


if __name__ == '__main__':
    # map_name = "Top Deck Passage 6"
    map_name = "Sunken Ruins 4"
    CharacterJob = IL
    cor = False  # chains of resentment
    using_booster = True
    always_using_booster = False
    rune_cd = 900

    app = App(CharacterJob, map_name, cor, using_booster, always_using_booster, rune_cd)
    # if using_booster:
    #     app.character.using_booster = using_booster
    # Register the controller so the Discord bot can control it:
    #   !start  -> starts controller_main in a background thread
    #   !stop   -> signals it to stop
    app.register_with_bot()
    app.dcbot.prepare_for_grind()
    app.dcbot.start_grind()

    # Keep the process alive while the bot runs.
    app.dcbot.bot_thread.join()

    # character = IL(map_name)
    # app.initiate_character()
    # app.main()


    # Keep the process alive while the bot runs.
