import re
import bs4
import requests
import user_agent
import os
import logging
from .utils import ensure_dir_exists, get_url_file_name, makeSafeFilename

logger = logging.getLogger(__name__)


class MediaFireDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent.generate_user_agent()

    def download(self, url, output_dir=None):
        """
        Download file from MediaFire
        
        Args:
            url (str): MediaFire URL
            output_dir (str): Directory to save the file (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get direct download URL
            download_url = self.get_direct_url(url)
            if not download_url:
                logger.error("Failed to get MediaFire download URL")
                return False
            
            # Download the file
            response = self.session.get(download_url, stream=True)
            if response.status_code != 200:
                logger.error(f"Failed to download file: HTTP {response.status_code}")
                return False
            
            # Get filename
            filename = get_url_file_name(download_url, response)
            filename = makeSafeFilename(filename)
            
            # Set output path
            if output_dir:
                ensure_dir_exists(output_dir)
                filepath = os.path.join(output_dir, filename)
            else:
                filepath = filename
            
            # Write file
            logger.info(f"Downloading MediaFire file: {filename}")
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"MediaFire download completed: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"MediaFire download error: {str(e)}")
            return False

    def get_direct_url(self, url):
        """
        Get direct download URL from MediaFire page
        
        Args:
            url (str): MediaFire URL
            
        Returns:
            str: Direct download URL or None if failed
        """
        try:
            return get(url)
        except Exception as e:
            logger.error(f"Failed to get MediaFire direct URL: {str(e)}")
            return None


# Legacy function for backward compatibility
def get(url):
    if re.match("download[0-9]*\.mediafire\.com", url.lstrip("https://").lstrip("http://").split("/")[0]):
        data = url.lstrip("https://").lstrip("http://").split("/")
        if len(data) <= 2:
            raise Exception("Invalid mediafire download url")
        unique_id = data[2]

    elif re.match("[w]*\.mediafire\.com", url.lstrip("https://").lstrip("http://").split("/")[0]):
        data = url.lstrip("https://").lstrip("http://").split("/")
        if len(data) <= 2:
            raise Exception("Invalid mediafire download url")
        unique_id = data[2]

    else:
        raise Exception("No se encontro ningun link de descarga")

    session = requests.Session()
    session.headers["User-Agent"] = user_agent.generate_user_agent()

    data = session.get(f"https://www.mediafire.com/file/{unique_id}/")
    wrp  = bs4.BeautifulSoup(data.text, "html.parser")
    btn  = wrp.find("a", attrs = {"id": "downloadButton"})
    if btn == None:
       raise Exception("Invalid download url")
    link = btn["href"]

    return link

