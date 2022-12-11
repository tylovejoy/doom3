from __future__ import annotations

import typing

import discord
from discord.ext import commands

import utils
import views
from views.roles import ColorRolesView, PronounRoles, ServerRelatedPings, TherapyRole

if typing.TYPE_CHECKING:
    from .doom import Doom

ASCII_LOGO = r"""                                                                                
                                                %%%%%&/*%%,/&&&&&&%%            
                                               *(%%%**,*((&/&&/*%%%&*#%%%       
                                              ,,,,,,,,,*(&&/&%&&(%&&**%%(  ...  
                                              ,(#%%,,,*/%&,///*#%%%(%%&&**%%    
                                            /%&#////,,,/&&&&//(&&//(((*%%%&*#%% 
                                        &&%/((####((,.*%&&&&&&&&&(/(%%//(*&&/   
                                       (%*(((///*,,.../#&&&&%&&&&&&&&&((#/*%%   
                                        &*(/(/*,,,...,(&&&&&#&&&&&&&&&&&&((     
                                            (//*,,.....*/**,,****&&&&&&&&&*     
                 (%                              ,,*((/,***%%#,,,,***&&#&       
                   ((%                       /*****///&&&&&&&&&%,,,,*/%&&       
        %%%         ((%                    ,.///*****(&&&&&&&&&&&&&&*/&         
         %%(****/%%&(((%%&&&&&,     ,,  (&/****////****/#&&&&&&&&&&&            
           ***/%%&****((%(#%&&%*******&&*****/&&%*////***,,,,**(&&&&            
            (%(&&&********&&&******/&&&&&%#&&&&&&&#((*///******#&&%             
            %&&&&&&&%%&&&&&&&****&&&&&&&&&&&&&&&&#**//***////*.                 
            **&&&&&&&&#%&&&(**,&&&&&&&&&&&&&&&&%*////***//***/                  
 %(       *****%%&&&(%%%%%%#*,&&&&&&&&&&&%&&&&&***///////***                    
   %%%%%%%%%****%&&%#%%%%%(,%&&&&&&&&&%&&&&&&&&*((***/////                      
         //%%%/*&&&&%%%%(,,,#&&&&&&&&&%&&&&&&&%(((((((,*%                       
                  &##%#/,,,****&&&&&&&%&&&&&&&(*((((,,*%                        
                  %%%%%%*,,*****%&&&&&#&&&&&(//(((/,*/&                         
                  %%%%%%%%/,**/#/*,,/,,////////*///*%&                          
                   #(,,,,,,,/*(#/*,,*%&%/////*(/*#%                             
                     ,,,,,..////(*,%%%%%%%%((((**%                              
                       ,.((//////,,%%%%%%%%%/***%                               
                          .((///*,,%%%%%%%%%%%.                                 
                             ///*,,*(%#%%%%%                                    
                             /(#**,,,,,                                         
                               ,,,,.,                                           """


class BotEvents(commands.Cog):
    def __init__(self, bot: Doom):
        self.bot = bot
        bot.tree.on_error = utils.on_app_command_error

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # TODO: parkour help what is this thread
        if message.channel.id == 1027419450275790898:
            await message.delete()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        The on_ready function is called when the bot
        is ready to receive and process commands.
        It prints a string containing the name of the bot,
        its owner, and which version of discord.py it's using.
        Args:
            self: Bot instance
        """
        app_info = await self.bot.application_info()
        self.bot.logger.info(
            f"{ASCII_LOGO}"
            f"\nLogged in as: {self.bot.user.name}\n"
            f"Using discord.py version: {discord.__version__}\n"
            f"Owner: {app_info.owner}\n"
        )
        if not self.bot.persistent_views_added:
            colors = [
                x
                async for x in self.bot.database.get(
                    "SELECT * FROM colors ORDER BY sort_order;",
                )
            ]

            queue = [
                x.hidden_id
                async for x in self.bot.database.get(
                    "SELECT hidden_id FROM records_queue;",
                )
            ]
            for x in queue:
                self.bot.add_view(views.VerificationView(), message_id=x)

            # colors = await ColorRoles.find().sort("+sort_order").to_list()
            view = ColorRolesView(colors)
            self.bot.add_view(view, message_id=960946616288813066)
            await self.bot.get_channel(752273327749464105).get_partial_message(
                960946616288813066
            ).edit(view=view)

            self.bot.add_view(ServerRelatedPings(), message_id=960946617169612850)
            self.bot.add_view(PronounRoles(), message_id=960946618142699560)
            self.bot.add_view(TherapyRole(), message_id=1005874559037231284)

            self.bot.logger.debug(f"Added persistent views.")
            self.persistent_views_added = True

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        ...

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Add user to DB
        await self.bot.database.set(
            "INSERT INTO users VALUES ($1, $2, true);",
            member.id,
            member.name[:25],
        )

        # Add user to cache
        self.bot.all_users[member.id] = utils.UserCacheData(
            nickname=member.nick, alertable=True
        )
        self.bot.logger.debug(f"Adding user to DB/cache: {member.name}: {member.id}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        members = [(member.id, member.name[:25]) for member in guild.members]
        await self.bot.database.set_many(
            "INSERT INTO users (user_id, nickname, alertable) VALUES ($1, $2, true)",
            [(_id, nick) for _id, nick in members],
        )

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        if before.parent_id not in self.bot.keep_alives:
            return

        if after.archived and not after.locked:
            await after.edit(archived=False)
            self.bot.logger.debug(f"Auto-unarchived thread: {after.id}")


async def setup(bot: Doom) -> None:
    await bot.add_cog(BotEvents(bot))
