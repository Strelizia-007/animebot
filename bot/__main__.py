from asyncio import create_task, create_subprocess_exec, create_subprocess_shell, run as asyrun, all_tasks, gather
from aiofiles import open as aiopen
from pyrogram import idle
from pyrogram.filters import command, user
from os import path as ospath, execl
from sys import executable

from bot import bot, Var, bot_loop, sch, LOGS, ffLock
from bot.core.auto_animes import fetch_animes
from bot.core.func_utils import clean_up, new_task
from bot.modules.up_posts import upcoming_animes

@bot.on_message(command('restart') & user(Var.ADMINS))
@new_task
async def restart(client, message):
    restart_message = await message.reply('<i>Restarting...</i>')
    if sch.running:
        sch.shutdown(wait=False)
    await clean_up()
    #if ffLock.locked():
        #await (await create_subprocess_shell('pkill', '-9', '-f', 'ffmpeg')).wait()
    await (await create_subprocess_exec('python3', 'update.py')).wait()
    async with aiopen(".restartmsg", "w") as f:
        await f.write(f"{restart_message.chat.id}\n{restart_message.id}\n")
    execl(executable, executable, "-m", "bot")

async def restart():
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="<i>Restarted !</i>")
        except Exception as e:
            LOGS.error(e)
            
async def main():
    sch.add_job(upcoming_animes, "cron", hour=0, minute=30)
    await bot.start()
    await restart()
    LOGS.info('Auto Anime Bot Started!')
    sch.start()
    await fetch_animes(Var.RSS_ITEMS)
    await idle()
    LOGS.info('Auto Anime Bot Stopped!')
    await bot.stop()
    for task in all_tasks:
        task.cancel()
    await clean_up()
    LOGS.info('Finished AutoCleanUp !!')
    
if __name__ == '__main__':
    bot_loop.run_until_complete(main())
