from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from urllib.request import urlopen
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile


class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(null=False, blank=False)

    def __str__(self):
        return self.user

upload_path = ''
class ObjectWithImageField(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=upload_path, null= True, blank=True)
    image_url = models.URLField(blank=True, null=True)
    
    def get_image_from_url(self, url):
       img_tmp = NamedTemporaryFile(delete=True)
       with urlopen(url) as uo:
           assert uo.status == 200
           img_tmp.write(uo.read())
           img_tmp.flush()
       img = File(img_tmp)
       self.image.save("image.jpeg", img)
       self.image_url = url

class Drive(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    photo = models.ImageField(null=False, blank=False)

    def __str__(self):
        return self.user