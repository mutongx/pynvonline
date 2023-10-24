# pynvonline
Python wrapper to download files from NVONLINE (partners.nvidia.com) without browser

Example usage:

```python
import nvonline
async with nvonline.NvOnline("name@company.domain", "myPAssw0rD") as cli:
    async for item in cli.list_groups():
        if item["name"] == "DRIVE OS 6.0.6 QNX for Safety SDK":
            async for document in cli.list_group_contents(site=item["site"], group=item["group"]):
                link = await cli.get_download_link(site=document["site"], document=document["document"])
                print(link)
```

Save the above file as `get_links.py`, then:

```bash
python3 get_links.py >links.txt
aria2c --input-file=links.txt  # Run `apt install aria2` if you don't have it
```

All files will be downloaded to the current directory.
