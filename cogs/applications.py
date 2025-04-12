import discord 
from discord import app_commands
from discord.ext import commands

class ApplicationSelect(discord.ui.Select):
    def __init__(self, cog):
        self.cog = cog
        options = [
            discord.SelectOption(label="In-Game Moderator Application", description="Apply for the moderator role")
        ]
        super().__init__(placeholder="Select an application...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        await self.cog.apply(interaction)


class ApplicationMenu(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.add_item(ApplicationSelect(cog))


class Applications(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.applications = {
            "In-Game Moderator Application": [
                "What is your discord username?",
                "What is your roblox username?",
                "Do you understand that asking for your application to be read will result in a denial?",
                "Explain what is RDM and the punishment for it.",
                "Explain what is VDM and the punishment for it.",
                "Explain what is LTAP and the punishment for it.",
                "Explain what is NITRP and the punishment for it.",
                "Explain what is Tool Abuse and the punishment for it.",
                "Do you understand that you have to go through training when your application gets accepted?",
                "Do you understand that requesting a role will result in termination?",
                "Do you understand that you will be required to use SPaG?",
                "What is your timezone and do you have any questions?",
            ]
        }
        self.response_channel_id = None
        self.accept_role_id = None

    @app_commands.command(name="app_panel", description="Show available application")
    async def app_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Apply for a Position",
            description="Select an application from the menu below.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=ApplicationMenu(self))

    @app_commands.command(name="set_app_channel", description="Set the channel for application responses (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def set_app_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.response_channel_id = channel.id
        await interaction.response.send_message(f"Application responses will be sent to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="app_accept_role", description="Set the role given when an application is accepted")
    @app_commands.default_permissions(administrator=True)
    async def app_accept_role(self, interaction: discord.Interaction, role: discord.Role):
        self.accept_role_id = role.id
        await interaction.response.send_message(f"Accepted applicants will now receive the {role.mention} role.", ephemeral=True)

    @app_commands.command(name="mark_for_review", description="Flag a user's application for shadow review (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def mark_for_review(self, interaction: discord.Interaction, user: discord.User, reason: str):
        embed = discord.Embed(
            title="🔍 Application Marked for Shadow Review",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="👤 User", value=user.mention, inline=False)
        embed.add_field(name="📌 Reason", value=reason, inline=False)
        embed.add_field(name="🛡️ Flagged by", value=interaction.user.mention, inline=False)
        await interaction.response.send_message(embed=embed)

    async def apply(self, interaction: discord.Interaction):
        app_name = "In-Game Moderator Application"
        questions = self.applications[app_name]
        user = interaction.user
        answers = []

        if not self.response_channel_id:
            await interaction.response.send_message("Application response channel is not set.")
            return

        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel)

        try:
            await user.send(f"Starting your application for '{app_name}'. Please answer the following questions.")
            for question in questions:
                await user.send(f"**{question}**")
                msg = await self.bot.wait_for("message", check=check, timeout=120)
                answers.append(msg.content)
            
            channel = self.bot.get_channel(self.response_channel_id)
            if not channel:
                await user.send("Application response channel not found.")
                return

            embed = discord.Embed(title=f"New Application: {app_name}", color=discord.Color.green())
            embed.add_field(name="User", value=user.mention, inline=False)
            for i, (q, a) in enumerate(zip(questions, answers), start=1):
                embed.add_field(name=f"Q{i}", value=f"{q}\n**Answer**: {a}", inline=False)

            accept_button = discord.ui.Button(label="Accept", style=discord.ButtonStyle.success)
            deny_button = discord.ui.Button(label="Deny", style=discord.ButtonStyle.danger)

            async def accept_callback(interaction: discord.Interaction):
                await self.process_decision(interaction, user, "Accepted")

            async def deny_callback(interaction: discord.Interaction):
                await self.process_decision(interaction, user, "Denied")

            accept_button.callback = accept_callback
            deny_button.callback = deny_callback

            view = discord.ui.View()
            view.add_item(accept_button)
            view.add_item(deny_button)

            await channel.send(embed=embed, view=view)
            await user.send("Your application has been submitted successfully! Please wait a few hours.")

        except Exception:
            await user.send("Application process cancelled or an error occurred.")

    async def process_decision(self, interaction: discord.Interaction, user: discord.Member, status: str):
        modal = discord.ui.Modal(title=f"{status} Application", custom_id=f"{status.lower()}_modal")
        reason_input = discord.ui.TextInput(label="Reason for decision", style=discord.TextStyle.paragraph, placeholder="Enter the reason...", required=True)
        modal.add_item(reason_input)

        async def on_submit(interaction: discord.Interaction):
            reason = reason_input.value

            embed = discord.Embed(title=f"Application {status}", color=discord.Color.green() if status == "Accepted" else discord.Color.red())
            embed.add_field(name="User", value=user.mention)
            embed.add_field(name="Reason", value=reason)

            admin_channel = self.bot.get_channel(self.response_channel_id)
            if admin_channel:
                await admin_channel.send(embed=embed)

            try:
                await user.send(f"Your application has been **{status}**.\n**Reason**: {reason}")
            except discord.Forbidden:
                pass

            if status == "Accepted" and self.accept_role_id:
                guild = interaction.guild
                role = guild.get_role(self.accept_role_id)
                if role:
                    await user.add_roles(role)
                    await interaction.response.send_message(f"{user.mention} has been accepted and given the {role.mention} role.", ephemeral=True)
                else:
                    await interaction.response.send_message("The role set for accepted applicants was not found.", ephemeral=True)

        modal.on_submit = on_submit
        await interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(Applications(bot))
