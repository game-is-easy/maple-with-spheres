import discord
from discord.ext import commands
import asyncio
import ssl
import certifi
import aiohttp

# Create SSL context with proper certificates
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True  # Required for message content access
intents.members = True  # Required to access member information

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is ready to send DMs!')


# Command to get user ID
@bot.command(name='getid')
async def get_user_id(ctx, user: discord.User = None):
    """
    Get user ID for yourself or mentioned user
    Usage: !getid or !getid @username
    """
    if user is None:
        user = ctx.author

    await ctx.send(
        f"User ID for **{user.name}#{user.discriminator}**: `{user.id}`")


# Command to get your own ID
@bot.command(name='myid')
async def get_my_id(ctx):
    """
    Get your own user ID
    Usage: !myid
    """
    await ctx.send(f"Your user ID is: `{ctx.author.id}`")


# Command to send DM by user ID
@bot.command(name='dm')
async def send_dm_by_id(ctx, user_id: int, *, message):
    """
    Send a DM to a user by their ID
    Usage: !dm <user_id> <message>
    """
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        await ctx.send(f"✅ DM sent to {user.name}#{user.discriminator}")
    except discord.NotFound:
        await ctx.send("❌ User not found!")
    except discord.Forbidden:
        await ctx.send(
            "❌ Cannot send DM to this user (they may have DMs disabled)")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


# Command to send DM by mentioning the user
@bot.command(name='dmuser')
async def send_dm_by_mention(ctx, user: discord.User, *, message):
    """
    Send a DM to a mentioned user
    Usage: !dmuser @username <message>
    """
    try:
        await user.send(message)
        await ctx.send(f"✅ DM sent to {user.name}#{user.discriminator}")
    except discord.Forbidden:
        await ctx.send(
            "❌ Cannot send DM to this user (they may have DMs disabled)")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


# Command to send image DM by user ID
@bot.command(name='dmimage')
async def send_dm_image_by_id(ctx, user_id: int, image_path: str, *,
                              message=None):
    """
    Send an image DM to a user by their ID
    Usage: !dmimage <user_id> <image_path> [optional message]
    """
    try:
        user = await bot.fetch_user(user_id)
        with open(image_path, 'rb') as f:
            picture = discord.File(f)
            await user.send(content=message, file=picture)
        await ctx.send(f"✅ Image DM sent to {user.name}#{user.discriminator}")
    except FileNotFoundError:
        await ctx.send("❌ Image file not found!")
    except discord.NotFound:
        await ctx.send("❌ User not found!")
    except discord.Forbidden:
        await ctx.send(
            "❌ Cannot send DM to this user (they may have DMs disabled)")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


# Command to send image DM by mentioning user
@bot.command(name='dmuserimage')
async def send_dm_image_by_mention(ctx, user: discord.User, image_path: str, *,
                                   message=None):
    """
    Send an image DM to a mentioned user
    Usage: !dmuserimage @username <image_path> [optional message]
    """
    try:
        with open(image_path, 'rb') as f:
            picture = discord.File(f)
            await user.send(content=message, file=picture)
        await ctx.send(f"✅ Image DM sent to {user.name}#{user.discriminator}")
    except FileNotFoundError:
        await ctx.send("❌ Image file not found!")
    except discord.Forbidden:
        await ctx.send(
            "❌ Cannot send DM to this user (they may have DMs disabled)")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


# Command to send image from URL
@bot.command(name='dmurl')
async def send_dm_image_url(ctx, user_id: int, image_url: str, *,
                            message=None):
    """
    Send an image DM from URL to a user by their ID
    Usage: !dmurl <user_id> <image_url> [optional message]
    """
    try:
        user = await bot.fetch_user(user_id)

        async with aiohttp.ClientSession(ssl=ssl_context) as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    # Get filename from URL or use default
                    filename = image_url.split('/')[-1] or 'image.png'
                    picture = discord.File(data, filename=filename)
                    await user.send(content=message, file=picture)
                    await ctx.send(
                        f"✅ Image DM sent to {user.name}#{user.discriminator}")
                else:
                    await ctx.send("❌ Failed to download image from URL")
    except discord.NotFound:
        await ctx.send("❌ User not found!")
    except discord.Forbidden:
        await ctx.send(
            "❌ Cannot send DM to this user (they may have DMs disabled)")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


