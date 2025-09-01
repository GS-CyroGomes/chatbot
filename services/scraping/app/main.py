from concurrent.futures import ThreadPoolExecutor
import asyncio, aiohttp, os, pprint
from dotenv import load_dotenv
from pathlib import Path
import json

class ChatwootScraperAsync:
    def __init__(self):
        load_dotenv()
        self.base_url = os.getenv("API_URL")
        self.max_threads = int(os.getenv("MAX_THREADS", 3))
        self.account_id = os.getenv("ACCOUNT_ID")
        self.token = os.getenv("API_TOKEN")
        self.headers = {"api_access_token": self.token}
        self.root_path = Path(__file__).absolute().parent.parent.parent.parent + "data/json"

    def get_resolved_chats(self, per_page=25):
        def thread_worker(page_start):
            asyncio.run(self.process_pages_async_while(page_start, per_page))

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = [executor.submit(thread_worker, 1) for _ in range(self.max_threads)]
            for future in futures:
                future.result()

    async def process_pages_async_while(self, page_start=1, per_page=25):
        page = page_start
        async with aiohttp.ClientSession() as session:
            while True:
                chats = await self.fetch_chats_page(session, page, per_page)
                if not chats:
                    break
                await self.fetch_all_chats_messages(chats)
                page += 1

    async def fetch_chats_page(self, session, page, per_page=25):
        url = f"{self.base_url}/accounts/{self.account_id}/conversations?status=resolved&page={page}&per_page={per_page}"
        async with session.get(url, headers=self.headers) as resp:
            data = await resp.json()
            return [chat["id"] for chat in data["data"]["payload"]]

    async def fetch_all_chats_messages(self, id_chats):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_messages(session, chat_id) for chat_id in id_chats]
            return await asyncio.gather(*tasks)

    async def fetch_messages(self, session, chat_id):
        url = f"{self.base_url}/accounts/{self.account_id}/conversations/{chat_id}/messages"
        async with session.get(url, headers=self.headers) as resp:
            data = await resp.json()
            messages = data.get("payload", [])
            for msg in messages:
                pprint.pprint(msg)
                exit()
                # print(f"Chat {chat_id} -> {msg.get('content')}")
            exit()
            return messages

    def format_chat_messages(self, messages):
        return messages

    def save_chat(self, chat_id, messages):
        with open(f"{self.root_path}/chat_{chat_id}.json", "w") as f:
            json.dump(messages, f)


if __name__ == "__main__":
    requester = ChatwootScraperAsync()
    # requester.get_resolved_chats()
