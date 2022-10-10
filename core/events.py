from __future__ import annotations

import typing

import discord
from discord.ext import commands

import utils

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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        ...

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        ...

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        ...


async def setup(bot: Doom) -> None:
    await bot.add_cog(BotEvents(bot))
