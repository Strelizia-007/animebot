from re import findall 
from math import floor
from time import time
from aiofiles import open as aiopen
from shlex import split as ssplit
from asyncio import sleep as asleep, gather, create_subprocess_shell
from asyncio.subprocess import PIPE

from bot import Var, ffLock, bot_loop
from .func_utils import mediainfo, convertBytes, convertTime, sendMessage, editMessage
from .reporter import rep

ffargs = {
    '1080': Var.FFCODE_1080,
    '720': Var.FFCODE_720,
    '480': Var.FFCODE_480,
    '360': Var.FFCODE_360,
}

class FFEncoder:
    def __init__(self, message, path, name, qual):
        self.__proc = None
        self.is_cancelled = False
        self.message = message
        self.__name = name
        self.__qual = qual
        self.dl_path = path
        self.__total_time = None
        self.out_path = f"encode/{name}"
        self.__prog_file = "prog.txt"
        self.__start_time = time()

    async def progress(self):
        self.__total_time = await mediainfo(self.dl_path, get_duration=True)
        if isinstance(self.__total_time, str):
            self.__total_time = 1.0
        while not (self.__proc is None or self.is_cancelled):
            async with aiopen(self.__prog_file, 'r+') as p:
                text = await p.read()
            if text:
                time_done = floor(int(t[-1]) / 1000000) if (t := findall("out_time_ms=(\d+)", text)) else 1
                ensize = int(s[-1]) if (s := findall(r"total_size=(\d+)", text)) else 0
                
                diff = time() - self.__start_time
                speed = ensize / diff
                percent = round((time_done/self.__total_time)*100, 2)
                tsize = ensize / (max(percent, 0.01)/100)
                eta = (tsize-ensize)/max(speed, 0.01)
    
                bar = floor(percent/8)*"█" + (12 - floor(percent/8))*"▒"
                
                progress_str = f"""‣ <b>Anime Name :</b> <b><i>{self.__name}</i></b>

‣ <b>Status :</b> <i>Encoding</i>
    <code>[{bar}]</code> {percent}%
    
    ‣ <b>Size :</b> {convertBytes(ensize)} out of ~ {convertBytes(tsize)}
    ‣ <b>Speed :</b> {convertBytes(speed)}/s
    ‣ <b>Time Took :</b> {convertTime(diff)}
    ‣ <b>Time Left :</b> {convertTime(eta)}

‣ <b>File(s) Encoded:</b> <code>{Var.QUALS.index(self.__qual)} / {len(Var.QUALS)}</code>"""
            
                await editMessage(self.message, progress_str)
                if (prog := findall(r"progress=(\w+)", text)) and prog[-1] == 'end':
                    break
            await asleep(8)
    
    async def start_encode(self):
        async with ffLock:
            try:
                async with aiopen(self.__prog_file, 'r+') as f:
                    await f.truncate(0)
            except FileNotFoundError:
                async with aiopen(self.__prog_file, 'w+'):
                    pass
              
            if self.is_cancelled:
                return
        
        if return_code == 0:
            return self.out_path
        else:
            await rep.report((await self.__proc.stderr.read()).decode().strip(), "error")
            
    async def cancel_encode(self):
        self.is_cancelled = True
        if self.__proc is not None:
            try:
                self.__proc.kill()
            except:
                pass
