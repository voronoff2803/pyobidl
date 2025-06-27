import time
import os
import re
import unicodedata
import re
import string
import logging
import sys

def setup_logging(verbose=False):
    """
    Setup logging configuration
    
    Args:
        verbose (bool): Enable verbose logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s' if verbose else '%(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set third-party loggers to WARNING level to reduce noise
    if not verbose:
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    ext = str(value).split('.')[-1]
    value = str(value).split('.')[0]
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_') + '.' + ext


def sizeof_fmt(num, suffix='B'):
    """
    Format bytes as human readable string
    
    Args:
        num (int): Number of bytes
        suffix (str): Suffix to append
        
    Returns:
        str: Human readable string
    """
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def req_file_size(req):
    """
    Get file size from HTTP request headers
    
    Args:
        req: HTTP request object
        
    Returns:
        int: File size in bytes, 0 if not available
    """
    try:
        return int(req.headers['content-length'])
    except:
        return 0

def get_url_file_name(url,req):
    """
    Extract filename from URL or HTTP headers
    
    Args:
        url (str): The URL
        req: HTTP request object
        
    Returns:
        str: Extracted filename
    """
    try:
        if "Content-Disposition" in req.headers.keys():
                name = str(req.headers["Content-Disposition"]).replace('attachment;', '').replace('attachment', '') 
                name = name.replace('filename=','').replace('"','')
                return name
        else:
            import urllib
            urlfix = urllib.parse.unquote(url,encoding='utf-8', errors='replace')
            tokens = str(urlfix).split('/');
            return tokens[len(tokens)-1]
    except:
        import urllib
        urlfix = urllib.parse.unquote(url,encoding='utf-8', errors='replace')
        tokens = str(urlfix).split('/');
        return tokens[len(tokens)-1]
    return ''

def get_file_size(file):
    """
    Get size of a local file
    
    Args:
        file (str): Path to file
        
    Returns:
        int: File size in bytes
    """
    file_size = os.stat(file)
    return file_size.st_size

def createID(count=8):
    """
    Generate a random ID string
    
    Args:
        count (int): Length of the ID
        
    Returns:
        str: Random ID string
    """
    from random import randrange
    map = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    id = ''
    i = 0
    while i<count:
        rnd = randrange(len(map))
        id+=map[rnd]
        i+=1
    return id

def makeSafeFilename(inputFilename):
    """
    Make a filename safe for filesystem use
    
    Args:
        inputFilename (str): Original filename
        
    Returns:
        str: Safe filename
    """
    # Set here the valid chars
    ret = ''
    map = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ._-'
    for char in inputFilename:
        if char in map:
           ret += char
        else:
           if char==' ':
              ret+='_'  # Replace spaces with underscores
           else:
              ret += '_'  # Replace invalid chars with underscores
    return ret

def ensure_dir_exists(directory):
    """
    Ensure a directory exists, create it if it doesn't
    
    Args:
        directory (str): Path to directory
    """
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

def get_file_extension(filename):
    """
    Get file extension from filename
    
    Args:
        filename (str): The filename
        
    Returns:
        str: File extension (including the dot)
    """
    return os.path.splitext(filename)[1]

def is_valid_url(url):
    """
    Check if a string is a valid URL
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid URL, False otherwise
    """
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None
