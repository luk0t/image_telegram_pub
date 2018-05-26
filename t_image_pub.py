import os
from typing import Type
import peewee as pw
import telegram
import settings
from collections import namedtuple


statuses = namedtuple('Statuses', ['not_published', 'published', 'not_found'])
image_statuses = statuses._make([0, 1, 2])

IMAGES = {'jpg', 'jpeg', 'png'}
DB = pw.SqliteDatabase(settings.DATABASE_NAME)


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
        *name, ext = file.split('.')
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
    image_file = image.filter(status=image_statuses.not_published).limit(1)
    full_path = os.path.join(path, image_file[0].image)
    try:
        with open(full_path, 'rb') as photo:
            bot.send_photo(chat_id=channel, photo=photo)
    except:
        print('!3!!!!!!!!!!!!!!!')
        exit(1)
    else:
        image_file[0].status = statuses.published

