import discord
from discord import app_commands
from discord.ext import commands
import json
import os

APPLICATIONS_FILE = "applications.json"

def load_applications():
    if os.path.exists(APPLICATIONS_FILE):
        with open(APPLICATIONS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_applications(data):
    with open(APPLICATIONS_FILE, "w") as f:
        json.dump(data, f, indent=4)

class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.applications = load_applications()
        self.response_channel_id = 1352595235976380508

    @app_commands.command(name="app_panel", description="Show available application")
    async def app_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Apply for a Position",
            description="Select an application from the menu below.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=ApplicationMenu(self))

    async def apply(self, interaction: discord.Interaction):
        app_name = "In-Game Moderator Application"
        questions = [
            "What is your discord username?",
            "What is your roblox username?",
            "Do you understand that asking for your application to be read will result in a denial?",
            "Explain what is RDM and the punishment for it.",
            "Explain what is VDM and the punishment for it.",
            "Explain what is LTAP and the punishment for it.",
            "Explain what is NITRP and the punishment for it.",
            "Explain what is Tool Abuse and the punishment for it.",
            "Do you understand that you have to go through a training when your application gets accepted?",
            "Do you understand that requesting a role will result in a termination?",
            "Do you understand that you will be required to use SPaG?",
            "What is your timezone and do you have any questions?",
        ]
        user = interaction.user
        answers = []

        try:
            await user.send(f"Starting your application for '{app_name}'. Answer the questions below.")
            
            for question in questions:
                embed = discord.Embed(description=f"**{question}**", color=discord.Color.blue())
                await user.send(embed=embed)
                msg = await self.bot.wait_for("message", check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel), timeout=120)
                answers.append(msg.content)
            
            channel = self.bot.get_channel(self.response_channel_id)
            if not channel:
                await user.send("Application response channel not found.")
                return
            
            embed = discord.Embed(title=f"New Application: {app_name}", color=discord.Color.green())
            embed.add_field(name="User", value=user.mention, inline=False)
            for q, a in zip(questions, answers):
                embed.add_field(name="​", value=f"**Q:** {q}\n**A:** {a}", inline=False)
            
            view = ApplicationDecisionView(self, user.id)
            message = await channel.send(embed=embed, view=view)
            
            self.applications[str(message.id)] = {"user_id": user.id}
            save_applications(self.applications)
            
            await user.send("Your application has been submitted successfully!")
        except Exception:
            await user.send("Application process cancelled or an error occurred.")

    async def send_decision(self, interaction: discord.Interaction, message_id: str, status: str):
        if message_id not in self.applications:
            await interaction.response.send_message("Application not found.", ephemeral=True)
            return
        
        user_id = self.applications[message_id]["user_id"]
        user = self.bot.get_user(user_id)
        if not user:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        
        modal = ApplicationDecisionModal(status, user, interaction.channel)
        await interaction.response.send_modal(modal)
        
        del self.applications[message_id]
        save_applications(self.applications)

class ApplicationDecisionView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.send_decision(interaction, str(interaction.message.id), "Accepted")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.send_decision(interaction, str(interaction.message.id), "Denied")

class ApplicationDecisionModal(discord.ui.Modal):
    def __init__(self, status, user, log_channel):
        super().__init__(title=f"{status} Application")
        self.status = status
        self.user = user
        self.log_channel = log_channel

        self.reason_input = discord.ui.TextInput(label="Reason", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_input.value
        await self.user.send(f"Your application has been {self.status}.
Reason: {reason}")
        
        embed = discord.Embed(title=f"Application {self.status}", color=discord.Color.green() if self.status == "Accepted" else discord.Color.red())
        embed.add_field(name="User", value=self.user.mention)
        embed.add_field(name="Reason", value=reason)
        await self.log_channel.send(embed=embed)
        
        await interaction.response.send_message("Decision recorded.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Applications(bot))
