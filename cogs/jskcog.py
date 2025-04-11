import discord
 import os
 import sys
 from discord.ext import commands
 
 class JskCog(commands.Cog, name="jsk"):  # Changed the name to "jsk"
     def __init__(self, bot):
         self.bot = bot
 
     @commands.command(name="jsk")
     @commands.is_owner()
     async def jsk(self, ctx, command: str, *args):
         """Handle different jsk commands like jsk load, jsk unload, etc."""
         if command == "load":
             if args:
                 await self.load(ctx, args[0])
             else:
                 await ctx.send("❌ Please provide the cog name to load.")
         elif command == "unload":
             if args:
                 await self.unload(ctx, args[0])
             else:
                 await ctx.send("❌ Please provide the cog name to unload.")
         elif command == "reload":
             if args:
                 await self.reload(ctx, args[0])
             else:
                 await ctx.send("❌ Please provide the cog name to reload.")
         elif command == "restart":
             await self.restart(ctx)
         elif command == "shutdown":
             await self.shutdown(ctx)
         elif command == "start":
             await self.start(ctx)
         else:
             await ctx.send("❌ Invalid command. Available commands: load, unload, reload, restart, shutdown, start.")
 
     async def load(self, ctx, extension: str):
         """Load a cog dynamically."""
         try:
             self.bot.load_extension(f"cogs.{extension}")
             await ctx.send(f"✅ Successfully loaded `{extension}`")
         except Exception as e:
             await ctx.send(f"❌ Failed to load `{extension}`\n```py\n{e}\n```")
 
     async def unload(self, ctx, extension: str):
         """Unload a cog dynamically."""
         try:
             self.bot.unload_extension(f"cogs.{extension}")
             await ctx.send(f"✅ Successfully unloaded `{extension}`")
         except Exception as e:
             await ctx.send(f"❌ Failed to unload `{extension}`\n```py\n{e}\n```")
 
     async def reload(self, ctx, extension: str):
         """Reload a cog dynamically."""
         try:
             self.bot.unload_extension(f"cogs.{extension}")
             self.bot.load_extension(f"cogs.{extension}")
             await ctx.send(f"🔄 Successfully reloaded `{extension}`")
         except Exception as e:
             await ctx.send(f"❌ Failed to reload `{extension}`\n```py\n{e}\n```")
 
     async def restart(self, ctx):
         """Restart the bot."""
         await ctx.send("🔄 Restarting bot...")
         await self.bot.close()
         os.execv(sys.executable, ['python'] + sys.argv)
 
     async def shutdown(self, ctx):
         """Shutdown the bot."""
         await ctx.send("⚠️ Shutting down...")
         await self.bot.close()
 
     async def start(self, ctx):
         """Send a message that the bot is already running."""
         await ctx.send("✅ Bot is already running!")
 
 async def setup(bot):
     await bot.add_cog(JskCog(bot))  # Changed to JskCog here
