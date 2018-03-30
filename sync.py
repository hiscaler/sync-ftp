# -*- encode: utf-8 -*-
import configparser
import os

import paramiko
import stat

"""FTP 文件同步"""


class Sync(object):
    _config = {
        'ip': None,
        'port': 21,
        'username': None,
        'password': None
    }

    _count = 0

    _remote_dir = None

    _local_dir = None

    def __init__(self, config, remote_dir, local_dir):
        for key in config:
            if key in self._config:
                value = config[key]
                if key is 'port':
                    value = int(value)
                else:
                    value = str(value)

                self._config[key] = value

        self._remote_dir = remote_dir
        self._local_dir = local_dir

    def open(self):
        pass

    def get_files(self, current_directory):
        pass

    def download(self):
        pass

    def upload(self):
        pass

    def close(self):
        pass


class SyncSftp(Sync):
    _transport = None
    _ftp = None

    def open(self):
        try:
            if self._transport is None:
                self._transport = paramiko.Transport((self._config['ip'], self._config['port']))

            self._transport.connect(username=self._config['username'], password=self._config['password'])

            if self._ftp is None:
                self._ftp = paramiko.SFTP.from_transport(self._transport)

        except BaseException as e:
            self.close()
            print(str(e))

    def get_files(self, path, recursion=False):
        files = []
        self._ftp.chdir(path)
        for name in self._ftp.listdir(path):
            if recursion:
                file_attr = self._ftp.lstat(path + '/' + name)
                if stat.S_ISDIR(file_attr.st_mode):
                    files.extend(self.get_files(path + '/' + name, recursion))
                elif stat.S_ISREG(file_attr.st_mode):
                    files.append(path + '/' + name)
            else:
                files.append(path + '/' + name)

        return files

    def download(self, path, recursion=True):
        file_attr = self._ftp.lstat(path)
        if stat.S_ISDIR(file_attr.st_mode):
            files = self.get_files(path, recursion)
        elif stat.S_ISREG(file_attr.st_mode):
            files = [path]
        else:
            files = []

        for file in files:
            local_path = file.replace(self._remote_dir, self._local_dir)
            file_dir = os.path.dirname(local_path)
            file_dir = file_dir.replace('/', os.sep)
            if not os.path.exists(file_dir):
                print("Make Dirs = " + file_dir)
                os.makedirs(file_dir)

            if os.path.isdir(local_path):
                continue

            if not os.path.exists(local_path):
                self._count += 1
                print("%s: Download %s file..." % (self._count, file))
                self._ftp.get(file, localpath=local_path)
            else:
                print("Ignore %s file..." % file)

    def close(self):
        if self._transport is not None:
            self._transport.close()

        if self._ftp is not None:
            self._ftp.close()


if __name__ == '__main__':
    cfg = configparser.ConfigParser()
    cfg.read('conf')
    if 'ftp' in cfg:
        ftp_config = cfg['ftp']
    else:
        raise BaseException

    config = {
        'ip': ftp_config['ip'],
        'port': ftp_config['port'],
        'username': ftp_config['username'],
        'password': ftp_config['password']
    }
    remote_dir = str(ftp_config['remote_dir'])
    local_dir = str(ftp_config['local_dir'])

    try:
        sftp = SyncSftp(config, remote_dir=remote_dir, local_dir=local_dir)
        sftp.open()
        root_dirs = sftp.get_files(remote_dir, False)
        for root_dir in root_dirs:
            sftp.download(root_dir)

    finally:
        sftp.close()
