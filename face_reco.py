from email import encoders
from email.mime.base import MIMEBase
import time
from datetime import datetime
import ssl
import face_recognition
import cv2
import os
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


class VideoCamera(object):
    def __init__(self):

        self.sender_email = 'sender_email'
        self.receiver_email = 'receiver_email'
        self.password = 'sender_email_password'

        self.message = MIMEMultipart("alternative")
        self.message["Subject"] = "Alert: A New Person Entered the Premises"
        self.message["From"] = self.sender_email
        self.message["To"] = self.receiver_email

        self.timeout = 240  # Sec
        self.last_time = time.time() - self.timeout
        self.known_face_names = []
        self.known_face_encodings = []
        self.images = []
        self.i = 0
        self.source = './known_images'
        for root, dirs, filenames in os.walk(self.source):
            for f in filenames:
                picture = (os.path.splitext(f))[0]
                self.known_face_names.append(picture)
                self.known_face_encodings.append('{}_face_encoding'.format(picture))
                self.images.append('{}_image'.format(picture))

                self.images[self.i] = face_recognition.load_image_file(self.source + "/{}.jpg".format(picture))
                self.known_face_encodings[self.i] = face_recognition.face_encodings(self.images[self.i])[0]

                self.i += 1
        # Initializes some variables

        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.face_detected_array = []
        self.process_this_frame = True

        self.video = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def email(self, img_path, name):

        with open(img_path, 'rb') as f:
            # set attachment mime and file name, the image type is png
            mime = MIMEBase('image', 'png', filename='img1.png')
            # add required header data:
            mime.add_header('Content-Disposition', 'attachment', filename='img1.png')
            mime.add_header('X-Attachment-Id', '0')
            mime.add_header('Content-ID', '<0>')
            # read attachment file content into the MIMEBase object
            mime.set_payload(f.read())
            # encode with base64
            encoders.encode_base64(mime)
            # add MIMEBase object to MIMEMultipart object
            self.message.attach(mime)

        body = MIMEText('''
        <html>
            <body>
                <h1>Alert</h1>
                <h2>{} has entered the Premises</h2>
                <h2>Time: {}</h2>
                <p>
                    <img src="cid:0">
                </p>
            </body>
        </html>'''.format(name, datetime.now()), 'html', 'utf-8')

        self.message.attach(body)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(self.sender_email, self.password)
            server.sendmail(
                self.sender_email, self.receiver_email, self.message.as_string()
            )
        # print(self.message.as_string())

    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, frame = self.video.read()

        if success:

            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Only process every other frame of video to save time
            if self.process_this_frame:
                # Find all the faces and face encodings in the current frame of video
                self.face_locations = face_recognition.face_locations(small_frame)
                self.face_encodings = face_recognition.face_encodings(small_frame, self.face_locations)

                face_names = []
                for face_encoding in self.face_encodings:
                    # See if the face is a match for the known face(s)
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    name = "Unknown"

                    # # If a match was found in known_face_encodings, just use the first one.
                    # if True in matches:
                    #     first_match_index = matches.index(True)
                    #     name = known_face_names[first_match_index]

                    # Or instead, use the known face with the smallest distance to the new face
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
                        if (not (name in self.face_detected_array) or (
                                name in self.face_detected_array and time.time() - self.last_time > self.timeout)):
                            self.last_time = time.time()
                            image_name = name + '_picture.jpg'
                            cv2.imwrite('pictures/{}.jpg'.format(image_name), frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
                            self.email('pictures/{}.jpg'.format(image_name), name)

                    face_names.append(name)
                    if not name in self.face_detected_array and name != 'Unknown':
                        self.face_detected_array.append(name)

            self.process_this_frame = not self.process_this_frame

            # Display the results
            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()
