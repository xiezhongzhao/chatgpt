#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：stock
@File    ：log.py
@Author  ：Xie Zhongzhao
@Date    ：2023/2/1 14:16
'''

import logging
import os

def create_logger(fp):
    # 打印日志的时间、日志级别名称、日志信息
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
    console_logger = logging.getLogger('ConsoleLoggoer')
    file_logger = logging.getLogger('FileLogger')

    # 向文件输出日志信息
    file_handler = logging.FileHandler(fp, mode='a', encoding='utf-8')
    file_logger.addHandler(file_handler)
    return console_logger, file_logger

# 创建logger
console_logger, file_logger = create_logger(os.path.join('./', 'log.log'))  #写入某文件的命令

