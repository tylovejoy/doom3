from cogs.gym.gym import Gym


async def setup(bot):
    """Add Cog to Discord bot."""
    await bot.add_cog(Gym(bot))
