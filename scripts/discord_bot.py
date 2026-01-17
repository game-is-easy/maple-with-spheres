import discord
from discord.ext import commands, tasks
import asyncio
import ssl
import certifi
from pynput import keyboard
import threading
import os
from locate_im import screencapture
from comboKeys import short_press, hold, PRL, exec_key_sequence
from gameUI import get_window_region

# Create SSL context with proper certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())


class DiscordBotManager:
    def __init__(self, token_path="../resources/token.txt"):
        self.token_path = token_path
        self.bot = None
        self.tasks = None
        self.bot_thread = None
        self.main_loop = None

        # For grinder/main loop management
        self.grind_thread = None
        self.grind_stop_event = threading.Event()
        self.grind_fn = None  # callable(stop_event) -> None
        self.initiate_character_fn = None

        # Global variables for the wait function
        self.waiting_for_reply = False
        self.reply_received = None
        self.key_pressed = None
        # self.target_user_id = None
        self.target_user_id = 304671527784284160
        self.target_user = None
        self.channel_id = 1405982674224681000
        self.channel = None
        self.rune_arrow_data = ''

        self._setup_bot()

    def _setup_bot(self):
        """Initialize the Discord bot"""
        with open(self.token_path, 'r') as f:
            self.bot_token = f.readlines()[0].strip()

        # Bot setup with intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.bot = commands.Bot(command_prefix='!', intents=intents)
        # self.tasks = tasks.

        # Set up event handlers
        @self.bot.event
        async def on_ready():
            print(f'{self.bot.user} has connected to Discord!')
            self.channel = await self.bot.fetch_channel(self.channel_id)
            self.target_user = await self.bot.fetch_user(self.target_user_id)

        @self.bot.event
        async def on_message(message):
            # Don't respond to own messages
            if message.author == self.bot.user:
                return

            # Check if we're waiting for a reply from the target user
            if (self.waiting_for_reply and
                    message.author.id == self.target_user_id and
                    isinstance(message.channel, discord.DMChannel)):
                print(
                    f"Received DM reply: '{message.content}' from {message.author}")
                self.reply_received = message.content
                self.waiting_for_reply = False

            # Process other bot commands
            await self.bot.process_commands(message)

        @self.bot.command(name="see", )
        async def send_screenshot(ctx):
            """
            See real-time in-game screenshot
            """
            tmp_filename = "../temp/gamescreen.png"
            screencapture(tmp_filename, region=get_window_region())
            with open(tmp_filename, 'rb') as f:
                picture = discord.File(f)
                if ctx.guild is None:
                    await self.target_user.send(file=picture)
                else:
                    await self.channel.send(file=picture)
            os.unlink(tmp_filename)

        @self.bot.command(name="press")
        # @discord.app_commands.describe(key_name="name of key on keyboard, e.g. z, return, etc.")
        async def send_short_press(ctx, key_name: str):
            """
            Press a key for a short duration (~0.1 s), e.g. `!press z`, `!press esc`
            :param key_name: name of key on keyboard, e.g. "a", "return", etc.
            """
            if PRL.get(key_name.upper()):
                short_press(PRL[key_name.upper()])
            else:
                message = f'No key with name "{key_name.upper()}".'
                if ctx.guild is None:
                    await self.target_user.send(message)
                else:
                    await self.channel.send(message)

        @self.bot.command(name="hold")
        # @discord.app_commands.describe(
        #     key_name="name of key on keyboard, e.g. z, return",
        #     duration="number in seconds, e.g. 4, 1.5"
        # )
        async def send_key_hold(ctx, key_name: str, duration: float):
            """
            Hold a key for some duration in seconds, e.g. `!hold shift 5`
            :param key_name: name of key on keyboard, e.g. "a", "return", etc.
            :param duration: number in seconds, e.g. 4, 1.5
            """
            if PRL.get(key_name.upper()):
                hold(PRL[key_name.upper()], duration)
            else:
                message = f'No key with name "{key_name.upper()}".'
                if ctx.guild is None:
                    await self.target_user.send(message)
                else:
                    await self.channel.send(message)

        @self.bot.command(name="town")
        # @discord.app_commands.describe(key_town_name="TO TOWN key name")
        async def to_town(ctx, key_town_name: str = 'J'):
            """
            Return back to town (default TO TOWN key: J), e.g. `!town`, `!town f10`
            """
            seq = short_press(PRL[key_town_name], delay_after_rep=10, execute=False)
            seq.extend(short_press(PRL["ENTER"], delay_after_rep=20, execute=False))
            exec_key_sequence(seq)
            await send_screenshot(ctx)

        @self.bot.command(name="initiate")
        async def initiate_grind(ctx):
            try:
                ready = self.prepare_for_grind()
                msg = "ready for grind." if ready else "not ready."
            except Exception as e:
                msg = f"Failed to initiate: {e}"

            if ctx.guild is None:
                await self.target_user.send(msg)
            else:
                await self.channel.send(msg)

        @self.bot.command(name="start")
        async def start_grind(ctx):
            try:
                started = self.start_grind()
                msg = "grind started." if started else "already grinding."
            except Exception as e:
                msg = f"Failed to start grind: {e}"

            if ctx.guild is None:
                await self.target_user.send(msg)
            else:
                await self.channel.send(msg)

        @self.bot.command(name="stop")
        async def stop_grind(ctx):
            stopped = self.stop_grind()
            msg = "Stop signal sent to grind function." if stopped else "not grinding."

            if ctx.guild is None:
                await self.target_user.send(msg)
            else:
                await self.channel.send(msg)

        @self.bot.command(name="list")
        async def list_prompt(ctx):
            commands_description = [
                ("see", "get real-time in-game screenshot, e.g. `!see`"),
                ("press", "press a key, e.g. `!press z`, `!press esc`"),
                ("hold", "hold a key for some duration in seconds, e.g. `!hold shift 5`"),
                ("town", "return back to town (default TO TOWN key: J), e.g. `!town`, `!town f10`"),
                ("initiate", "set/refresh job, minimap location, etc., e.g. `!initiate`"),
                ("start", "start rotation, e.g. `!start`"),
                ("stop", "stop rotation (expect some delay), e.g. `!stop`")
            ]
            msg = ['\n'.join(f"`!{desc[0]}`: {desc[1]}") for desc in commands_description]

            if ctx.guild is None:
                await self.target_user.send(msg)
            else:
                await self.channel.send(msg)

    def start_bot(self):
        """Start the Discord bot in a background thread"""
        if self.bot_thread is not None and self.bot_thread.is_alive():
            print("Bot is already running!")
            return

        def bot_runner():
            """Run the Discord bot"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.main_loop = loop
            loop.run_until_complete(self.bot.start(self.bot_token))

        self.bot_thread = threading.Thread(target=bot_runner, daemon=False)
        self.bot_thread.start()

        print("Bot starting in background...")
        # time.sleep(3)  # Give bot time to start
        #
        # # Wait for bot to be ready
        # while not self.bot.is_ready():
        #     time.sleep(0.1)
        #
        # print("Bot is ready!")

    def stop_bot(self):
        """Stop the Discord bot"""
        if self.bot and not self.bot.is_closed():
            # Schedule the bot closure on its event loop
            if self.main_loop and not self.main_loop.is_closed():
                asyncio.run_coroutine_threadsafe(self.bot.close(),
                                                 self.main_loop)

    def is_ready(self):
        """Check if the bot is ready"""
        return self.bot and self.bot.is_ready()

    def set_grind_fn(self, grind_fn):
        """Register the main grind function.

        grind_fn must be a callable that accepts a single argument: stop_event (threading.Event).
        It should run until stop_event.is_set() becomes True.
        """
        self.grind_fn = grind_fn

    def set_initiate_character_fn(self, initiate_character_fn):
        self.initiate_character_fn = initiate_character_fn

    def prepare_for_grind(self):
        if self.initiate_character_fn is None:
            raise RuntimeError("No initiate character function registered.")
        try:
            self.initiate_character_fn()
        except Exception as e:
            print(f"initiate character function Error: {e}")
            return False

        if self.grind_fn is None:
            raise RuntimeError("No grinder registered. Call set_grind_fn(grind_fn) first.")

        # def _runner():
        #     try:
        #         self.grind_fn()
        #     except Exception as e:
        #         print(f"grind function crashed: {e}")
        #
        # self.grind_thread = threading.Thread(target=_runner, daemon=False)
        return True

    def start_grind(self):
        """Start the registered grinder in a background thread."""
        # if self.grind_fn is None:
        #     raise RuntimeError("No grinder registered. Call set_grind_fn(grind_fn) first.")

        if self.grind_thread is not None and self.grind_thread.is_alive():
            print("need initialize!")
            return False

        # Reset stop flag and start grind
        self.grind_stop_event.clear()

        def _runner():
            try:
                self.grind_fn()
            except Exception as e:
                print(f"grind function crashed: {e}")

        self.grind_thread = threading.Thread(target=_runner, daemon=False)
        self.grind_thread.start()
        return True

    def stop_grind(self):
        """Signal the grind function to stop and wait briefly for it to exit."""
        if self.grind_thread is None:
            return False
        if not self.grind_thread.is_alive():
            return False

        self.grind_stop_event.set()
        return True

    def on_key_press(self, key, target_keys, callback):
        """Handle key press events"""
        key_name_to_data = {
            "Key.up": 'w',
            "Key.down": 's',
            "Key.left": 'a',
            "Key.right": 'd'
        }
        try:
            if hasattr(key, 'char') and key.char and key.char.lower() in target_keys:
                self.key_pressed = True
                callback()
            elif key in target_keys:  # For special keys like keyboard.Key.space
                self.key_pressed = True
                callback()
            elif str(key) in key_name_to_data:
                print(key)
                self.rune_arrow_data += key_name_to_data[str(key)]
        except AttributeError:
            # Special keys (ctrl, alt, etc.) don't have char
            if key in target_keys:
                self.key_pressed = True
                callback()

    async def wait_for_response_or_key(self):
        """Helper function to wait for either Discord response or key press"""
        while (self.waiting_for_reply and
               not self.key_pressed and
               self.reply_received is None):
            await asyncio.sleep(0.1)

    async def async_send_message(self, message, user_id=None):
        if user_id:
            target_user = await self.bot.fetch_user(user_id)
        elif not self.target_user:
            self.target_user = await self.bot.fetch_user(self.target_user_id)
            target_user = self.target_user
        else:
            target_user = self.target_user
        await target_user.send(message)

    def send_message(self, message: str, user_id=None):
        if not self.is_ready():
            return {'trigger': 'error', 'discord_reply': None,
                    'success': False, 'error': 'Bot not ready'}
        asyncio.run_coroutine_threadsafe(
            self.async_send_message(message, user_id),
            self.main_loop
        )

    async def async_send_dm_and_wait_for_response(
            self,
            user_id: int,
            message: str = None,
            image_path: str = None,
            wait_keys: str = 'z',
            timeout: float = 300.0
    ) -> dict:
        """Async version of send_dm_and_wait_for_response"""
        # Reset variables
        self.waiting_for_reply = False
        self.reply_received = None
        self.key_pressed = None
        self.rune_arrow_data = ''
        if not self.target_user:
            if not self.target_user_id:
                self.target_user_id = user_id
            self.target_user = await self.bot.fetch_user(self.target_user_id)

        try:
            # Send the DM first
            # user = await self.bot.fetch_user(user_id)
            print("----------")
            print(f"Sending DM to {self.target_user.display_name}")

            if image_path:
                # Send local image
                with open(image_path, 'rb') as f:
                    picture = discord.File(f)
                    await self.target_user.send(content=message, file=picture)
            elif message:
                await self.target_user.send(message)

            # print(f"DM sent successfully! Now waiting for key '{wait_keys}' or Discord reply...")
            #
            # # Set up keyboard listener
            # listener_stopped = threading.Event()
            #
            # def stop_listener():
            #     listener_stopped.set()
            #
            # # Convert string key to list for checking
            # if isinstance(wait_keys, str):
            #     target_keys = list(wait_keys.lower())
            # else:
            #     target_keys = wait_keys
            #
            # listener = keyboard.Listener(
            #     on_press=lambda key: self.on_key_press(key, target_keys,
            #                                            stop_listener)
            # )
            #
            # # Start listening for keyboard input
            # listener.start()
            self.waiting_for_reply = True

            # Wait for either condition with proper timeout handling
            try:
                await asyncio.wait_for(
                    self.wait_for_response_or_key(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                print(f"Timeout reached ({timeout} seconds)")
                self.waiting_for_reply = False
                # listener.stop()
                return {
                    'trigger': 'timeout',
                    'discord_reply': None,
                    'success': False
                }

            # Stop the keyboard listener
            # listener.stop()
            # self.waiting_for_reply = False

            # Determine what triggered the exit
            if self.key_pressed:
                print(f"Resumed by keyboard input: '{wait_keys}'")
                return {'trigger': 'key', 'arrow_data': self.rune_arrow_data, 'success': True}
            elif self.reply_received:
                return {'trigger': 'discord', 'discord_reply': self.reply_received, 'success': True}
            else:
                return {'trigger': 'unknown', 'discord_reply': None, 'success': False}

        except Exception as e:
            print(f"Error in async_send_dm_and_wait_for_response: {e}")
            self.waiting_for_reply = False
            return {'trigger': 'error', 'discord_reply': None, 'success': False}

    def send_dm_and_wait_for_response(
            self,
            user_id: int,
            message: str = None,
            image_path: str = None,
            wait_keys: str = 'z',
            timeout: float = 10.0
    ) -> dict:
        """Synchronous wrapper that schedules the async function on the bot's event loop"""
        if not self.is_ready():
            return {'trigger': 'error', 'discord_reply': None,
                    'success': False, 'error': 'Bot not ready'}

        # Create a future and schedule it on the bot's event loop
        future = asyncio.run_coroutine_threadsafe(
            self.async_send_dm_and_wait_for_response(user_id, message,
                                                     image_path, wait_keys,
                                                     timeout),
            self.main_loop
        )

        # Wait for the result
        try:
            return future.result(timeout + 1.0)  # Add some extra time for the future itself
        except Exception as e:
            print(f"Error waiting for future result: {e}")
            return {'trigger': 'error', 'discord_reply': None,
                    'success': False}


