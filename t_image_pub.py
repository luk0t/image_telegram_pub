"""
Simple telegram image publisher
"""

import os
import argparse
import sys
import logging
from typing import Type
from collections import namedtuple
import peewee as pw
import telegram


Statuses = namedtuple('Statuses', ['not_published',
                                   'published',
                                   'not_found',
                                   'not_valid'])
image_statuses = Statuses._make([0, 1, 2, 4])
logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(module)s  '
                              '%(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)

work_path = os.path.dirname(os.path.abspath(__file__))

IMAGES = {'jpg', 'jpeg', 'png'}
DB = pw.SqliteDatabase(os.path.join(work_path, os.getenv('DATABSE_NAME')))


class Image(pw.Model):
    image = pw.CharField(max_length=255, unique=True)
    status = pw.SmallIntegerField(default=0)

    class Meta:
        database = DB


def add_images(path: str, image: Type[Image])-> None:
    """ Add new images to database
    :param path: path to directory with images files
    :param image: peewee image class
    :return: None
    """
    for file in os.listdir(path):
        *_, ext = file.split('.')
        if ext.lower() in IMAGES:
            try:
                image.create(image=file)
            except pw.IntegrityError:
                pass


def clean_images_published(path: str, image: Type[Image])-> None:
    """Delete already published images
    :param path: path to directory with images
    :param image: Image class of db
    :return: None
    """
    for record in image.filter(status=image_statuses.published):
        full_path = os.path.join(path, record.image)
        try:
            os.remove(full_path)
        except FileNotFoundError:
            pass


def public_image(token: str,
                 path: str,
                 channel: str,
                 image: Type[Image])-> None:
    """ Public one image in telegram channel
    :param token: api token for telegram bot
    :param path: path to directory with images
    :param channel: chanel name for publication
    :param image: Image class of db
    :return: None
    """
    bot = telegram.Bot(token=token)
    while True:
        image_file = image.filter(status=image_statuses.not_published).limit(1)
        if len(image_file) == 0:
            logger.warning("Can't find image to public")
            exit(1)
        full_path = os.path.join(path, image_file[0].image)
        try:
            with open(full_path, 'rb') as photo:
                bot.send_photo(chat_id=channel, photo=photo)
        except FileNotFoundError:
            logger.error("FileNotFound {}".format(image_file[0].image))
            image_file[0].status = image_statuses.not_found
            image_file[0].save()
            continue
        except telegram.error.BadRequest:
            logger.error("Bad file {}".format(image_file[0].image))
            image_file[0].status = image_statuses.not_valid
            image_file[0].save()
            continue
        else:
            image_file[0].status = image_statuses.published
            image_file[0].save()
            break


def main(argv):
    """
    :param argv: main args
    :return: None
    """
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-p', '--public', help='Public next image to chanel',
                       action='store_true')
    group.add_argument('-c', '--clean', help='Delete already published files',
                       action='store_true')
    group.add_argument('-a', '--add', help='Add new images to database',
                       action='store_true')
    DB.create_tables([Image])
    args = parser.parse_args(argv)
    if args.public:
        public_image(os.getenv('TOKEN'),
                     os.getenv('IMAGE_PATH'),
                     os.getenv('CHANNEL'),
                     Image)
    elif args.clean:
        clean_images_published(os.getenv('IMAGES_PATH'), Image)
    elif args.add:
        add_images(os.getenv('IMAGES_PATH'), Image)


if __name__ == '__main__':
    main(sys.argv[1:])
