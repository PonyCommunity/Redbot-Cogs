import os
import shutil
import logging
import lavalink
import torch
from TTS.api import TTS



from gtts import gTTS
from googletrans import Translator
from discord.ext import tasks
from redbot.core import commands
from redbot.core.bot import Red, cog_data_path  # noqa
from redbot.core.commands import Cog
from redbot.cogs.audio import Audio
from typing import Optional

log = logging.getLogger("red.crab-cogs.tts")

# Get device


class TextToSpeech(Cog):
    """Plays text to speech in voice chat. Overrides music."""

    def __init__(self, bot: Red, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.tts_storage = cog_data_path(cog_instance=self).joinpath("tts")
        self.translator = Translator()
        self.clear_old_tts.start()

    async def red_delete_data_for_user(self, **kwargs):
        pass

    @tasks.loop(hours=1)
    async def clear_old_tts(self):
        try:
            if os.path.exists(self.tts_storage):
                shutil.rmtree(self.tts_storage)
        except Exception as error:
            log.error("Trying to clear old TTS audio files", exc_info=error)

    async def cog_unload(self):
        self.clear_old_tts.stop()

    @commands.hybrid_command()
    @commands.guild_only()
    async def tts(self, ctx: commands.Context, *, text: str):
        """Speak in voice chat. Overrides music. Detects the language."""
        device = "cuda" if torch.cuda.is_available() else "cpu"


        audio: Optional[Audio] = self.bot.get_cog("Audio")
        if audio is None:
            return await ctx.send("Audio cog is not loaded!")
        if not ctx.guild.me.voice:
            if await ctx.invoke(audio.command_summon):
                return  # failed to join voicechat

        tts = TTS("tts_models/de/thorsten/tacotron2-DDC")
        

        self.tts_storage.mkdir(parents=True, exist_ok=True)
        audio_path = str(self.tts_storage.joinpath(f"{ctx.message.id}.mp3"))

        tts.tts_with_vc_to_file(
            "Wie sage ich auf Italienisch, dass ich dich liebe?",
             speaker_wav="tts.mp3",
             file_path=audio_path
        )

        player = lavalink.get_player(ctx.guild.id)
        player.store("channel", ctx.channel.id)
        load_result = await player.load_tracks(audio_path)
        if load_result.has_error or load_result.load_type != lavalink.enums.LoadType.TRACK_LOADED:
            await ctx.send("There was an error playing the voice message. Check the logs for more details.")
            log.error(load_result.exception_message)
            return

        if player:
            await player.stop()
        player.add(requester=ctx.author, track=load_result.tracks[0])
        await player.play()
        if ctx.interaction:
            await ctx.reply("🗣")
        else:
            await ctx.react_quietly("🗣")