# Global bot manager instance (optional - for simple usage)
_bot_manager = None


def get_bot_manager(token_path="../resources/token.txt"):
    """Get or create a global bot manager instance"""
    global _bot_manager
    if _bot_manager is None:
        _bot_manager = DiscordBotManager(token_path)
    return _bot_manager


def start_bot(token_path="../resources/token.txt"):
    """Convenience function to start the global bot"""
    manager = get_bot_manager(token_path)
    manager.start_bot()
    return manager


def send_text_message(message: str, user_id=None):
    manager = get_bot_manager()
    manager.send_message(message, user_id)


def send_dm_and_wait_for_response(
        user_id: int,
        message: str = None,
        image_path: str = None,
        wait_keys: str = 'z',
        timeout: float = 300.0
) -> dict:
    """Convenience function using the global bot manager"""
    manager = get_bot_manager()
    if not manager.is_ready():
        raise RuntimeError("Bot is not ready. Call start_bot() first.")

    return manager.send_dm_and_wait_for_response(
        user_id, message, image_path, wait_keys, timeout
    )


if __name__ == "__main__":
    # Example usage when running this file directly.
    # This example registers a simple controller that prints a heartbeat.

    bot_manager = start_bot()

    def controller(stop_event: threading.Event):
        import time
        print("Controller started. Use !start_main / !stop_main from Discord.")
        while not stop_event.is_set():
            time.sleep(1)

    bot_manager.set_grind_fn(controller)

    try:
        # Keep the main process alive while the bot runs.
        bot_manager.grind_thread.join()
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        print("Shutting down...")
        if bot_manager:
            bot_manager.stop_grind()
            bot_manager.stop_bot()