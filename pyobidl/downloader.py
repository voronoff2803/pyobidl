import time
import os
import re
import requests
from . import googledrive
from . import mediafire
from .megacli import mega
from .megacli import megafolder
from .utils import req_file_size,get_file_size,get_url_file_name,slugify,createID,makeSafeFilename

class Downloader(object):
    def __init__(self,destpath='', mega_email=None, mega_password=None, proxies=None):
        self.filename = ''
        self.stoping = False
        self.destpath = destpath
        if self.destpath!='':
            isExist = os.path.exists(self.destpath)
            if not isExist:
                os.makedirs(self.destpath)
        self.id = createID(12)
        self.url = ''
        self.progressfunc = None
        self.args = None
        self.mega_email = mega_email
        self.mega_password = mega_password
        self.proxies = proxies
        # Cache for Mega session
        self.mega_session = None
        
    def _get_mega_session(self):
        """Get or create a Mega session"""
        if self.mega_session is not None:
            # Return existing session if we have one
            return self.mega_session
            
        # Create Mega instance with options
        mg_options = {
            'timeout': 300,  # Increased timeout
            'proxies': self.proxies  # Pass proxies to Mega
        }
        mg = mega.Mega(options=mg_options)
        
        # Try to login with max 5 attempts with exponential backoff
        login_attempts = 0
        max_login_attempts = 5
        mdl = None
        last_error = None
        
        while login_attempts < max_login_attempts and mdl is None:
            try:
                # Use credentials if provided, otherwise login anonymously
                if self.mega_email and self.mega_password:
                    mdl = mg.login(self.mega_email, self.mega_password)
                else:
                    mdl = mg.login()
            except Exception as login_ex:
                last_error = login_ex
                login_attempts += 1
                if login_attempts >= max_login_attempts:
                    print(f"Failed to login after {max_login_attempts} attempts. Last error: {str(login_ex)}")
                    raise login_ex
                    
                # Exponential backoff wait before retrying (2^attempt seconds)
                wait_time = 2 ** login_attempts
                print(f"Login attempt {login_attempts} failed. Retrying in {wait_time} seconds.")
                time.sleep(wait_time)
        
        if mdl is None:
            print(f"Failed to login to Mega. Error: {str(last_error)}")
            return None
            
        # Cache the session for future use
        self.mega_session = mdl
        return mdl
        
    def download_info(self,url='',proxies=None):
        infos = []
        self.url = url
        req = None
        setproxycu = None
        if proxies:
            setproxycu = proxies
        elif self.proxies:
            setproxycu = self.proxies
        if '.cu' not in url:
            setproxycu = None
        if 'mediafire' in url:
                try:
                    url = mediafire.get(url)
                except:return None
        elif 'drive.google' in url:
                try:
                    info = googledrive.get_info(url)
                    self.filename = slugify(info['file_name'])
                    url = info['file_url']
                except:return None
        elif 'mega.nz' in url:
                try:
                    # Get or create a Mega session
                    mdl = self._get_mega_session()
                    if mdl is None:
                        return None
                        
                    try:
                        info = mdl.get_public_url_info(url)
                    except Exception as e:
                        print(f"Error getting URL info: {str(e)}")
                        # If session expired, clear it and try once more
                        if "Not logged in" in str(e):
                            self.mega_session = None
                            mdl = self._get_mega_session()
                            if mdl is None:
                                return None
                            info = mdl.get_public_url_info(url)
                        else:
                            info = None
                            
                    if info:
                        fname = info['name']
                        fsize = info['size']
                        infos.append({'fname':fname,'furl':url,'fsize':fsize,'iter':mdl.download_iter_url(url)})
                        req = 0
                    else:
                        mgfiles = megafolder.get_files_from_folder(url)
                        files = []
                        for fi in mgfiles:
                            url = fi['data']['g']
                            fname = fi['name']
                            fsize = fi['size']
                            infos.append({'fname':fname,'furl':url,'fsize':fsize})
                except Exception as ex:
                    print(f"Mega download_info error: {str(ex)}")
                    return None
        if req is None:
           req = requests.get(url,allow_redirects=True,stream=True,proxies=setproxycu)
           fname = get_url_file_name(url,req)
           fsize = req_file_size(req)
           infos.append({'fname':fname,'furl':url,'fsize':fsize,'resp':req})
        return infos
        
    def download_url(self,url='',progressfunc=None,args=None,proxies=None):
        self.url = url
        self.progressfunc = progressfunc
        self.args = args
        req = None
        setproxycu = None
        if proxies:
            setproxycu = proxies
        elif self.proxies:
            setproxycu = self.proxies
        if '.cu' not in url:
            setproxycu = None
        if 'mediafire' in url:
                try:
                    url = mediafire.get(url)
                except:return None
        elif 'drive.google' in url:
                try:
                    info = googledrive.get_info(url)
                    self.filename = slugify(info['file_name'])
                    url = info['file_url']
                except:return None
        elif 'mega.nz' in url:
                try:
                    # Get or create a Mega session
                    mdl = self._get_mega_session()
                    if mdl is None:
                        return None
                        
                    try:
                        info = mdl.get_public_url_info(url)
                    except Exception as e:
                        print(f"Error getting URL info: {str(e)}")
                        # If session expired, clear it and try once more
                        if "Not logged in" in str(e):
                            self.mega_session = None
                            mdl = self._get_mega_session()
                            if mdl is None:
                                return None
                            info = mdl.get_public_url_info(url)
                        else:
                            info = None
                            
                    if info:
                        output = mdl.download_url(url,dest_path=self.destpath,dest_filename=self.destpath+info['name'],progressfunc=progressfunc,args=args,self_in=self)
                        if not self.stoping:
                            return output
                        return None
                    else:
                        mgfiles = megafolder.get_files_from_folder(url)
                        files = []
                        for fi in mgfiles:
                            if self.stoping:break
                            url = fi['data']['g']
                            req = requests.get(url,allow_redirects=True,stream=True,proxies=setproxycu)
                            self.filename = fi['name']
                            output = self._process_download(url,req,progressfunc=progressfunc,args=args,self_in=self)
                            files.append(output)
                        if self.stoping:return None
                        if len(files>0):
                            return files
                    return None
                except Exception as ex:
                    print(f"Mega download_url error: {str(ex)}")
                    return None
        if req is None:
           req = requests.get(url,allow_redirects=True,stream=True,proxies=setproxycu)
        return self._process_download(url,req,progressfunc=progressfunc,args=args)

    def _process_download(self,url,req,progressfunc=None,args=None):
        if req is None:return None
        if req.status_code == 200:
            file_size = req_file_size(req)
            file_name = get_url_file_name(url,req)
            if self.filename!='':
                self.filename = makeSafeFilename(self.filename)
                file_name = self.filename
            else:
                file_name = makeSafeFilename(file_name)
                self.filename = file_name
            file_wr = open(self.destpath+file_name,'wb')
            chunk_por = 0
            chunkrandom = 100
            total = file_size
            time_start = time.time()
            time_total = 0
            size_per_second = 0
            clock_start = time.time()
            for chunk in req.iter_content(chunk_size = 1024):
                    if self.stoping:break
                    chunk_por += len(chunk)
                    size_per_second+=len(chunk)
                    tcurrent = time.time() - time_start
                    time_total += tcurrent
                    time_start = time.time()
                    if time_total>=1:
                        clock_time = (total - chunk_por) / (size_per_second)
                        if progressfunc:
                            progressfunc(self,file_name,chunk_por,total,size_per_second,clock_time,args)
                        time_total = 0
                        size_per_second = 0
                    file_wr.write(chunk)
            file_wr.close()
            if not self.stoping:
                return self.destpath+file_name
        return None

    def stop(self):self.stoping=True
    def renove(self):
        self.download_url(self.url,self.progressfunc,self.args)

