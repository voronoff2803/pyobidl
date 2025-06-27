import requests
from bs4 import BeautifulSoup
import os
import logging
from .utils import ensure_dir_exists, makeSafeFilename

logger = logging.getLogger(__name__)


class GoogleDriveDownloader:
    def __init__(self):
        self.session = requests.Session()

    def download(self, url, output_dir=None):
        """
        Download file from Google Drive
        
        Args:
            url (str): Google Drive URL
            output_dir (str): Directory to save the file (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get file info
            file_info = self.get_file_info(url)
            if not file_info:
                logger.error("Failed to get Google Drive file info")
                return False
            
            file_id = file_info['file_id']
            filename = makeSafeFilename(file_info['file_name'])
            
            # Set output path
            if output_dir:
                ensure_dir_exists(output_dir)
                filepath = os.path.join(output_dir, filename)
            else:
                filepath = filename
            
            # Download the file
            logger.info(f"Downloading Google Drive file: {filename}")
            success = self._download_file_from_drive(file_id, filepath)
            
            if success:
                logger.info(f"Google Drive download completed: {filepath}")
                return True
            else:
                logger.error("Google Drive download failed")
                return False
                
        except Exception as e:
            logger.error(f"Google Drive download error: {str(e)}")
            return False

    def _download_file_from_drive(self, file_id, destination):
        """
        Download file from Google Drive using file ID
        
        Args:
            file_id (str): Google Drive file ID
            destination (str): Local file path to save to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            URL = "https://docs.google.com/uc?export=download"
            
            session = requests.Session()
            response = session.get(URL, params={'id': file_id}, stream=True)
            token = self._get_confirm_token(response)
            
            if token:
                params = {'id': file_id, 'confirm': token}
                response = session.get(URL, params=params, stream=True)
            
            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading from Google Drive: {str(e)}")
            return False

    def _get_confirm_token(self, response):
        """
        Get confirmation token for large files
        
        Args:
            response: HTTP response object
            
        Returns:
            str: Confirmation token or None
        """
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value
        return None

    def get_file_info(self, url):
        """
        Get file information from Google Drive URL
        
        Args:
            url (str): Google Drive URL
            
        Returns:
            dict: File information or None if failed
        """
        try:
            return get_info(url)
        except Exception as e:
            logger.error(f"Failed to get Google Drive file info: {str(e)}")
            return None


# Legacy functions for backward compatibility
def get_direct_url(id):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(URL, params = { 'id' : id }, stream = True)
    try:
        if response.url:
            return response.url
    except:pass
    return None


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None


def get_info(url):
    req = requests.get(url)
    sp = BeautifulSoup(req.text,"html.parser")
    file_name = sp.find('meta',{'property':'og:title'}).attrs['content']
    file_id = url.split('/')[-2]
    file_url = get_direct_url(file_id)
    return {'file_name':file_name,'file_id':file_id,'file_url':file_url}