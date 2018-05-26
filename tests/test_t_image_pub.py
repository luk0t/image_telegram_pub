import peewee as pw
import os
import shutil
import random
import unittest
import string
import t_image_pub
import settings


def generate_images_files():
    images = []
    for i in range(10):
        images.append(
            "{}.jpg".format(''.join(
                random.choices(string.ascii_letters, k=5))))
    return images


path = '/tmp/test_t_image'
images_dir = 'files'


class TestAddImages(unittest.TestCase):
    def setUp(self):
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)
        self.db = pw.SqliteDatabase(os.path.join(path, 'test.db'))
        self.db.connect()

        class Image(t_image_pub.Image):
            class Meta:
                database = self.db
        self.image = Image
        self.db.create_tables([self.image])

    def test_files(self):
        self.images = generate_images_files()
        for f in self.images:
            open(os.path.join(path, f), 'a').close()
        t_image_pub.add_images(path, self.image)
        result = self.image.select()
        self.assertEqual(len(result), len(self.images))
        for i in result:
            self.assertIn(i.image, self.images)

    def test_duplicate_image(self):
        self.images = generate_images_files()
        for f in self.images:
            open(os.path.join(path, f), 'a').close()
        t_image_pub.add_images(path, self.image)
        t_image_pub.add_images(path, self.image)
        result = self.image.select()
        self.assertEqual(len(result), len(self.images))
        for i in result:
            self.assertIn(i.image, self.images)


class TestCleanImagesPublished(unittest.TestCase):
    def setUp(self):
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)
        self.db = pw.SqliteDatabase(os.path.join(path, 'test.db'))
        self.db.connect()

        class Image(t_image_pub.Image):
            class Meta:
                database = self.db
        self.image = Image
        self.db.create_tables([self.image])
        self.images = generate_images_files()
        for f in self.images:
            open(os.path.join(path, f), 'a').close()
        print(os.listdir(path))
        for i in self.images:
            self.image.create(
                image=i, status=t_image_pub.image_statuses.published)

    def test_clean_images(self):
        t_image_pub.clean_images_published(path, self.image)
        for f in os.listdir(path):
            self.assertFalse(f.endswith('.jpg'))

    def test_clean_not_exists(self):
        os.remove(os.path.join(path, self.images[0]))
        t_image_pub.clean_images_published(path, self.image)
        for f in os.listdir(path):
            self.assertFalse(f.endswith('.jpg'))


class TestPublicImage(unittest.TestCase):
    def setUp(self):
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)
        self.db = pw.SqliteDatabase(os.path.join(path, 'test.db'))
        self.db.connect()

        class Image(t_image_pub.Image):
            class Meta:
                database = self.db
        self.image = Image
        self.db.create_tables([self.image])

    def test_public_image(self):
        print(os.listdir(path))
        test_path = os.path.dirname(os.path.abspath(__file__))
        files_path = os.path.join(test_path, images_dir)
        print(files_path)
        print(os.listdir(files_path))
        for file in os.listdir(files_path):
            *name, ext = file.split('.')
            print(ext)
            if ext.lower() in t_image_pub.IMAGES:
                try:
                    self.image.create(image=file)
                except pw.IntegrityError:
                    pass
        t_image_pub.public_image(settings.TOKEN,
                                 files_path,
                                 settings.CHANNEL,
                                 self.image)
if __name__ == '__main__':
    unittest.main()
