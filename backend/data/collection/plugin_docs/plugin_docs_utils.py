from bs4 import Tag


def get_version(sidebar: Tag) -> str | None:
    """
        Extract current plugin version.
    """
    rd_el = sidebar.find("h5")

    if rd_el: 
        return str(rd_el.text).split(" ")[1]
    
    return None


def get_jenkins_version_req_and_release_date(sidebar: Tag) -> tuple[str | None, str | None]:
    """
        Extract current jenkins version required and its release date.
    """
    div_list = sidebar.find_all("div")
    
    time_el = div_list[0].find("time")
    datetime = None
    if time_el:
        datetime = str(time_el.get("datetime")) 

    jenkins_ver_el = div_list[1]
    jenkins_version_req = None
    if jenkins_ver_el: 
        jenkins_version_req = str(jenkins_ver_el.text).strip().split(" ")[2]

    return jenkins_version_req, datetime