from discord_bot import DiscordBotManager
from jobs.ExpMages import IL, Bishop


class App:
    def __init__(self, CharacterJob, map_name, cor=False, using_booster=False, always_using_booster=False, silence_mode=False, auto_active_dc_window=False, rune_cd=900):
        # Start the Discord bot immediately (it stays alive and listens for commands)
        self.CharacterJob = CharacterJob
        self.map_name = map_name
        self.cor = cor
        self.using_booster = using_booster
        self.always_using_booster = always_using_booster
        self.silence_mode = silence_mode
        self.auto_active_dc_window = auto_active_dc_window
        self.dcbot = DiscordBotManager()
        self.dcbot.start_bot()
        self.character = None
        self.rune_cd = rune_cd

    def initiate_character(self):
        self.character = self.CharacterJob(self.map_name)
        self.character.cor = self.cor
        self.character.using_booster = self.using_booster
        self.character.always_using_booster = self.always_using_booster
        self.character.silence_mode = self.silence_mode
        self.character.auto_active_dc_window = self.auto_active_dc_window

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
    # map_name = "Star-Swallowing Sea 1"
    # map_name = "End of the World 1-4"
    # map_name = "Top Deck Passage 6"
    # map_name = "Sunken Ruins 4"
    map_name = "Silent Ashlands 1"
    CharacterJob = IL
    # map_name = "Blooming Spring 1"
    # CharacterJob = Bishop
    options = {
        # "cor": True,  # chains of resentment
        "using_booster": True,
        # "always_using_booster": True,
        # "silence_mode": True,
        "auto_active_dc_window": True,
        "rune_cd": 600
    }
    app = App(CharacterJob, map_name, **options)
    app.register_with_bot()
    app.dcbot.prepare_for_grind()
    app.dcbot.start_grind()

    # Keep the process alive while the bot runs.
    app.dcbot.bot_thread.join()
