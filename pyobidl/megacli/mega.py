import math
import re
import json
import logging
import secrets
from pathlib import Path
import hashlib
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Util import Counter
import os
import random
import binascii
import tempfile
import shutil
import subprocess
import sys

import requests
from tenacity import retry, wait_exponential, retry_if_exception_type, stop_after_attempt

from .errors import ValidationError, RequestError
from .crypto import (a32_to_base64, encrypt_key, base64_url_encode,
                     encrypt_attr, base64_to_a32, base64_url_decode,
                     decrypt_attr, a32_to_str, get_chunks, str_to_a32,
                     decrypt_key, mpi_to_int, stringhash, prepare_key, make_id,
                     makebyte, modular_inverse)

logger = logging.getLogger(__name__)


class Mega:
    def __init__(self, options=None):
        self.schema = 'https'
        self.domain = 'mega.co.nz'
        self.timeout = 300  # Increased from 160 to 300 seconds
        self.sid = None
        self.sequence_num = random.randint(0, 0xFFFFFFFF)
        self.request_id = make_id(10)
        self._trash_folder_node_id = None
        self.stoping = False
        self.proxies = None

        if options is None:
            options = {}
        self.options = options
        
        # Set proxies if provided in options
        if 'proxies' in options:
            self.proxies = options['proxies']

    def stop(self):
        self.stoping = True

    def parse_mega_url(self, url):
        """
        Parse Mega.nz URL to extract file ID and decryption key
        
        Args:
            url (str): Mega.nz URL in format https://mega.nz/file/[file_id]#[decryption_key]
        
        Returns:
            tuple: (file_id, decryption_key) or (None, None) if invalid
        """
        try:
            # Remove any extra characters or spaces
            url = url.strip()
            
            # Check if it's a valid Mega URL
            if not url.startswith('https://mega.nz/file/'):
                return None, None
            
            # Extract the part after /file/
            file_part = url.split('/file/', 1)[1]
            
            # Split by # to get file_id and decryption_key
            if '#' in file_part:
                file_id, decryption_key = file_part.split('#', 1)
                return file_id, decryption_key
            else:
                return None, None
                
        except Exception as e:
            logger.error(f"Error parsing URL: {e}")
            return None, None

    def download_with_megatools(self, url, output_dir):
        """
        Download using megatools (megadl command)
        """
        try:
            # Clean the URL to remove any leading/trailing whitespace
            url = url.strip()
            
            # Check if megatools is available
            if not shutil.which('megadl'):
                logger.error("megatools (megadl) not found")
                return False
                
            # Get absolute paths for debugging
            original_dir = os.getcwd()
            abs_output_dir = os.path.abspath(output_dir)
            
            logger.info(f"🔍 download_with_megatools: Original dir: {original_dir}")
            logger.info(f"🔍 download_with_megatools: Output dir: {output_dir}")
            logger.info(f"🔍 download_with_megatools: Absolute output dir: {abs_output_dir}")
            
            # List files before download
            files_before = []
            if os.path.exists(abs_output_dir):
                files_before = os.listdir(abs_output_dir)
                logger.info(f"🔍 download_with_megatools: Files in output dir before: {files_before}")
            
            # Change to output directory
            logger.info(f"🔍 download_with_megatools: Changing to output directory...")
            os.chdir(abs_output_dir)
            current_dir_after_change = os.getcwd()
            logger.info(f"🔍 download_with_megatools: Current dir after change: {current_dir_after_change}")
            
            # Run megadl command
            logger.info(f"🔍 download_with_megatools: Running: megadl {url}")
            result = subprocess.run(['megadl', url], capture_output=True, text=True)
            
            logger.info(f"🔍 download_with_megatools: Return code: {result.returncode}")
            logger.info(f"🔍 download_with_megatools: stdout: {result.stdout}")
            logger.info(f"🔍 download_with_megatools: stderr: {result.stderr}")
            
            # List files after download (while still in output dir)
            files_after = os.listdir('.')
            logger.info(f"🔍 download_with_megatools: Files in current dir after download: {files_after}")
            
            # Change back to original directory
            logger.info(f"🔍 download_with_megatools: Changing back to original directory...")
            os.chdir(original_dir)
            current_dir_after_return = os.getcwd()
            logger.info(f"🔍 download_with_megatools: Current dir after return: {current_dir_after_return}")
            
            # List files in output dir from original location
            if os.path.exists(abs_output_dir):
                files_final = os.listdir(abs_output_dir)
                logger.info(f"🔍 download_with_megatools: Files in output dir from original location: {files_final}")
            
            if result.returncode == 0:
                # Check if stderr contains warnings about invalid links
                if result.stderr and "Skipping invalid Mega download link" in result.stderr:
                    logger.error(f"❌ megatools rejected URL as invalid: {result.stderr}")
                    return False
                    
                # Check if stdout indicates successful download
                if result.stdout and "Downloaded" in result.stdout:
                    logger.info("✅ Download completed successfully using megatools!")
                    return True
                elif not files_after:
                    logger.error("❌ megatools completed but no files were downloaded")
                    return False
                else:
                    logger.info("✅ Download completed successfully using megatools!")
                    return True
            else:
                logger.error(f"❌ megatools failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ megatools error: {e}")
            logger.error(f"🔍 download_with_megatools: Exception details: {type(e).__name__}: {str(e)}")
            # Make sure we return to original directory even on error
            try:
                os.chdir(original_dir)
            except:
                pass
            return False

    def install_megatools_macos(self):
        """
        Attempt to install megatools on macOS using Homebrew
        """
        if sys.platform != "darwin":  # Not macOS
            return False
            
        logger.info("🍺 Attempting to install megatools via Homebrew...")
        try:
            result = subprocess.run(['brew', 'install', 'megatools'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ megatools installed successfully!")
                return True
            else:
                logger.error(f"❌ Homebrew installation failed: {result.stderr}")
                return False
        except FileNotFoundError:
            logger.error("❌ Homebrew not found. Please install Homebrew first: https://brew.sh")
            return False

    def simple_download(self, url, output_dir=None):
        """
        Simple download method using megatools or providing instructions
        
        Args:
            url (str): Mega.nz URL
            output_dir (str): Directory to save the file (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Parse the URL
            file_id, decryption_key = self.parse_mega_url(url)
            
            if not file_id or not decryption_key:
                logger.error("Error: Invalid Mega.nz URL format")
                logger.error("Expected format: https://mega.nz/file/[file_id]#[decryption_key]")
                return False
            
            logger.info(f"File ID: {file_id}")
            logger.info(f"Decryption Key: {decryption_key[:10]}...")
            
            logger.info("Connecting to Mega.nz...")
            
            # Set output directory
            if output_dir:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    logger.info(f"Created directory: {output_dir}")
            else:
                output_dir = os.getcwd()
            
            logger.info(f"Download directory: {output_dir}")
            
            # Try method 1: megatools (if available)
            if shutil.which('megadl'):
                logger.info("Using megatools (megadl)...")
                return self.download_with_megatools(url, output_dir)
            
            # Try to install megatools on macOS
            if sys.platform == "darwin":  # macOS
                if self.install_megatools_macos():
                    logger.info("🔄 Retrying download...")
                    return self.download_with_megatools(url, output_dir)
            
            # Fallback: provide instructions
            logger.error("❌ Direct download method not available for Mega.nz encrypted files.")
            logger.info("📋 To download Mega.nz files, please use one of these methods:")
            logger.info("Method 1: Install megatools (Recommended)")
            logger.info("  macOS: brew install megatools")
            logger.info("  Ubuntu/Debian: sudo apt install megatools")
            logger.info("  Then run this script again")
            logger.info("Method 2: Manual download")
            logger.info(f"  1. Open this URL in your browser: {url}")
            logger.info("  2. Click download and save to your desired location")
            logger.info("Method 3: Use megacmd")
            logger.info("  Download from: https://mega.nz/cmd")
            logger.info(f"  Then run: mega-get {url}")
            
            return False
                
        except Exception as e:
            logger.error(f"❌ Error during download: {e}")
            return False

    def login(self, email=None, password=None):
        if email:
            self._login_user(email, password)
        else:
            self.login_anonymous()
        self._trash_folder_node_id = self.get_node_by_type(4)[0]
        logger.info('Login complete')
        return self

    def _login_user(self, email, password):
        logger.info('Logging in user...')
        email = email.lower()
        
        try:
            # Step 1: Get the user salt (first API call)
            get_user_salt_resp = self._api_request({'a': 'us0', 'user': email})
            user_salt = None
            
            try:
                user_salt = base64_to_a32(get_user_salt_resp['s'])
            except KeyError:
                # v1 user account
                logger.info('Using v1 account authentication')
                password_aes = prepare_key(str_to_a32(password))
                user_hash = stringhash(email, password_aes)
            else:
                # v2 user account
                logger.info('Using v2 account authentication')
                pbkdf2_key = hashlib.pbkdf2_hmac(hash_name='sha512',
                                                password=password.encode(),
                                                salt=a32_to_str(user_salt),
                                                iterations=100000,
                                                dklen=32)
                password_aes = str_to_a32(pbkdf2_key[:16])
                user_hash = base64_url_encode(pbkdf2_key[-16:])
            
            # Step 2: Authenticate with user hash (second API call)
            resp = self._api_request({'a': 'us', 'user': email, 'uh': user_hash})
            
            if isinstance(resp, int):
                # Handle error codes specifically
                if resp == -9:
                    logger.error("Invalid credentials (email or password incorrect)")
                    raise RequestError("Invalid credentials")
                elif resp == -11:
                    logger.error("Rate limit exceeded")
                    raise RequestError("Rate limit exceeded - wait before trying again")
                elif resp == -16:
                    logger.error("Account blocked/suspended")
                    raise RequestError("Account suspended")
                else:
                    logger.error(f"Login error code: {resp}")
                    raise RequestError(resp)
                    
            # Process the successful login
            self._login_process(resp, password_aes)
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise

    def login_anonymous(self):
        logger.info('Logging in anonymous temporary user...')
        master_key = [random.randint(0, 0xFFFFFFFF)] * 4
        password_key = [random.randint(0, 0xFFFFFFFF)] * 4
        session_self_challenge = [random.randint(0, 0xFFFFFFFF)] * 4

        user = self._api_request({
            'a':
            'up',
            'k':
            a32_to_base64(encrypt_key(master_key, password_key)),
            'ts':
            base64_url_encode(
                a32_to_str(session_self_challenge) +
                a32_to_str(encrypt_key(session_self_challenge, master_key)))
        })

        resp = self._api_request({'a': 'us', 'user': user})
        if isinstance(resp, int):
            raise RequestError(resp)
        self._login_process(resp, password_key)

    def _login_process(self, resp, password):
        encrypted_master_key = base64_to_a32(resp['k'])
        self.master_key = decrypt_key(encrypted_master_key, password)
        if 'tsid' in resp:
            tsid = base64_url_decode(resp['tsid'])
            key_encrypted = a32_to_str(
                encrypt_key(str_to_a32(tsid[:16]), self.master_key))
            if key_encrypted == tsid[-16:]:
                self.sid = resp['tsid']
        elif 'csid' in resp:
            encrypted_rsa_private_key = base64_to_a32(resp['privk'])
            rsa_private_key = decrypt_key(encrypted_rsa_private_key,
                                          self.master_key)

            private_key = a32_to_str(rsa_private_key)
            # The private_key contains 4 MPI integers concatenated together.
            rsa_private_key = [0, 0, 0, 0]
            for i in range(4):
                # An MPI integer has a 2-byte header which describes the number
                # of bits in the integer.
                bitlength = (private_key[0] * 256) + private_key[1]
                bytelength = math.ceil(bitlength / 8)
                # Add 2 bytes to accommodate the MPI header
                bytelength += 2
                rsa_private_key[i] = mpi_to_int(private_key[:bytelength])
                private_key = private_key[bytelength:]

            first_factor_p = rsa_private_key[0]
            second_factor_q = rsa_private_key[1]
            private_exponent_d = rsa_private_key[2]
            # In MEGA's webclient javascript, they assign [3] to a variable
            # called u, but I do not see how it corresponds to pycryptodome's
            # RSA.construct and it does not seem to be necessary.
            rsa_modulus_n = first_factor_p * second_factor_q
            phi = (first_factor_p - 1) * (second_factor_q - 1)
            public_exponent_e = modular_inverse(private_exponent_d, phi)

            rsa_components = (
                rsa_modulus_n,
                public_exponent_e,
                private_exponent_d,
                first_factor_p,
                second_factor_q,
            )
            rsa_decrypter = RSA.construct(rsa_components)

            encrypted_sid = mpi_to_int(base64_url_decode(resp['csid']))

            sid = '%x' % rsa_decrypter._decrypt(encrypted_sid)
            sid = binascii.unhexlify('0' + sid if len(sid) % 2 else sid)
            self.sid = base64_url_encode(sid[:43])

    @retry(retry=retry_if_exception_type(RuntimeError),
           wait=wait_exponential(multiplier=2, min=2, max=60),
           stop=stop_after_attempt(10))  # Maximum 10 retries
    def _api_request(self, data):
        params = {'id': self.sequence_num}
        self.sequence_num += 1

        if self.sid:
            params.update({'sid': self.sid})

        # ensure input data is a list
        if not isinstance(data, list):
            data = [data]

        url = f'{self.schema}://g.api.{self.domain}/cs'
        try:
            response = requests.post(
                url,
                params=params,
                data=json.dumps(data),
                timeout=self.timeout,
                proxies=self.proxies
            )
            json_resp = json.loads(response.text)
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            logger.error(f"Request error: {str(e)}")
            msg = f'Request error: {str(e)}'
            raise RuntimeError(msg)
            
        try:
            if isinstance(json_resp, list):
                int_resp = json_resp[0] if isinstance(json_resp[0],
                                                      int) else None
            elif isinstance(json_resp, int):
                int_resp = json_resp
        except IndexError:
            int_resp = None
        if int_resp is not None:
            if int_resp == 0:
                return int_resp
            if int_resp == -3:
                msg = 'Request failed, retrying'
                logger.info(msg)
                raise RuntimeError(msg)
            raise RequestError(int_resp)
        return json_resp[0]

    def _parse_url(self, url):
        """Parse file id and key from url."""
        if '/file/' in url:
            # V2 URL structure
            url = url.replace(' ', '')
            file_id = re.findall(r'\W\w\w\w\w\w\w\w\w\W', url)[0][1:-1]
            id_index = re.search(file_id, url).end()
            key = url[id_index + 1:]
            return f'{file_id}!{key}'
        elif '!' in url:
            # V1 URL structure
            match = re.findall(r'/#!(.*)', url)
            path = match[0]
            return path
        else:
            raise RequestError('Url key missing')

    def _process_file(self, file, shared_keys):
        if file['t'] == 0 or file['t'] == 1:
            keys = dict(
                keypart.split(':', 1) for keypart in file['k'].split('/')
                if ':' in keypart)
            uid = file['u']
            key = None
            # my objects
            if uid in keys:
                key = decrypt_key(base64_to_a32(keys[uid]), self.master_key)
            # shared folders
            elif 'su' in file and 'sk' in file and ':' in file['k']:
                shared_key = decrypt_key(base64_to_a32(file['sk']),
                                         self.master_key)
                key = decrypt_key(base64_to_a32(keys[file['h']]), shared_key)
                if file['su'] not in shared_keys:
                    shared_keys[file['su']] = {}
                shared_keys[file['su']][file['h']] = shared_key
            # shared files
            elif file['u'] and file['u'] in shared_keys:
                for hkey in shared_keys[file['u']]:
                    shared_key = shared_keys[file['u']][hkey]
                    if hkey in keys:
                        key = keys[hkey]
                        key = decrypt_key(base64_to_a32(key), shared_key)
                        break
            if file['h'] and file['h'] in shared_keys.get('EXP', ()):
                shared_key = shared_keys['EXP'][file['h']]
                encrypted_key = str_to_a32(
                    base64_url_decode(file['k'].split(':')[-1]))
                key = decrypt_key(encrypted_key, shared_key)
                file['shared_folder_key'] = shared_key
            if key is not None:
                # file
                if file['t'] == 0:
                    k = (key[0] ^ key[4], key[1] ^ key[5], key[2] ^ key[6],
                         key[3] ^ key[7])
                    file['iv'] = key[4:6] + (0, 0)
                    file['meta_mac'] = key[6:8]
                # folder
                else:
                    k = key
                file['key'] = key
                file['k'] = k
                attributes = base64_url_decode(file['a'])
                attributes = decrypt_attr(attributes, k)
                file['a'] = attributes
            # other => wrong object
            elif file['k'] == '':
                file['a'] = False
        elif file['t'] == 2:
            self.root_id = file['h']
            file['a'] = {'n': 'Cloud Drive'}
        elif file['t'] == 3:
            self.inbox_id = file['h']
            file['a'] = {'n': 'Inbox'}
        elif file['t'] == 4:
            self.trashbin_id = file['h']
            file['a'] = {'n': 'Rubbish Bin'}
        return file

    def _init_shared_keys(self, files, shared_keys):
        """
        Init shared key not associated with a user.
        Seems to happen when a folder is shared,
        some files are exchanged and then the
        folder is un-shared.
        Keys are stored in files['s'] and files['ok']
        """
        ok_dict = {}
        for ok_item in files['ok']:
            shared_key = decrypt_key(base64_to_a32(ok_item['k']),
                                     self.master_key)
            ok_dict[ok_item['h']] = shared_key
        for s_item in files['s']:
            if s_item['u'] not in shared_keys:
                shared_keys[s_item['u']] = {}
            if s_item['h'] in ok_dict:
                shared_keys[s_item['u']][s_item['h']] = ok_dict[s_item['h']]
        self.shared_keys = shared_keys

    def find_path_descriptor(self, path, files=()):
        """
        Find descriptor of folder inside a path. i.e.: folder1/folder2/folder3
        Params:
            path, string like folder1/folder2/folder3
        Return:
            Descriptor (str) of folder3 if exists, None otherwise
        """
        paths = path.split('/')

        files = files or self.get_files()
        parent_desc = self.root_id
        found = False
        for foldername in paths:
            if foldername != '':
                for file in files.items():
                    if (file[1]['a'] and file[1]['t']
                            and file[1]['a']['n'] == foldername):
                        if parent_desc == file[1]['p']:
                            parent_desc = file[0]
                            found = True
                if found:
                    found = False
                else:
                    return None
        return parent_desc

    def find(self, filename=None, handle=None, exclude_deleted=False):
        """
        Return file object from given filename
        """
        files = self.get_files()
        if handle:
            return files[handle]
        path = Path(filename)
        filename = path.name
        parent_dir_name = path.parent.name
        for file in list(files.items()):
            parent_node_id = None
            try:
                if parent_dir_name:
                    parent_node_id = self.find_path_descriptor(parent_dir_name,
                                                               files=files)
                    if (filename and parent_node_id and file[1]['a']
                            and file[1]['a']['n'] == filename
                            and parent_node_id == file[1]['p']):
                        if (exclude_deleted and self._trash_folder_node_id
                                == file[1]['p']):
                            continue
                        return file
                elif (filename and file[1]['a']
                      and file[1]['a']['n'] == filename):
                    if (exclude_deleted
                            and self._trash_folder_node_id == file[1]['p']):
                        continue
                    return file
            except TypeError:
                continue

    def get_files(self):
        logger.info('Getting all files...')
        files = self._api_request({'a': 'f', 'c': 1, 'r': 1})
        files_dict = {}
        shared_keys = {}
        self._init_shared_keys(files, shared_keys)
        for file in files['f']:
            processed_file = self._process_file(file, shared_keys)
            # ensure each file has a name before returning
            if processed_file['a']:
                files_dict[file['h']] = processed_file
        return files_dict

    def get_upload_link(self, file):
        """
        Get a files public link inc. decrypted key
        Requires upload() response as input
        """
        if 'f' in file:
            file = file['f'][0]
            public_handle = self._api_request({'a': 'l', 'n': file['h']})
            file_key = file['k'][file['k'].index(':') + 1:]
            decrypted_key = a32_to_base64(
                decrypt_key(base64_to_a32(file_key), self.master_key))
            return (f'{self.schema}://{self.domain}'
                    f'/#!{public_handle}!{decrypted_key}')
        else:
            raise ValueError('''Upload() response required as input,
                            use get_link() for regular file input''')

    def get_link(self, file):
        """
        Get a file public link from given file object
        """
        file = file[1]
        if 'h' in file and 'k' in file:
            public_handle = self._api_request({'a': 'l', 'n': file['h']})
            if public_handle == -11:
                raise RequestError("Can't get a public link from that file "
                                   "(is this a shared file?)")
            decrypted_key = a32_to_base64(file['key'])
            return (f'{self.schema}://{self.domain}'
                    f'/#!{public_handle}!{decrypted_key}')
        else:
            raise ValidationError('File id and key must be present')

    def _node_data(self, node):
        try:
            return node[1]
        except (IndexError, KeyError):
            return node

    def get_folder_link(self, file):
        try:
            file = file[1]
        except (IndexError, KeyError):
            pass
        if 'h' in file and 'k' in file:
            public_handle = self._api_request({'a': 'l', 'n': file['h']})
            if public_handle == -11:
                raise RequestError("Can't get a public link from that file "
                                   "(is this a shared file?)")
            decrypted_key = a32_to_base64(file['shared_folder_key'])
            return (f'{self.schema}://{self.domain}'
                    f'/#F!{public_handle}!{decrypted_key}')
        else:
            raise ValidationError('File id and key must be present')

    def get_user(self):
        user_data = self._api_request({'a': 'ug'})
        return user_data

    def get_node_by_type(self, type):
        """
        Get a node by it's numeric type id, e.g:
        0: file
        1: dir
        2: special: root cloud drive
        3: special: inbox
        4: special trash bin
        """
        nodes = self.get_files()
        for node in list(nodes.items()):
            if node[1]['t'] == type:
                return node

    def get_files_in_node(self, target):
        """
        Get all files in a given target, e.g. 4=trash
        """
        if type(target) == int:
            # convert special nodes (e.g. trash)
            node_id = self.get_node_by_type(target)
        else:
            node_id = [target]

        files = self._api_request({'a': 'f', 'c': 1})
        files_dict = {}
        shared_keys = {}
        self._init_shared_keys(files, shared_keys)
        for file in files['f']:
            processed_file = self._process_file(file, shared_keys)
            if processed_file['a'] and processed_file['p'] == node_id[0]:
                files_dict[file['h']] = processed_file
        return files_dict

    def get_id_from_public_handle(self, public_handle):
        # get node data
        node_data = self._api_request({'a': 'f', 'f': 1, 'p': public_handle})
        node_id = self.get_id_from_obj(node_data)
        return node_id

    def get_id_from_obj(self, node_data):
        """
        Get node id from a file object
        """
        node_id = None

        for i in node_data['f']:
            if i['h'] != '':
                node_id = i['h']
        return node_id

    def get_quota(self):
        """
        Get current remaining disk quota in MegaBytes
        """
        json_resp = self._api_request({
            'a': 'uq',
            'xfer': 1,
            'strg': 1,
            'v': 1
        })
        # convert bytes to megabyes
        return json_resp['mstrg'] / 1048576

    def get_storage_space(self, giga=False, mega=False, kilo=False):
        """
        Get the current storage space.
        Return a dict containing at least:
          'used' : the used space on the account
          'total' : the maximum space allowed with current plan
        All storage space are in bytes unless asked differently.
        """
        if sum(1 if x else 0 for x in (kilo, mega, giga)) > 1:
            raise ValueError("Only one unit prefix can be specified")
        unit_coef = 1
        if kilo:
            unit_coef = 1024
        if mega:
            unit_coef = 1048576
        if giga:
            unit_coef = 1073741824
        json_resp = self._api_request({'a': 'uq', 'xfer': 1, 'strg': 1})
        return {
            'used': json_resp['cstrg'] / unit_coef,
            'total': json_resp['mstrg'] / unit_coef,
        }

    def get_balance(self):
        """
        Get account monetary balance, Pro accounts only
        """
        user_data = self._api_request({"a": "uq", "pro": 1})
        if 'balance' in user_data:
            return user_data['balance']

    def delete(self, public_handle):
        """
        Delete a file by its public handle
        """
        return self.move(public_handle, 4)

    def delete_url(self, url):
        """
        Delete a file by its url
        """
        path = self._parse_url(url).split('!')
        public_handle = path[0]
        file_id = self.get_id_from_public_handle(public_handle)
        return self.move(file_id, 4)

    def destroy(self, file_id):
        """
        Destroy a file by its private id
        """
        return self._api_request({
            'a': 'd',
            'n': file_id,
            'i': self.request_id
        })

    def destroy_url(self, url):
        """
        Destroy a file by its url
        """
        path = self._parse_url(url).split('!')
        public_handle = path[0]
        file_id = self.get_id_from_public_handle(public_handle)
        return self.destroy(file_id)

    def empty_trash(self):
        # get list of files in rubbish out
        files = self.get_files_in_node(4)

        # make a list of json
        if files != {}:
            post_list = []
            for file in files:
                post_list.append({"a": "d", "n": file, "i": self.request_id})
            return self._api_request(post_list)

    def download(self, file, dest_path=None, dest_filename=None):
        """
        Download a file by it's file object
        """
        return self._download_file(file_handle=None,
                                   file_key=None,
                                   file=file[1],
                                   dest_path=dest_path,
                                   dest_filename=dest_filename,
                                   is_public=False)

    def _export_file(self, node):
        node_data = self._node_data(node)
        self._api_request([{
            'a': 'l',
            'n': node_data['h'],
            'i': self.request_id
        }])
        return self.get_link(node)

    def export(self, path=None, node_id=None):
        nodes = self.get_files()
        if node_id:
            node = nodes[node_id]
        else:
            node = self.find(path)

        node_data = self._node_data(node)
        is_file_node = node_data['t'] == 0
        if is_file_node:
            return self._export_file(node)
        if node:
            try:
                # If already exported
                return self.get_folder_link(node)
            except (RequestError, KeyError):
                pass

        master_key_cipher = AES.new(a32_to_str(self.master_key), AES.MODE_ECB)
        ha = base64_url_encode(
            master_key_cipher.encrypt(node_data['h'].encode("utf8") +
                                      node_data['h'].encode("utf8")))

        share_key = secrets.token_bytes(16)
        ok = base64_url_encode(master_key_cipher.encrypt(share_key))

        share_key_cipher = AES.new(share_key, AES.MODE_ECB)
        node_key = node_data['k']
        encrypted_node_key = base64_url_encode(
            share_key_cipher.encrypt(a32_to_str(node_key)))

        node_id = node_data['h']
        request_body = [{
            'a':
            's2',
            'n':
            node_id,
            's': [{
                'u': 'EXP',
                'r': 0
            }],
            'i':
            self.request_id,
            'ok':
            ok,
            'ha':
            ha,
            'cr': [[node_id], [node_id], [0, 0, encrypted_node_key]]
        }]
        self._api_request(request_body)
        nodes = self.get_files()
        return self.get_folder_link(nodes[node_id])

    def download_url(self, url, dest_path=None, dest_filename=None,progressfunc=None,args=(),self_in=None):
        """
        Download a file by it's public url
        """
        path = self._parse_url(url).split('!')
        file_id = path[0]
        file_key = path[1]
        return self._download_file(
            file_handle=file_id,
            file_key=file_key,
            dest_path=dest_path,
            dest_filename=dest_filename,
            is_public=True,
            progressfunc=progressfunc,
            args=args,
            self_in=self_in
        )

    def download_iter_url(self, url, dest_path=None, dest_filename=None,progressfunc=None,args=(),self_in=None):
        """
        Download a file by it's public url
        """
        path = self._parse_url(url).split('!')
        file_id = path[0]
        file_key = path[1]
        return self._download_iter_file(
            file_handle=file_id,
            file_key=file_key,
            dest_path=dest_path,
            dest_filename=dest_filename,
            is_public=True,
            progressfunc=progressfunc,
            args=args,
            self_in=self_in
        )

    def _download_file(self,
                       file_handle,
                       file_key,
                       dest_path=None,
                       dest_filename=None,
                       is_public=False,
                       file=None,
                       progressfunc=None,
                       args=None,
                       f_data=None,
                       self_in=None):
        if file is None:
            if is_public:
                file_key = base64_to_a32(file_key)
                file_data = self._api_request({
                    'a': 'g',
                    'g': 1,
                    'p': file_handle
                })
            else:
                if f_data is None:
                    file_data = self._api_request({
                        'a': 'g',
                        'g': 1,
                        'n': file_handle
                    })
                else:
                    file_data = f_data

            k = (file_key[0] ^ file_key[4], file_key[1] ^ file_key[5],
                 file_key[2] ^ file_key[6], file_key[3] ^ file_key[7])
            iv = file_key[4:6] + (0, 0)
            meta_mac = file_key[6:8]
        else:
            file_data = self._api_request({'a': 'g', 'g': 1, 'n': file['h']})
            k = file['k']
            iv = file['iv']
            meta_mac = file['meta_mac']

        # Seems to happens sometime... When this occurs, files are
        # inaccessible also in the official also in the official web app.
        # Strangely, files can come back later.
        if 'g' not in file_data:
            raise RequestError('File not accessible anymore')
        file_url = file_data['g']
        file_size = file_data['s']
        attribs = base64_url_decode(file_data['at'])
        attribs = decrypt_attr(attribs, k)

        if dest_filename is not None:
            file_name = dest_filename
        else:
            file_name = attribs['n']

        import time

        chunk_por = 0
        chunkrandom = 100
        total = file_size
        time_start = time.time()
        time_total = 0
        size_per_second = 0

        input_file = requests.get(file_url, stream=True).raw

        if dest_path is None:
            dest_path = ''
        else:
            dest_path += '/'

        with tempfile.NamedTemporaryFile(mode='w+b',
                                         prefix='megapy_',
                                         delete=False) as temp_output_file:
            k_str = a32_to_str(k)
            counter = Counter.new(128,
                                  initial_value=((iv[0] << 32) + iv[1]) << 64)
            aes = AES.new(k_str, AES.MODE_CTR, counter=counter)

            mac_str = '\0' * 16
            mac_encryptor = AES.new(k_str, AES.MODE_CBC,
                                    mac_str.encode("utf8"))
            iv_str = a32_to_str([iv[0], iv[1], iv[0], iv[1]])

            for chunk_start, chunk_size in get_chunks(file_size):
                chunk = input_file.read(chunk_size)
                self_post = self
                if self_in:
                    self_post = self_in
                #funcion de progres
                if self_post.stoping:break
                chunk_por += len(chunk)
                size_per_second+=len(chunk);
                tcurrent = time.time() - time_start
                time_total += tcurrent
                time_start = time.time()
                if time_total>=1:
                    clock_time = (file_size - chunk_por) / (size_per_second)
                    if progressfunc:
                       file_name = str(file_name).split('/')[-1]
                       progressfunc(self_post,file_name,chunk_por,file_size,size_per_second,clock_time,args)
                       time_total = 0
                       size_per_second = 0

                chunk = aes.decrypt(chunk)
                temp_output_file.write(chunk)



                encryptor = AES.new(k_str, AES.MODE_CBC, iv_str)
                for i in range(0, len(chunk) - 16, 16):
                    block = chunk[i:i + 16]
                    encryptor.encrypt(block)

                # fix for files under 16 bytes failing
                if file_size > 16:
                    i += 16
                else:
                    i = 0

                block = chunk[i:i + 16]
                if len(block) % 16:
                    block += b'\0' * (16 - (len(block) % 16))
                mac_str = mac_encryptor.encrypt(encryptor.encrypt(block))

                file_info = os.stat(temp_output_file.name)
                logger.info('%s of %s downloaded', file_info.st_size,
                            file_size)
            file_mac = str_to_a32(mac_str)
            # check mac integrity
            if (file_mac[0] ^ file_mac[1],
                    file_mac[2] ^ file_mac[3]) != meta_mac:
                raise ValueError('Mismatched mac')
            output_path = Path(dest_path + file_name)
            shutil.move(temp_output_file.name, output_path)
            return output_path

    def _download_iter_file(self,
                       file_handle,
                       file_key,
                       dest_path=None,
                       dest_filename=None,
                       is_public=False,
                       file=None,
                       progressfunc=None,
                       args=None,
                       f_data=None,
                       self_in=None):
        if file is None:
            if is_public:
                file_key = base64_to_a32(file_key)
                file_data = self._api_request({
                    'a': 'g',
                    'g': 1,
                    'p': file_handle
                })
            else:
                if f_data is None:
                    file_data = self._api_request({
                        'a': 'g',
                        'g': 1,
                        'n': file_handle
                    })
                else:
                    file_data = f_data

            k = (file_key[0] ^ file_key[4], file_key[1] ^ file_key[5],
                 file_key[2] ^ file_key[6], file_key[3] ^ file_key[7])
            iv = file_key[4:6] + (0, 0)
            meta_mac = file_key[6:8]
        else:
            file_data = self._api_request({'a': 'g', 'g': 1, 'n': file['h']})
            k = file['k']
            iv = file['iv']
            meta_mac = file['meta_mac']

        # Seems to happens sometime... When this occurs, files are
        # inaccessible also in the official also in the official web app.
        # Strangely, files can come back later.
        if 'g' not in file_data:
            raise RequestError('File not accessible anymore')
        file_url = file_data['g']
        file_size = file_data['s']
        attribs = base64_url_decode(file_data['at'])
        attribs = decrypt_attr(attribs, k)

        if dest_filename is not None:
            file_name = dest_filename
        else:
            file_name = attribs['n']

        import time

        chunk_por = 0
        chunkrandom = 100
        total = file_size
        time_start = time.time()
        time_total = 0
        size_per_second = 0

        input_file = requests.get(file_url, stream=True).raw

        if dest_path is None:
            dest_path = ''
        else:
            dest_path += '/'

        with tempfile.NamedTemporaryFile(mode='w+b',
                                         prefix='megapy_',
                                         delete=False) as temp_output_file:
            k_str = a32_to_str(k)
            counter = Counter.new(128,
                                  initial_value=((iv[0] << 32) + iv[1]) << 64)
            aes = AES.new(k_str, AES.MODE_CTR, counter=counter)

            mac_str = '\0' * 16
            mac_encryptor = AES.new(k_str, AES.MODE_CBC,
                                    mac_str.encode("utf8"))
            iv_str = a32_to_str([iv[0], iv[1], iv[0], iv[1]])

            for chunk_start, chunk_size in get_chunks(file_size):
                chunk = input_file.read(chunk_size)
                self_post = self
                if self_in:
                    self_post = self_in
                #funcion de progres
                if self_post.stoping:break
                chunk_por += len(chunk)
                size_per_second+=len(chunk);
                tcurrent = time.time() - time_start
                time_total += tcurrent
                time_start = time.time()
                if time_total>=1:
                    clock_time = (file_size - chunk_por) / (size_per_second)
                    if progressfunc:
                       file_name = str(file_name).split('/')[-1]
                       progressfunc(self_post,file_name,chunk_por,file_size,size_per_second,clock_time,args)
                       time_total = 0
                       size_per_second = 0

                chunk = aes.decrypt(chunk)
                temp_output_file.write(chunk)



                encryptor = AES.new(k_str, AES.MODE_CBC, iv_str)
                for i in range(0, len(chunk) - 16, 16):
                    block = chunk[i:i + 16]
                    encryptor.encrypt(block)

                # fix for files under 16 bytes failing
                if file_size > 16:
                    i += 16
                else:
                    i = 0

                block = chunk[i:i + 16]
                if len(block) % 16:
                    block += b'\0' * (16 - (len(block) % 16))
                mac_str = mac_encryptor.encrypt(encryptor.encrypt(block))

                file_info = os.stat(temp_output_file.name)
                logger.info('%s of %s downloaded', file_info.st_size,
                            file_size)
                yield chunk
            return b''

    async def async_download_url(self, url, dest_path=None, dest_filename=None,progressfunc=None,args=(),self_in=None):
        """
        Download a file by it's public url
        """
        path = self._parse_url(url).split('!')
        file_id = path[0]
        file_key = path[1]
        return await self._async_download_file(
            file_handle=file_id,
            file_key=file_key,
            dest_path=dest_path,
            dest_filename=dest_filename,
            is_public=True,
            progressfunc=progressfunc,
            args=args,
            self_in=self_in
        )

    async def _async_download_file(self,
                       file_handle,
                       file_key,
                       dest_path=None,
                       dest_filename=None,
                       is_public=False,
                       file=None,
                       progressfunc=None,
                       args=None,
                       f_data=None,
                       self_in=None):
        if file is None:
            if is_public:
                file_key = base64_to_a32(file_key)
                file_data = self._api_request({
                    'a': 'g',
                    'g': 1,
                    'p': file_handle
                })
            else:
                if f_data is None:
                    file_data = self._api_request({
                        'a': 'g',
                        'g': 1,
                        'n': file_handle
                    })
                else:
                    file_data = f_data

            k = (file_key[0] ^ file_key[4], file_key[1] ^ file_key[5],
                 file_key[2] ^ file_key[6], file_key[3] ^ file_key[7])
            iv = file_key[4:6] + (0, 0)
            meta_mac = file_key[6:8]
        else:
            file_data = self._api_request({'a': 'g', 'g': 1, 'n': file['h']})
            k = file['k']
            iv = file['iv']
            meta_mac = file['meta_mac']

        # Seems to happens sometime... When this occurs, files are
        # inaccessible also in the official also in the official web app.
        # Strangely, files can come back later.
        if 'g' not in file_data:
            raise RequestError('File not accessible anymore')
        file_url = file_data['g']
        file_size = file_data['s']
        attribs = base64_url_decode(file_data['at'])
        attribs = decrypt_attr(attribs, k)

        if dest_filename is not None:
            file_name = dest_filename
        else:
            file_name = attribs['n']

        import time

        chunk_por = 0
        chunkrandom = 100
        total = file_size
        time_start = time.time()
        time_total = 0
        size_per_second = 0

        input_file = requests.get(file_url, stream=True).raw

        if dest_path is None:
            dest_path = ''
        else:
            dest_path += '/'

        with tempfile.NamedTemporaryFile(mode='w+b',
                                         prefix='megapy_',
                                         delete=False) as temp_output_file:
            k_str = a32_to_str(k)
            counter = Counter.new(128,
                                  initial_value=((iv[0] << 32) + iv[1]) << 64)
            aes = AES.new(k_str, AES.MODE_CTR, counter=counter)

            mac_str = '\0' * 16
            mac_encryptor = AES.new(k_str, AES.MODE_CBC,
                                    mac_str.encode("utf8"))
            iv_str = a32_to_str([iv[0], iv[1], iv[0], iv[1]])

            for chunk_start, chunk_size in get_chunks(file_size):
                chunk = input_file.read(chunk_size)
                self_post = self
                if self_in:
                    self_post = self_in
                #funcion de progres
                if self_post.stoping:break
                chunk_por += len(chunk)
                size_per_second+=len(chunk);
                tcurrent = time.time() - time_start
                time_total += tcurrent
                time_start = time.time()
                if time_total>=1:
                    clock_time = (file_size - chunk_por) / (size_per_second)
                    if progressfunc:
                       file_name = str(file_name).split('/')[-1]
                       await progressfunc(self_post,file_name,chunk_por,file_size,size_per_second,clock_time,args)
                       time_total = 0
                       size_per_second = 0

                chunk = aes.decrypt(chunk)
                temp_output_file.write(chunk)



                encryptor = AES.new(k_str, AES.MODE_CBC, iv_str)
                for i in range(0, len(chunk) - 16, 16):
                    block = chunk[i:i + 16]
                    encryptor.encrypt(block)

                # fix for files under 16 bytes failing
                if file_size > 16:
                    i += 16
                else:
                    i = 0

                block = chunk[i:i + 16]
                if len(block) % 16:
                    block += b'\0' * (16 - (len(block) % 16))
                mac_str = mac_encryptor.encrypt(encryptor.encrypt(block))

                file_info = os.stat(temp_output_file.name)
                logger.info('%s of %s downloaded', file_info.st_size,
                            file_size)
            file_mac = str_to_a32(mac_str)
            # check mac integrity
            if (file_mac[0] ^ file_mac[1],
                    file_mac[2] ^ file_mac[3]) != meta_mac:
                raise ValueError('Mismatched mac')
            output_path = Path(dest_path + file_name)
            shutil.move(temp_output_file.name, output_path)
            return output_path

    def upload(self, filename, dest=None, dest_filename=None):
        # determine storage node
        if dest is None:
            # if none set, upload to cloud drive node
            if not hasattr(self, 'root_id'):
                self.get_files()
            dest = self.root_id

        # request upload url, call 'u' method
        with open(filename, 'rb') as input_file:
            file_size = os.path.getsize(filename)
            ul_url = self._api_request({'a': 'u', 's': file_size})['p']

            # generate random aes key (128) for file
            ul_key = [random.randint(0, 0xFFFFFFFF) for _ in range(6)]
            k_str = a32_to_str(ul_key[:4])
            count = Counter.new(
                128, initial_value=((ul_key[4] << 32) + ul_key[5]) << 64)
            aes = AES.new(k_str, AES.MODE_CTR, counter=count)

            upload_progress = 0
            completion_file_handle = None

            mac_str = '\0' * 16
            mac_encryptor = AES.new(k_str, AES.MODE_CBC,
                                    mac_str.encode("utf8"))
            iv_str = a32_to_str([ul_key[4], ul_key[5], ul_key[4], ul_key[5]])
            if file_size > 0:
                for chunk_start, chunk_size in get_chunks(file_size):
                    chunk = input_file.read(chunk_size)
                    upload_progress += len(chunk)

                    encryptor = AES.new(k_str, AES.MODE_CBC, iv_str)
                    for i in range(0, len(chunk) - 16, 16):
                        block = chunk[i:i + 16]
                        encryptor.encrypt(block)

                    # fix for files under 16 bytes failing
                    if file_size > 16:
                        i += 16
                    else:
                        i = 0

                    block = chunk[i:i + 16]
                    if len(block) % 16:
                        block += makebyte('\0' * (16 - len(block) % 16))
                    mac_str = mac_encryptor.encrypt(encryptor.encrypt(block))

                    # encrypt file and upload
                    chunk = aes.encrypt(chunk)
                    output_file = requests.post(ul_url + "/" +
                                                str(chunk_start),
                                                data=chunk,
                                                timeout=self.timeout)
                    completion_file_handle = output_file.text
                    logger.info('%s of %s uploaded', upload_progress,
                                file_size)
            else:
                output_file = requests.post(ul_url + "/0",
                                            data='',
                                            timeout=self.timeout)
                completion_file_handle = output_file.text

            logger.info('Chunks uploaded')
            logger.info('Setting attributes to complete upload')
            logger.info('Computing attributes')
            file_mac = str_to_a32(mac_str)

            # determine meta mac
            meta_mac = (file_mac[0] ^ file_mac[1], file_mac[2] ^ file_mac[3])

            dest_filename = dest_filename or os.path.basename(filename)
            attribs = {'n': dest_filename}

            encrypt_attribs = base64_url_encode(
                encrypt_attr(attribs, ul_key[:4]))
            key = [
                ul_key[0] ^ ul_key[4], ul_key[1] ^ ul_key[5],
                ul_key[2] ^ meta_mac[0], ul_key[3] ^ meta_mac[1], ul_key[4],
                ul_key[5], meta_mac[0], meta_mac[1]
            ]
            encrypted_key = a32_to_base64(encrypt_key(key, self.master_key))
            logger.info('Sending request to update attributes')
            # update attributes
            data = self._api_request({
                'a':
                'p',
                't':
                dest,
                'i':
                self.request_id,
                'n': [{
                    'h': completion_file_handle,
                    't': 0,
                    'a': encrypt_attribs,
                    'k': encrypted_key
                }]
            })
            logger.info('Upload complete')
            return data

    def _mkdir(self, name, parent_node_id):
        # generate random aes key (128) for folder
        ul_key = [random.randint(0, 0xFFFFFFFF) for _ in range(6)]

        # encrypt attribs
        attribs = {'n': name}
        encrypt_attribs = base64_url_encode(encrypt_attr(attribs, ul_key[:4]))
        encrypted_key = a32_to_base64(encrypt_key(ul_key[:4], self.master_key))

        # update attributes
        data = self._api_request({
            'a':
            'p',
            't':
            parent_node_id,
            'n': [{
                'h': 'xxxxxxxx',
                't': 1,
                'a': encrypt_attribs,
                'k': encrypted_key
            }],
            'i':
            self.request_id
        })
        return data

    def _root_node_id(self):
        if not hasattr(self, 'root_id'):
            self.get_files()
        return self.root_id

    def create_folder(self, name, dest=None):
        dirs = tuple(dir_name for dir_name in str(name).split('/') if dir_name)
        folder_node_ids = {}
        for idx, directory_name in enumerate(dirs):
            existing_node_id = self.find_path_descriptor(directory_name)
            if existing_node_id:
                folder_node_ids[idx] = existing_node_id
                continue
            if idx == 0:
                if dest is None:
                    parent_node_id = self._root_node_id()
                else:
                    parent_node_id = dest
            else:
                parent_node_id = folder_node_ids[idx - 1]
            created_node = self._mkdir(name=directory_name,
                                       parent_node_id=parent_node_id)
            node_id = created_node['f'][0]['h']
            folder_node_ids[idx] = node_id
        return dict(zip(dirs, folder_node_ids.values()))

    def rename(self, file, new_name):
        file = file[1]
        # create new attribs
        attribs = {'n': new_name}
        # encrypt attribs
        encrypt_attribs = base64_url_encode(encrypt_attr(attribs, file['k']))
        encrypted_key = a32_to_base64(encrypt_key(file['key'],
                                                  self.master_key))
        # update attributes
        return self._api_request([{
            'a': 'a',
            'attr': encrypt_attribs,
            'key': encrypted_key,
            'n': file['h'],
            'i': self.request_id
        }])

    def move(self, file_id, target):
        """
        Move a file to another parent node
        params:
        a : command
        n : node we're moving
        t : id of target parent node, moving to
        i : request id

        targets
        2 : root
        3 : inbox
        4 : trash

        or...
        target's id
        or...
        target's structure returned by find()
        """

        # determine target_node_id
        if type(target) == int:
            target_node_id = str(self.get_node_by_type(target)[0])
        elif type(target) in (str, ):
            target_node_id = target
        else:
            file = target[1]
            target_node_id = file['h']
        return self._api_request({
            'a': 'm',
            'n': file_id,
            't': target_node_id,
            'i': self.request_id
        })

    def add_contact(self, email):
        """
        Add another user to your mega contact list
        """
        return self._edit_contact(email, True)

    def remove_contact(self, email):
        """
        Remove a user to your mega contact list
        """
        return self._edit_contact(email, False)

    def _edit_contact(self, email, add):
        """
        Editing contacts
        """
        if add is True:
            l = '1'  # add command
        elif add is False:
            l = '0'  # remove command
        else:
            raise ValidationError('add parameter must be of type bool')

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            ValidationError('add_contact requires a valid email address')
        else:
            return self._api_request({
                'a': 'ur',
                'u': email,
                'l': l,
                'i': self.request_id
            })

    def get_public_url_info(self, url):
        """
        Get size and name from a public url, dict returned
        """
        file_handle, file_key = self._parse_url(url).split('!')
        return self.get_public_file_info(file_handle, file_key)

    def import_public_url(self, url, dest_node=None, dest_name=None):
        """
        Import the public url into user account
        """
        file_handle, file_key = self._parse_url(url).split('!')
        return self.import_public_file(file_handle,
                                       file_key,
                                       dest_node=dest_node,
                                       dest_name=dest_name)

    def get_public_file_info(self, file_handle, file_key):
        """
        Get size and name of a public file
        """
        data = self._api_request({'a': 'g', 'p': file_handle, 'ssm': 1})
        if isinstance(data, int):
            raise RequestError(data)

        if 'at' not in data or 's' not in data:
            raise ValueError("Unexpected result", data)

        key = base64_to_a32(file_key)
        k = (key[0] ^ key[4], key[1] ^ key[5], key[2] ^ key[6],
             key[3] ^ key[7])

        size = data['s']
        unencrypted_attrs = decrypt_attr(base64_url_decode(data['at']), k)
        if not unencrypted_attrs:
            return None
        result = {'size': size, 'name': unencrypted_attrs['n']}
        return result

    def import_public_file(self,
                           file_handle,
                           file_key,
                           dest_node=None,
                           dest_name=None):
        """
        Import the public file into user account
        """
        # Providing dest_node spare an API call to retrieve it.
        if dest_node is None:
            # Get '/Cloud Drive' folder no dest node specified
            dest_node = self.get_node_by_type(2)[1]

        # Providing dest_name spares an API call to retrieve it.
        if dest_name is None:
            pl_info = self.get_public_file_info(file_handle, file_key)
            dest_name = pl_info['name']

        key = base64_to_a32(file_key)
        k = (key[0] ^ key[4], key[1] ^ key[5], key[2] ^ key[6],
             key[3] ^ key[7])

        encrypted_key = a32_to_base64(encrypt_key(key, self.master_key))
        encrypted_name = base64_url_encode(encrypt_attr({'n': dest_name}, k))
        return self._api_request({
            'a':
            'p',
            't':
            dest_node['h'],
            'n': [{
                'ph': file_handle,
                't': 0,
                'a': encrypted_name,
                'k': encrypted_key
            }]
        })
