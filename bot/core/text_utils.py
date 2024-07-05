from calendar import month_name
from random import choice
from aiohttp import ClientSession
from anitopy import parse

from bot import Var, bot
from .ffencoder import ffargs
from .func_utils import async_logs, async_to_sync
from .reporter import rep

CAPTION_FORMAT = """
<b><i>{en_title}</i></b>
<b>╭────────────────────</b>
<b>⌲ 𝖳𝗒𝗉𝖾:</b> <i>TV</i>
<b>❦︎ 𝖲𝖾𝖺𝗌𝗈𝗇:</b> <i>{anime_season}</i>
<b>❍ 𝖤𝗉𝗂𝗌𝗈𝖽𝖾:</b> <i>{ep_no}</i>
<b>❐ 𝖲𝗍𝖺𝗍𝗎𝗌:</b> <i>{status}</i>
<b>〄 𝖠𝗎𝖽𝗂𝗈:</b> <i>Japanese</i>
<b>♡ 𝖦𝖾𝗇𝗋𝖾𝗌:</b> <i>{genres}</i>
<b>╰────────────────────</b>
<b><a href=https://t.me/pirate_flicks>© 𝖯𝗂𝗋𝖺𝗍𝖾 𝖥𝗅𝗂𝖼𝗄𝗌</a></b>
"""

GENRES_EMOJI = {"Action": "👊", "Adventure": choice(['🪂', '🧗‍♀']), "Comedy": "🤣", "Drama": " 🎭", "Ecchi": choice(['💋', '🥵']), "Fantasy": choice(['🧞', '🧞‍♂', '🧞‍♀','🌗']), "Hentai": "🔞", "Horror": "☠", "Mahou Shoujo": "☯", "Mecha": "🤖", "Music": "🎸", "Mystery": "🔮", "Psychological": "♟", "Romance": "💞", "Sci-Fi": "🛸", "Slice of Life": choice(['☘','🍁']), "Sports": "⚽️", "Supernatural": "🫧", "Thriller": choice(['🥶', '🔪','🤯'])}

ANIME_GRAPHQL_QUERY = """
query ($id: Int, $search: String) {
  Media(id: $id, type: ANIME, search: $search) {
    id
    idMal
    title {
      romaji
      english
      native
    }
    type
    format
    status(version: 2)
    description(asHtml: false)
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    season
    seasonYear
    episodes
    duration
    chapters
    volumes
    countryOfOrigin
    source
    hashtag
    trailer {
      id
      site
      thumbnail
    }
    updatedAt
    coverImage {
      large
    }
    bannerImage
    genres
    synonyms
    averageScore
    meanScore
    popularity
    trending
    favourites
    studios {
      nodes {
         name
         siteUrl
      }
    }
    isAdult
    nextAiringEpisode {
      airingAt
      timeUntilAiring
      episode
    }
    airingSchedule {
      edges {
        node {
          airingAt
          timeUntilAiring
          episode
        }
      }
    }
    externalLinks {
      url
      site
    }
    rankings {
      rank
      year
      context
    }
    siteUrl
  }
}
"""

class AniLister:
    def __init__(self):
        self.__api = "https://graphql.anilist.co"
        
    async def get_anidata(self, anime_name):
        async with ClientSession() as sess:
            async with sess.post(self.__api, json={'query': ANIME_GRAPHQL_QUERY, 'variables': {'search' : anime_name}}) as resp:
                if resp.status == 200:
                    return (await resp.json())['data'].get('Media')
                # await rep.report(f"AniList Data Post Error : {resp.status}", "error")
                return {}
    
class TextEditor:
    def __init__(self, name):
        self.__name = name
        self.adata = {}
        self.pdata = parse(name)

    async def load_anilist(self):
        for option in [(False, False), (False, True), (True, False), (True, True)]:
            self.adata = await AniLister().get_anidata(await self.parse_name(*option))
            if self.adata:
                break

    @async_logs
    async def get_id(self):
        if (ani_id := self.adata.get('id')) and str(ani_id).isdigit():
            return ani_id
            
    @async_logs
    async def parse_name(self, no_s=False, no_y=False):
        anime_name = self.pdata.get("anime_title")
        anime_season = self.pdata.get("anime_season", "01")
        anime_year = self.pdata.get("anime_year")
        if anime_name:
            pname = anime_name
            if not no_s and self.pdata.get("episode_number"):
                pname += f" {anime_season}"
            if not no_y and anime_year:
                pname += f" {anime_year}"
            return pname
        return anime_name
        
    @async_logs
    async def get_poster(self):
        if anime_id := await self.get_id():
            return f"https://img.anili.st/media/{anime_id}"
        return "https://te.legra.ph/file/8a5155c0fc61cc2b9728c.jpg"
        
    @async_logs
    async def get_upname(self, qual=""):
        anime_name = self.pdata.get("anime_title")
        codec = 'HEVC' if 'libx265' in ffargs[qual] else 'AV1' if 'libaom-av1' in ffargs[qual] else ''
        lang = 'Dub' if 'dub' in self.__name.lower() else 'Sub'
        anime_season = str(ani_s[-1]) if (ani_s := self.pdata.get('anime_season', '01')) and isinstance(ani_s, list) else str(ani_s)
        if anime_name and self.pdata.get("episode_number"):
            return f"[S{anime_season}-{'E'+str(self.pdata.get('episode_number')) if self.pdata.get('episode_number') else ''}] {self.adata.get('title', {}).get('english', '')} {'['+qual+'p]' if qual else ''} {'['+codec.upper()+']' if codec else ''} {'['+lang+']'} {Var.BRAND_UNAME}.mkv".replace("‘", "")

    @async_logs
    async def get_caption(self):
        sd = self.adata.get('startDate', {})
        startdate = f"{month_name[sd['month']]} {sd['day']}, {sd['year']}" if sd['day'] and sd['year'] else ""
        ed = self.adata.get('endDate', {})
        enddate = f"{month_name[ed['month']]} {ed['day']}, {ed['year']}" if ed['day'] and ed['year'] else ""
        
        return CAPTION_FORMAT.format(
                en_title=self.adata.get("title").get('english', ''),
                na_title=self.adata.get("title").get('native', ''),
                ro_title=self.adata.get("title").get('romaji', ''),
                form=self.adata.get("format") or "N/A",
              # genres=", ".join(f"{GENRES_EMOJI[x]} #{x.replace(' ', '_').replace('-', '_')}" for x in (self.adata.get('genres') or [])),
                genres=", ".join(f"{x.replace(' ', '_').replace('-', '_')}" for x in (self.adata.get('genres') or [])),
                avg_score=f"{sc}%" if (sc := self.adata.get('averageScore')) else "N/A",
                status=self.adata.get("status") or "RELEASING",
                anime_season = str(ani_s[-1]) if (ani_s := self.pdata.get('anime_season', '01')) and isinstance(ani_s, list) else str(ani_s),
                start_date=startdate or "N/A",
                end_date=enddate or "N/A",
                t_eps=self.adata.get("episodes") or "N/A",
                plot= (desc if (desc := self.adata.get("description") or "N/A") and len(desc) < 200 else desc[:200] + "..."),
                ep_no=self.pdata.get("episode_number"),
                cred=Var.BRAND_UNAME,
            )