class AsyncDownloader(object):
    def __init__(self,destpath='', mega_email=None, mega_password=None, proxies=None):
        self.filename = ''
        self.stoping = False
        self.destpath = destpath
        if self.destpath!='':
            isExist = os.path.exists(self.destpath)
            if not isExist:
                os.makedirs(self.destpath)
        self.id = createID(12)
        self.url = ''
        self.progressfunc = None
        self.args = None
        self.mega_email = mega_email
        self.mega_password = mega_password
        self.proxies = proxies
        # Cache for Mega session
        self.mega_session = None
        
    async def _get_mega_session(self):
        """Get or create a Mega session"""
        if self.mega_session is not None:
            # Return existing session if we have one
            return self.mega_session
            
        # Create Mega instance with options
        mg_options = {
            'timeout': 300,  # Increased timeout
            'proxies': self.proxies  # Pass proxies to Mega
        }
        mg = mega.Mega(options=mg_options)
        
        # Try to login with max 5 attempts with exponential backoff
        login_attempts = 0
        max_login_attempts = 5
        mdl = None
        last_error = None
        
        while login_attempts < max_login_attempts and mdl is None:
            try:
                # Use credentials if provided, otherwise login anonymously
                if self.mega_email and self.mega_password:
                    mdl = mg.login(self.mega_email, self.mega_password)
                else:
                    mdl = mg.login()
            except Exception as login_ex:
                last_error = login_ex
                login_attempts += 1
                if login_attempts >= max_login_attempts:
                    print(f"Failed to login after {max_login_attempts} attempts. Last error: {str(login_ex)}")
                    raise login_ex
                    
                # Exponential backoff wait before retrying (2^attempt seconds)
                wait_time = 2 ** login_attempts
                print(f"Login attempt {login_attempts} failed. Retrying in {wait_time} seconds.")
                import asyncio
                await asyncio.sleep(wait_time)
        
        if mdl is None:
            print(f"Failed to login to Mega. Error: {str(last_error)}")
            return None
            
        # Cache the session for future use
        self.mega_session = mdl
        return mdl

    async def download_url(self,url='',progressfunc=None,args=None,proxies=None):
        self.url = url
        self.progressfunc = progressfunc
        self.args = args
        req = None
        setproxycu = None
        if proxies:
            setproxycu = proxies
        elif self.proxies:
            setproxycu = self.proxies
        if '.cu' not in url:
            setproxycu = None
        if 'mediafire' in url:
                try:
                    url = mediafire.get(url)
                except:return None
        elif 'drive.google' in url:
                try:
                    info = googledrive.get_info(url)
                    self.filename = slugify(info['file_name'])
                    url = info['file_url']
                except:return None
        elif 'mega.nz' in url:
                try:
                    # Get or create a Mega session
                    mdl = await self._get_mega_session()
                    if mdl is None:
                        return None
                        
                    try:
                        info = mdl.get_public_url_info(url)
                    except Exception as e:
                        print(f"Error getting URL info: {str(e)}")
                        # If session expired, clear it and try once more
                        if "Not logged in" in str(e):
                            self.mega_session = None
                            mdl = await self._get_mega_session()
                            if mdl is None:
                                return None
                            info = mdl.get_public_url_info(url)
                        else:
                            info = None
                            
                    if info:
                        output = await mdl.async_download_url(url,dest_path=self.destpath,dest_filename=self.destpath+info['name'],progressfunc=progressfunc,args=args,self_in=self)
                        if not self.stoping:
                            return output
                        return None
                    else:
                        mgfiles = await megafolder.get_files_from_folder(url)
                        files = []
                        for fi in mgfiles:
                            if self.stoping:break
                            url = fi['data']['g']
                            req = requests.get(url,allow_redirects=True,stream=True,proxies=setproxycu)
                            self.filename = fi['name']
                            output = await self._process_download(url,req,progressfunc=progressfunc,args=args,self_in=self)
                            files.append(output)
                        if self.stoping:
                            return None
                        if len(files>0):
                            return files
                    return None
                except Exception as ex:
                    print(f"Mega download_url error: {str(ex)}")
                    return None
        if req is None:
           req = requests.get(url,allow_redirects=True,stream=True,proxies=setproxycu)
        return await self._process_download(url,req,progressfunc=progressfunc,args=args)

    async def _process_download(self,url,req,progressfunc=None,args=None):
        if req is None:return None
        if req.status_code == 200:
            file_size = req_file_size(req)
            file_name = get_url_file_name(url,req)
            if self.filename!='':
                self.filename = makeSafeFilename(self.filename)
                file_name = self.filename
            else:
                file_name = makeSafeFilename(file_name)
                self.filename = file_name
            file_wr = open(self.destpath+file_name,'wb')
            chunk_por = 0
            chunkrandom = 100
            total = file_size
            time_start = time.time()
            time_total = 0
            size_per_second = 0
            clock_start = time.time()
            for chunk in req.iter_content(chunk_size = 1024):
                    if self.stoping:break
                    chunk_por += len(chunk)
                    size_per_second+=len(chunk)
                    tcurrent = time.time() - time_start
                    time_total += tcurrent
                    time_start = time.time()
                    if time_total>=1:
                        clock_time = (total - chunk_por) / (size_per_second)
                        if progressfunc:
                            progressfunc(self,file_name,chunk_por,total,size_per_second,clock_time,args)
                        time_total = 0
                        size_per_second = 0
                    file_wr.write(chunk)
            file_wr.close()
            if not self.stoping:
                return self.destpath+file_name
        return None

    async def stop(self):
        self.stoping=True
    async def renove(self):
        await self.download_url(self.url,self.progressfunc,self.args)
