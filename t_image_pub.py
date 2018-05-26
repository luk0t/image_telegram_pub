import os
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


def init_base():
    DB.connect()
    DB.create_tables([Image])


def add_images(path: str, image: Image)-> None:
    """ Add new images to database
    :param path: path to directory with images files
    :param image: peewee image class
    :return: None
    """
    for file in os.listdir(path):
        *name, ext = file.split('.')
        if ext.lower() in IMAGES:
            image.create(image=file)


def clean_images_published(path: str, image: Image)-> None:
    """Delete already published images
    :param path: path to directory with images
    :param image: Image class of db
    :return: None
    """
    for record in image.filter(status=image_statuses.published):
        full_path = os.path.join(path, record.image)
        os.remove(full_path)


def public_image(token: str, path: str, channel: str, image: Image)-> None:
    """ Public one image in telegram channel
    :param token: api token for telegram bot
    :param path: path to directory with images
    :param channel: chanel name for publication
    :param image: Image class of db
    :return: None
    """
    bot = telegram.Bot(token=token)
    image_file = image.filter(status=image_statuses.not_published).limit(1)
    full_path = os.path.join(path, image_file.image)
    try:
        bot.send_photo(chat_id=channel, photo=open(full_path, 'rb'))
    except:
        exit(1)
    else:
        image_file.image.status = statuses.published
        image_file.save()

