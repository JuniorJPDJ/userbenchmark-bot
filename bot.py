import asyncio
import logging
import os

import aiohttp
from bs4 import BeautifulSoup
from telethon import TelegramClient, events
from telethon.tl.custom import InlineBuilder
from telethon.tl.types import InputWebDocument
import yaml

def env_constructor(loader, node):
    return os.environ.get(loader.construct_scalar(node), None)

async def main(config):
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=config['log_level'])
    # logger = logging.getLogger(__name__)

    client = TelegramClient(**config['telethon_settings'])
    print("Starting")
    await client.start(bot_token=config['bot_token'])
    print("Started")

    async with aiohttp.ClientSession(
            raise_for_status=True,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0"}
      ) as http_sess:
        builder = InlineBuilder(client)

        @client.on(events.InlineQuery)
        async def inline_handler(event):
            if not event.text or len(event.text) < 2:
                await event.answer()
                return
            

            try:
                resp = await http_sess.get("https://www.userbenchmark.com/Search", params={
                    "searchTerm": event.text
                })
                
                # TODO: handle case with only one result (redirect to result page - eg. ryzen 5800)
                
                results = await resp.text()
            except aiohttp.ClientResponseError:
                await event.answer([builder.article("Error occured while searching", description="Oops ;/", text="Oops ;/")])
                return

            results = BeautifulSoup(results, features="html.parser").find_all(class_='tl-tag')

            await event.answer(
                [builder.article(
                    title=r.find(class_="tl-title").text,
                    description=f'{r.find(class_="tl-caption").text}\n{r.find(class_="tl-desc").text}',
                    text=r['href'],
                    thumb=InputWebDocument(
                        url=r.find(class_="tl-icon")['src'],
                        mime_type="image/jpeg",
                        size=0,
                        attributes=[]
                    )
                ) for r in results] or 
                [builder.article("No search results found", description="Try another query", text="No search results found.")]
            )

        async with client:
            print("Good morning!")
            await client.run_until_disconnected()


if __name__ == '__main__':
    yaml.SafeLoader.add_constructor("!env", env_constructor)
    with open("config.yml", 'r') as f:
        config = yaml.safe_load(f)
    asyncio.run(main(config))