# Command to send DM with attachment from current message
@bot.command(name='dmattachment')
async def send_dm_with_attachment(ctx, user_id: int, *, message=None):
    """
    Send DM with attachment from your message
    Usage: !dmattachment <user_id> [optional message] (attach image to your message)
    """
    if not ctx.message.attachments:
        await ctx.send("❌ Please attach an image to your message!")
        return

    try:
        user = await bot.fetch_user(user_id)
        attachment = ctx.message.attachments[0]  # Get first attachment

        # Download the attachment
        file_data = await attachment.read()
        picture = discord.File(file_data, filename=attachment.filename)

        await user.send(content=message, file=picture)
        await ctx.send(
            f"✅ Attachment DM sent to {user.name}#{user.discriminator}")
    except discord.NotFound:
        await ctx.send("❌ User not found!")
    except discord.Forbidden:
        await ctx.send(
            "❌ Cannot send DM to this user (they may have DMs disabled)")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


# Function to send DM with image programmatically
async def send_direct_message_with_image(user_id, message=None,
                                         image_path=None, image_url=None):
    """
    Function to send DM with image programmatically
    Args:
        user_id: Discord user ID
        message: Optional text message
        image_path: Path to local image file
        image_url: URL to image online
    """
    try:
        user = await bot.fetch_user(user_id)

        if image_path:
            # Send local image
            with open(image_path, 'rb') as f:
                picture = discord.File(f)
                await user.send(content=message, file=picture)
        elif image_url:
            # Send image from URL
            async with aiohttp.ClientSession(ssl=ssl_context) as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        filename = image_url.split('/')[-1] or 'image.png'
                        picture = discord.File(data, filename=filename)
                        await user.send(content=message, file=picture)
                    else:
                        print(
                            f"Failed to download image from URL: {image_url}")
                        return False
        else:
            # Send text only
            await user.send(message)

        print(f"DM sent to {user.name}#{user.discriminator}")
        return True
    except Exception as e:
        print(f"Failed to send DM: {e}")
        return False


# Example of sending a welcome DM when someone joins the server
@bot.event
async def on_member_join(member):
    welcome_message = f"Welcome to the server, {member.name}! 🎉"
    try:
        await member.send(welcome_message)
        print(f"Welcome DM sent to {member.name}")
    except discord.Forbidden:
        print(f"Could not send welcome DM to {member.name} - DMs disabled")


# Example command to send bulk DMs (use carefully!)
@bot.command(name='bulkdm')
@commands.has_permissions(administrator=True)  # Only admins can use this
async def send_bulk_dm(ctx, *, message):
    """
    Send DM to all members of the server (Admin only)
    Usage: !bulkdm <message>
    """
    guild = ctx.guild
    success_count = 0
    fail_count = 0

    await ctx.send("🔄 Starting bulk DM process...")

    for member in guild.members:
        if not member.bot:  # Don't send to bots
            try:
                await member.send(message)
                success_count += 1
                await asyncio.sleep(
                    1)  # Rate limiting - wait 1 second between messages
            except:
                fail_count += 1

    await ctx.send(
        f"✅ Bulk DM complete! Sent: {success_count}, Failed: {fail_count}")


# Error handling for missing permissions
@send_bulk_dm.error
async def bulk_dm_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ You need administrator permissions to use this command!")


if __name__ == "__main__":
    with open("../resources/token.txt", 'r') as f:
        BOT_TOKEN = f.readlines()[0]
    IMAGE_PATH = "/Users/qiaoxuan/PycharmProjects/maple-with-spheres/training/08082349_4.png"  # or set IMAGE_URL instead
    # Run the bot
    bot.run(BOT_TOKEN)