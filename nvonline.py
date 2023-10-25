import re
import httpx
import json
from html import unescape
from urllib.parse import urlparse, parse_qs

class NvOnline:

    def __init__(self, email: str, password: str):
        self._email = email
        self._password = password
        self._prefix = "https://partners.nvidia.com"
        self._cookies = httpx.Cookies()
        self._client = httpx.AsyncClient(cookies=self._cookies, timeout=60)

    async def __aenter__(self):
        self._cookies.clear()
        await self.login()
        await self.validate_session()
        return self

    async def __aexit__(self, *_):
        pass

    async def login(self):
        login_resp = await self._client.post(f"{self._prefix}/Login/Login", data={
            "Username": self._email,
            "Password": self._password,
            "SiteHash": "",
            "Domain": "",
            "RememberUser": False,
        })
        login_text = login_resp.text
        if '<form action="/Login/Terms" method="post">' not in login_text:
            raise RuntimeError("invalid email or password")
        term_resp = await self._client.post(f"{self._prefix}/Login/Terms", data={})
        if term_resp.status_code != 302:
            raise RuntimeError("failed to accept terms")
        return term_resp.headers["location"]

    async def get_site(self):
        resp = await self._client.post(f"{self._prefix}/Base/GetSitesForLoggedOnUser")
        resp.raise_for_status()
        j = resp.json()
        return str(j["PreferedSite"])

    async def validate_session(self):
        resp = await self._client.post(f"{self._prefix}/DocumentDetails/ValidateSession")
        if resp.status_code != 200:
            raise RuntimeError("invalid session")
        j = resp.json()
        if j["Result"] != "OK":
            raise RuntimeError("invalid session validation result")
        return True
    
    async def list_groups(self, site: str | None = None):
        if site is None:
            site = await self.get_site()
        page = 0
        page_size = 25
        total = None
        while total is None or page * page_size < total:
            page += 1
            resp = await self._client.post(f"{self._prefix}/DocumentDetails/ListContents", data = {
                "srchText": "",
                "pageNo": page,
                "pageSize": page_size,
                "ArrayOfProperty": json.dumps([{"PropertyName": "Site", "Operation": "Equals", "Value": site}]),
                "dbRefreshRequired": False,
                "groupsOnly": True
            })
            resp.raise_for_status()
            j = resp.json()
            if j["Message"] != "OK":
                raise RuntimeError(f"list content failed: {j['Message']}")
            for item in re.finditer(r'<a href="(/DocumentDetails/GroupDetail.*?)" target="_blank" class="click-link">(.*?)</a>', j["Html"]):
                query = parse_qs(urlparse(unescape(item.group(1))).query)
                yield {"name": item.group(2), "site": query["siteid"][0], "group":query["groupID"][0]}
            total = j["TotalRecord"]
    
    async def list_group_contents(self, site: str, group: str):
        resp = await self._client.get(f"{self._prefix}/DocumentDetails/GroupDetail?siteid={site}&groupID={group}")
        resp.raise_for_status()
        for item in re.finditer(r'<a href=".*?" onclick="_openGroupDocumentDetailsPopup\((\d+)\);">(.*?)</a>', resp.text):
            yield {"name": item.group(2), "site": site, "group": group, "document": item.group(1)}

    async def get_download_link(self, site: str, document: str):
        resp = await self._client.get(f"{self._prefix}/Download/NativeDownloadFile?SiteID={site}&DocID={document}")
        if resp.status_code != 302:
            raise RuntimeError("failed to get download link")
        return resp.headers["location"]
