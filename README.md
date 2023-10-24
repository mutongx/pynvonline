# pynvonline

Python wrapper to download files from NVONLINE (partners.nvidia.com) without browser.

Example usage:

First, install dependencies:

```bash
python3 -m pip install -r requirements.txt
apt install -y aria2
```

Then save the following file as `get_links.py`:

```python
import nvonline
async with nvonline.NvOnline("name@company.domain", "myPAssw0rD") as cli:
    async for item in cli.list_groups():
        if item["name"] == "DRIVE OS 6.0.6 QNX for Safety SDK":
            async for document in cli.list_group_contents(site=item["site"], group=item["group"]):
                link = await cli.get_download_link(site=document["site"], document=document["document"])
                print(link)
```

Generate download links and use Aria2 to download them:

```bash
python3 get_links.py >links.txt
aria2c --input-file=links.txt
```

All files will be downloaded to the current directory.
