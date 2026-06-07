from urllib.parse import urlparse
 
def split_doc_types(data: dict[str, str]):
    """
    Splits documentation pages into developer and non-developer types by checking the url

    Parameters:
    - data (dict): Dictionary where keys are URLs and values are HTML content.

    Returns:
    - tuple: (developer_urls, non_developer_urls), both as lists of URLs.
    """

    print(f"There are {len(data)} pages")

    non_developer_urls = []
    developer_urls = []

    for url in data.keys():
        path = urlparse(url).path
        path_parts = [part for part in path.split("/") if part]
        second_arg = path_parts[1] if len(path_parts) > 1 else None

        if second_arg == "developer": 
            developer_urls.append(url)
        else:
            non_developer_urls.append(url)
    

    return developer_urls, non_developer_urls