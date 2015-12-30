#!/usr/bin/env python3
"""
html2warc creates warc files from local web resources
"""

__date__ = '2015/12/30'
__version__ = '0.7'
__status__ = 'Testing'
__license__ = 'The MIT License (MIT)'
__copyright__ = 'Copyright (c) 2014 Steffen Fritz'
__author__ = 'steffen fritz'
__maintainer__ = 'steffen fritz'
__contact__ = 'sfnfzs2600@gmail.com'


import os
import sys
import uuid
import datetime
import mimetypes
import re

# possible names for an index file, listed as compiled regexp,
# in order of preference
index_filenames = [
    re.compile(r'(index)\.(html?|asp|php)', re.I),  # most common
    re.compile(r'welcome\.html?', re.I)             # AOL server
]

def source_to_warc(source_dir, targetwarc, createdate, rooturl):
    """
    :param source_dir: source directory
    :param targetwarc: output warc file
    :param createdate: bag creation date
    :param rooturl:    arbitrary URL
    :type: string objects
    """
    for rootdir, _, files in os.walk(source_dir):
        for file_ in files:
            
            possible_filenames_ = [file_]

            for index_filename_ in index_filenames:
                if index_filename_.fullmatch(file_):
                    possible_filenames_.append('')
                    continue # only one index per directory!

            source_file_ = os.path.join(rootdir, file_)
            mime_type_ = mimetypes.guess_type(source_file_)
            file_size_ = os.path.getsize(source_file_)
            block_length = 110 # init with len of network header

            rootdir_parts = rootdir.split('/')
            source_dir_parts = source_dir.split('/')
            source_file_uri_parts = []
            path_step = 0
            for segment in rootdir_parts:
                if  len(source_dir_parts) < path_step+1 or segment != source_dir_parts[path_step]:
                    source_file_uri_parts.append(segment)
                path_step = path_step + 1

            for possible_filename_ in possible_filenames_:

                source_file_uri = rooturl + '/'.join(source_file_uri_parts)+ '/' + possible_filename_

                print("{}\t[{}]\t{}b".format(source_file_uri, mime_type_[0], file_size_))

                with open(targetwarc, "a", newline="\r\n") as fw:
                    fw.write("WARC/1.0\n")
                    fw.write("WARC-Type: response\n")

                    fw.write("WARC-Target-URI: " + source_file_uri + "\n")

                    fw.write("WARC-Record-ID: <urn:uuid:" + str(uuid.uuid4()) + ">\n")
                    fw.write("WARC-Date: " + str(createdate) + "\n")
                    fw.write("Content-Type: " + "application/http;msgtype=response" + "\n")
                    fw.write("WARC-Identified-Payload-Type: " + str(mime_type_[0]) + "\n")

                    block_length = block_length + file_size_ + len(str(mime_type_[0])) + len(str(createdate))
                    fw.write("Content-Length: " + str(block_length) + "\n")
                    fw.write("\n")

                    # network protocol information
                    fw.write("HTTP/1.1 200 OK\n")
                    fw.write("DATE: " + str(createdate) + "\n")
                    fw.write("Accept-Ranges: bytes" + "\n")
                    fw.write("Connection: close" + "\n")
                    fw.write("Content-Type: " + str(mime_type_[0]) + "\n")
                    fw.write("Content-Length: " + str(file_size_) + "\n")
                    fw.write("\n")

                with open(source_file_, "rb") as fd:
                    for line_ in fd:
                        with open(targetwarc, "ab") as fw:
                            fw.write(line_)
                    fw = open(targetwarc, "a")
                    fw.write("\r\n\r\n")


def write_init_record(targetwarc, createdate):
    """
    this function writes the warcinfo record
    :param targetwarc: the output file
    :ptype string
    :return
    """
    content_length = 2
    record_ = []

    record_.append("software: html2warc http://hub.darcs.net/ampoffcom/html2warc\n")
    record_.append("format: WARC File Format 1.0\n")
    record_.append("conformsTo: http://bibnum.bnf.fr/WARC/WARC_ISO_28500_version1_latestdraft.pdf\n")
    record_.append("description: warc file created from offline data\n")
    for n in range(0, len(record_)):
        content_length += len(record_[n])

    with open(targetwarc, "w", newline="\r\n") as fd:
        fd.write("WARC/1.0\n")
        fd.write("WARC-Type: warcinfo\n")
        fd.write("WARC-Date: " + createdate + "\n")
        fd.write("WARC-Filename: " + targetwarc + "\n")
        fd.write("WARC-Record-ID: <urn:uuid:" + str(uuid.uuid4()) + ">\n")
        fd.write("Content-Type: application/warc-fields\n")
        fd.write("Content-Length: " + str(content_length) + "\n")
        fd.write("\n")
        for line in record_:
            fd.write(line)
        fd.write("\n\n\n")


def help_message():
    """
    prints a usage message if html2warc is not executed with 3 arguments
    """
    print("\nUSAGE: html2warc.py ROOTURL SOURCEDIR TARGETWARC\n")


def main():
    """
    :return exit code
    :rtype int
    """
    if len(sys.argv) != 4:
        help_message()
        sys.exit(0)
    if len(sys.argv) == 4:
        try:
            rooturl = sys.argv[1]
            if not rooturl.endswith("/"):
                rooturl += "/"
            sourcedir = sys.argv[2]
            targetwarc = sys.argv[3] + ".warc"
        except IOError as err:
            print(str(err))
            sys.exit(1)

    createdate = datetime.datetime.now().isoformat()
    write_init_record(targetwarc, createdate)
    source_to_warc(sourcedir, targetwarc, createdate, rooturl)

    return 0


if __name__ == '__main__':
    main()
