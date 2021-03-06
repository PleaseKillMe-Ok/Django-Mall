# -*- coding: utf-8 -*-
# @Time  : 2020/8/16 下午4:33
# @Author : 司云中
# @File : storage.py
# @Software: Pycharm
from django.core.files import File
from django.core.files.storage import Storage

from Emall.loggings import Logging
from Emall.settings import FDFS_URL, FDFS_CLIENT_CONF
from django.utils.deconstruct import deconstructible

from fdfs_client.client import Fdfs_client, get_tracker_conf

common_logger = Logging.logger('django')


@deconstructible
class FastDfsStorage(Storage):
    """操作文件通过file_id"""

    def __init__(self, base_url=None, client_conf=None):
        """
        初始化
        :param base_url:构造图片上传的基本url，包括域名，已经搭配nginx
        :param client_conf:FastDfs客户端的配置字典
        """
        if base_url is None:
            base_url = FDFS_URL
        self.base_url = base_url
        if client_conf is None:
            client_conf = FDFS_CLIENT_CONF
        self.client_conf = client_conf
        self.client = Fdfs_client(get_tracker_conf(self.client_conf))

    def _open(self, name, mode='rb'):
        """返回封装后的文件对象"""
        return File(open(self.path(name), mode))

    def open(self, name, mode='rb'):
        """
        从FastDfs中取出文件
        :param name: 文件名
        :param mode: 打开的模式
        :return:
        """
        return self._open(name, mode)

    def _save(self, name, content):
        """
        存储文件到FastDfs上
        :param name:  文件名（无卵用)
        :param content: 打开的file对象
        :return:
        """
        filebuffer = content.read()  # 读取二进制内容
        is_save, ret_upload = self.upload(filebuffer)
        return ret_upload.get('Remote file_id').decode() if is_save else None

    def save(self, name, content, max_length=None):
        """
        Save new content to the file specified by name. The content should be
        a proper File object or any Python file-like object, ready to be read
        from the beginning.
        """
        # Get the proper name for the file, as it will actually be saved.
        # 要不要name无所谓，只是为了尽量不改底层源码
        if name is None:
            name = content.name

        if not hasattr(content, 'chunks'):
            content = File(content, name)

        name = self.get_available_name(name, max_length=max_length)  # 截取固定大小的文件名长度
        return self._save(name, content)


    def update(self, filebuffer, remote_file_id):
        """
        修改文件内容
        :param local_path: 本地文件名
        :param remote_file_id:  fastdfs中的file_id
        @return: dictionary {
            'Status'     : 'Modify successed.',
            'Storage IP' : storage_ip
        }
        """

        try:
            remote_file_id = bytes(remote_file_id.encode("utf-8"))  # 旧的file_id
            ret_update = self.client.modify_by_buffer(filebuffer, remote_file_id)
            if ret_update.get("Status") != 'Modify successed.':
                raise Exception
            return True, ret_update
        except Exception as e:
            common_logger.info(e)
            return None, "文件更新失败"

    def upload(self, filebuffer, meta_dict=None):
        """
        保存文件时回调的函数
        保存在FastDfs中
        通过client来操作
        :param name: 文件名
        :param filebuffer: 文件内容（二进制）
        :param meta_dict: dictionary e.g.:{
            'ext_name'  : 'jpg',
            'file_size' : '10240B',
            'width'     : '160px',
            'hight'     : '80px'
        }
        @return dict {
            'Group name'      : group_name,
            'Remote file_id'  : remote_file_id,
            'Status'          : 'Upload successed.',
            'Local file name' : '',
            'Uploaded size'   : upload_size,
            'Storage IP'      : storage_ip
        } if success else None
        """
        try:
            ret_upload = self.client.upload_by_buffer(filebuffer)
            if ret_upload.get("Status") != "Upload successed.":
                raise Exception
            return True, ret_upload
            # file_name为bytes类型，只能返回str类型，不然会报错
        except Exception as e:
            return False, None

    def url(self, name):
        """
        返回文件的完整URL路径给前端
        :param name: 数据库中保存的文件名
        :return: 完整的URL
        """
        return self.base_url + '/' + name

    def exists(self, name):
        """
        判断文件是否存在，FastDFS可以自行解决文件的重名问题
        所以此处返回False，告诉Django上传的都是新文件
        :param name:  文件名
        :return: False
        """
        return False

    def download_to_file(self, local_path, remote_file_id):
        """
        从FastDfs分布式文件系统进行下载文件,保存成文件格式
        :param local_path: 本地保存文件路径
        :param remote_file_id: 上传到FastDfs文件系统中自动生成的文件路径即文件id,
        :return True/False, dict {
            'Remote file_id'  : remote_file_id,
            'Content'         : local_filename,
            'Download size'   : downloaded_size,
            'Storage IP'      : storage_ip
        }
        """
        try:
            ret_download = self.client.download_to_file(local_path, remote_file_id)
            return True, ret_download
        except Exception as e:
            return False, None

    def download_to_buffer(self, remote_file_id, offset=0, down_bytes=0):
        """
        通过文件名从FastDfs上下载文件,存储为buffer格式
        :param local_filename: 本地文件名，一般存于数据库
        :param remote_file_id: 远程文件id
        :param offset: 文件数据起始偏移量
        :param down_bytes: 需要下载的文件大小
        :return:return True/False, dict {
            'Remote file_id'  : remote_file_id,
            'Content'         : file_buffer,
            'Download size'   : downloaded_size,
            'Storage IP'      : storage_ip
        }
        """
        try:
            ret_download = self.client.download_to_buffer(remote_file_id, offset, down_bytes)
            return True, ret_download
        except Exception as e:
            return False, None


    def modify_by_buffer(self, filebuffer, appender_fileid, offset=0):
        """
        通过buffer修改文件内容
        :param filebuffer:文件buffer
        :param appender_fileid:远程文件id
        :param offset:起始偏移量
        :return:True/False, dictionary {
            'Status'     : 'Modify successed.',
            'Storage IP' : storage_ip
        }
        """

        try:
            ret_modify = self.client.modify_by_buffer(filebuffer, appender_fileid, offset)
            return True, ret_modify
        except Exception as e:
            return False, None

    def delete(self, remote_file_id):
        """
        从FastDfs分布式文件系统中将文件删除
        :param remote_file_id: 上传到FastDfs文件系统中自动生成的文件路径即文件id
        @return True/False, tuple ('Delete file successed.', remote_file_id, storage_ip)
        """
        try:
            ret_delete = self.client.delete_file(remote_file_id)
            return True, ret_delete
        except Exception as e:
            return False, None




