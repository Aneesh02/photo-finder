from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import logout, login
from django.http import HttpResponse
from home.models import Photo,ObjectWithImageField,Drive
import string
import random
import re

#Required for face_recognition
from imutils import paths
import face_recognition
import cv2
import os

#For getting drive files
import pandas as pd
import io
import pickle
import os
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request


def Create_Service(client_secret_file, api_name, api_version, *scopes):
    print(client_secret_file, api_name, api_version, scopes, sep='-')
    CLIENT_SECRET_FILE = client_secret_file
    API_SERVICE_NAME = api_name
    API_VERSION = api_version
    SCOPES = [scope for scope in scopes[0]]
    print(SCOPES)

    cred = None

    pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}.pickle'
    # print(pickle_file)

    if os.path.exists(pickle_file):
        with open(pickle_file, 'rb') as token:
            cred = pickle.load(token)

    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            cred = flow.run_local_server()

        with open(pickle_file, 'wb') as token:
            pickle.dump(cred, token)

    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
        print(API_SERVICE_NAME, 'service created successfully')
        return service
    except Exception as e:
        print('Unable to connect.')
        print(e)
        return None

def convert_to_RFC_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + 'Z'
    return dt

# Create your views here.
def login(request):
    global roomcode
    roomcode_status = 0
    user = request.user
    if user.is_anonymous:
        return render(request, 'login.html')
    elif request.method == "POST":
        images = request.FILES.getlist("images")
        roomCode = request.POST.get("roomCode")
        roomcode_status=1
        for image in images:
            print("Boo",image)
            photo = Photo.objects.create(user=user, image=image)
            photo.save()
        
    
    if roomcode_status == 0:
        return render(request, 'login.html')
    else:
        pass
    photos = Photo.objects.filter(user=user)
    count = photos.count()
    print("Count",count)
    context = {"photos": photos, "count": count, "roomCode": roomCode}
    roomcode = roomCode
    return render(request, "home.html", context)


    

def home(request):
    user = request.user
    if user.is_anonymous:
        return redirect('/')
    else:
        return render(request, 'home.html')


def deletePhoto(request):
    user = request.user
    photos = Photo.objects.filter(user=user)
    if request.method == "POST":
        photos.delete()
    photos = Photo.objects.filter(user=user)
    count = photos.count()
    context = {"photos": photos, "count": count}
    return render(request, "home.html", context)

def process(request):
    global roomcode
    user = request.user
    name = user
    if user.is_anonymous:
        return redirect("/login")
    
    photos = Photo.objects.filter(user=user)
    count = photos.count()
    if photos.count() == 0:
        context = {
            "error_message": "No photos to process.\n Upload some photos and then Try again"
        }
        return render(request, "404.html", context)

    imagePaths = [("static/images/" + str(photo.image)) for photo in photos]
    print(imagePaths)
    knownEncodings = []
    for (i, imagePath) in enumerate(imagePaths):
        # extract the person name from the image path
        print("[INFO] processing image {}/{}".format(i + 1,len(imagePaths)))
        
        # load the input image and convert it from BGR (OpenCV ordering)
        # to dlib ordering (RGB)
        image = cv2.imread(imagePath)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # detect the (x, y)-coordinates of the bounding boxes
        # corresponding to each face in the input image
        boxes = face_recognition.face_locations(rgb,model="hog")
        # compute the facial embedding for the face
        encodings = face_recognition.face_encodings(rgb, boxes)
        # loop over the encodings
        if len(encodings)>1:
            context = {
            "error_message": "Multiple faces detected.\n Upload your face images only."}
            return render(request, "404.html", context)
            
        for encoding in encodings:
            # add each encoding + name to our set of known names and
            # encodings
            knownEncodings.append(encoding)
        # dump the facial encodings + names to disk
        print("[INFO] serializing encodings...")
    data = {user: knownEncodings}
    print("============")
    
    print("=============")
    print(data)

    
    CLIENT_SECRET_FILE = "credentials.json"
    API_NAME = "drive"
    API_VERSION = "v3"
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

    # print(roomcode)
    # for match in pattern.finditer(roomcode):
    #     idx = match.group(0)
    # print(idx)

    folder_id= "1i6MPCoBnCBhC8FokzTfzqY_M1mEeMQki"

    query = f"parents = '{folder_id}'"

    response = service.files().list(q=query).execute()
    files = response.get('files')
    nextPageToken = response.get('nextPageToken')

    while nextPageToken:
        response = service.files().list(q=query).execute()
        files.extend(response.get('files'))
        nextPageToken = response.get('nextPageToken')

    df = pd.DataFrame(files)
    
    
    image_id_list = df["id"].tolist()
    image_name = df["name"].tolist()

    for i in range(len(image_id_list)):
        
        file_name = image_name[i]

        request = service.files().get_media(fileId=image_id_list[i])
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fd=fh, request=request)
        done = False

        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)

        with open(os.path.join('./static/images/', file_name), 'wb') as f:
            f.write(fh.read())
            f.close()
        my_obj = Drive(user=user,photo=image_name[i])

    print("Booyah")
    
    context = {"photos": photos, "count": count}
    return render(request, "process.html", context)


