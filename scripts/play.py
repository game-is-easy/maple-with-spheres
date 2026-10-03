from scripts.jobs.ExpMages import IL, Bishop


class App:
    def __init__(self, CharacterJob, map_name, cor=False, using_booster=False, always_using_booster=False, silence_mode=False, auto_active_dc_window=False, use_dc=True, rune_cd=900, cor_mode=False):
        # Start the Discord bot immediately (it stays alive and listens for commands)
        self.CharacterJob = CharacterJob
        self.map_name = map_name if not cor_mode else ""
        self.cor = cor
        self.using_booster = using_booster
        self.always_using_booster = always_using_booster
        self.silence_mode = silence_mode
        self.auto_active_dc_window = auto_active_dc_window
        self.character = None
        self.rune_cd = rune_cd
        self.cor_mode = cor_mode

        if use_dc:
            from scripts.discord_bot import DiscordBotManager

            self.dcbot = DiscordBotManager()
            self.dcbot.start_bot()

            self.register_with_bot()
            self.dcbot.prepare_for_grind()
            self.dcbot.start_grind()
            self.dcbot.bot_thread.join()
        else:
            self.initiate_character()
            self.character.loop(self.rune_cd)

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

    def main_cor(self):
        if self.character is None:
            raise RuntimeError("Character not initialized. Call initiate_character(...) before starting.")
        self.dcbot.grind_stop_event.clear()
        self.character.cor_mode(dcbot=self.dcbot, stop_event=self.dcbot.grind_stop_event)

    def register_with_bot(self):
        """Register this controller with the Discord bot so it can be started/stopped."""
        self.dcbot.set_initiate_character_fn(self.initiate_character)
        if self.cor_mode:
            self.dcbot.set_grind_fn(self.main_cor)
        else:
            self.dcbot.set_grind_fn(self.main)


if __name__ == '__main__':
    import os
    if "PYCHARM_HOSTED" in os.environ:
        # map_name = "Star-Swallowing Sea 1"
        # map_name = "End of the World 1-4"
        # map_name = "Blooming Spring 1"
        # map_name = "Top Deck Passage 6"
        # map_name = "Sunken Ruins 4"
        map_name = "Fate-Fields of Eternity 3"
        CharacterJob = IL
        # map_name = "Silent Ashlands 1"
        # CharacterJob = Bishop
        options = {
            "cor": True,  # chains of resentment
            "using_booster": True,
            # "always_using_booster": True,
            # "silence_mode": True,
            "auto_active_dc_window": True,
            # "use_dc": False,
            "rune_cd": 900,
            # "cor_mode": True
        }
    else:
        import argparse
        import sys

        sys.path.append(".")
        ap = argparse.ArgumentParser(description="start bot")
        ap.add_argument("job")
        ap.add_argument("-m", "--map_name")
        ap.add_argument("-c", "--cor", action="store_true")
        ap.add_argument("-b", "--using_booster", action="store_true")
        ap.add_argument("-B", "--always_using_booster", action="store_true")
        ap.add_argument("-s", "--silence_level", action="count", default=0)
        ap.add_argument("-a", "--auto_active_dc_window", action="store_true")
        ap.add_argument("-l", "--local", action="store_true")
        ap.add_argument("-r", "--rune_cd", type=int, default=900)
        ap.add_argument("-C", "--cor_mode", action="store_true")
        args = ap.parse_args()

        job_map = {"IL": IL, "Bishop": Bishop}
        map_map = {"IL": "Fate-Fields of Eternity 3", "Bishop": "Sunken Ruins 4"}
        CharacterJob = job_map[args.job]
        map_name = args.map_name or map_map[args.job]
        options = {
            "cor": args.cor,  # chains of resentment
            "using_booster": args.using_booster,
            "always_using_booster": args.always_using_booster,
            "silence_mode": args.silence_level >= 1,
            "auto_active_dc_window": args.silence_level < 2,
            "use_dc": not args.local,
            "rune_cd": args.rune_cd,
            "cor_mode": args.cor_mode
        }

    app = App(CharacterJob, map_name, **options)
    # app.register_with_bot()
    # app.dcbot.prepare_for_grind()
    # app.dcbot.start_grind()
    #
    # # Keep the process alive while the bot runs.
    # app.dcbot.bot_thread.join()
