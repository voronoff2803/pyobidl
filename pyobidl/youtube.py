import youtube_dl
import os
import logging
from .utils import ensure_dir_exists

logger = logging.getLogger(__name__)


class YoutubeDownloader:
    def __init__(self):
        self.yt_opts = {
            'no_warnings': True,
            'ignoreerrors': True,
            'restrict_filenames': True,
            'format': 'best[protocol=https]/best[protocol=http]/bestvideo[protocol=https]/bestvideo[protocol=http]'
        }

    def download(self, url, output_dir=None):
        """
        Download video from YouTube
        
        Args:
            url (str): YouTube URL
            output_dir (str): Directory to save the file (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if output_dir:
                ensure_dir_exists(output_dir)
                self.yt_opts['outtmpl'] = os.path.join(output_dir, '%(title)s.%(ext)s')
            else:
                self.yt_opts['outtmpl'] = '%(title)s.%(ext)s'
            
            ydl = youtube_dl.YoutubeDL(self.yt_opts)
            
            logger.info(f"Downloading from YouTube: {url}")
            ydl.download([url])
            
            return True
            
        except Exception as e:
            logger.error(f"YouTube download error: {str(e)}")
            return False

    def get_info(self, url):
        """
        Get video information without downloading
        
        Args:
            url (str): YouTube URL
            
        Returns:
            dict: Video information or None if failed
        """
        try:
            ydl = youtube_dl.YoutubeDL(self.yt_opts)
            with ydl:
                result = ydl.extract_info(url, download=False)
            return result
        except Exception as e:
            logger.error(f"YouTube info extraction error: {str(e)}")
            return None


# Legacy functions for backward compatibility
def get_youtube_info(url):
    downloader = YoutubeDownloader()
    return downloader.get_info(url)


def filter_formats(formats):
    filter = []
    for f in formats:
        try:
            if '(DASH video)' in f['format']: continue
            if f['format_id'] == '136' or f['format_id'] == '135' or f['format_id'] == '134':
                if f['filesize']:
                     filter.append(f)
        except:pass
    return filter


def getVideoData(url):
    try:
        videoinfo = get_youtube_info(url)
        formats = filter_formats(videoinfo['formats'])
        format = formats[-1]
        videoname = videoinfo['title'] + '.' + format['ext']
        url = format['url']
        return {'name':videoname,'url':url}
    except:pass
    return None
    

