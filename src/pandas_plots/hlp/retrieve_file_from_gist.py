import time
import urllib.request


def retrieve_file_from_gist(
    account: str,
    gist_id: str,
    filename: str,
) -> None:
    """
    Downloads a file from a GitHub gist to the current directory.
    A cache-buster timestamp is appended to the URL to force the
    Fastly/GitHub CDN to serve the latest commit.
    
    ⚠️ Dont forget to **import** the file afterwards if its `.py`!  
    Its best practise to add the filename to `.gitignore` to keep the repo clean.

    Parameters
    ----------
    account : str
        The GitHub account name that owns the gist.
    gist_id : str
        The id of the gist.
    filename : str
        The name of the file to retrieve from the gist.

    Returns
    -------
    None
    """
    raw_gist_url = f"https://gist.githubusercontent.com/{account}/{gist_id}/raw/{filename}?v={int(time.time())}"
    path, _ = urllib.request.urlretrieve(raw_gist_url, filename)
    return
