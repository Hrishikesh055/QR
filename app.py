from flask import Flask, request,send_file
import io
import datetime
import os
import pyqrcode
import png
from pyqrcode import QRCode
from PIL import Image,ImageOps
import requests
import qrcode
import boto3
from botocore.exceptions import NoCredentialsError
from flask_expects_json import expects_json
# ...
app = Flask(__name__)
validation = {
    "type": "object",
    "properties": {
        "url":{"type":"string"},
        "logo_url":{ "type": "string" },
        "front_color":{"type":"string","pattern": "(?:#|0x)(?:[a-f0-9]{3}|[a-f0-9]{6})\b|(?:rgb|hsl)a?\([^\)]*\)"},
        "back_color":{"type":"string","pattern": "(?:#|0x)(?:[a-f0-9]{3}|[a-f0-9]{6})\b|(?:rgb|hsl)a?\([^\)]*\)"},
        "border_thickness":{"type":"number"},
        "border_color":{"type":"string","pattern": "(?:#|0x)(?:[a-f0-9]{3}|[a-f0-9]{6})\b|(?:rgb|hsl)a?\([^\)]*\)"}
    },
    "required": ["url"]
}
def upload_to_aws(image, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_ID'),
                      aws_secret_access_key=os.getenv('AWS_ACCESS_KEY'))

    try:
        img = io.BytesIO()
        image.save(img, 'PNG')
        img.seek(0)
        s3.upload_fileobj(img,os.getenv("AWS_BUCKET_NAME"), s3_file)
        print("Upload Successful")
        link = 'https://testi.exponentialhost.com/' + s3_file
        return link
        # return 'https:i.exponentialhost.com/textInImage/image.png'
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False
def QR(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
        )
    qr.add_data(url)
    qr.make(fit=True)
    return qr

def QR_color(qr,front_color,back_color):
     qr_img = qr.make_image(fill_color=front_color, back_color=back_color)
     return qr_img
def QR_logo(qr_img,logo_url):
    logo_path = logo_url
    print(logo_path)
        # logo = Image.open(logo_path)
    logo = Image.open(requests.get(logo_path, stream=True).raw)

    # taking base width and adjusting image size
    basewidth = 50
    wpercent = (basewidth / float(logo.size[0]))
    hsize = int((float(logo.size[1]) * float(wpercent)))
    logo = logo.resize((basewidth, hsize), Image.ANTIALIAS)
    pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
    qr_img.paste(logo, pos)
    return qr_img
def QR_frame(img,border_thickness,border_color):
    img_with_border = ImageOps.expand(img,border=border_thickness,fill=border_color)
    return img_with_border

@app.route('/qrcode', methods=['POST'])
@expects_json(validation, ignore_for=['GET'])
def process_json():
    try:
        content_type = request.headers.get('Content-Type')
        if (content_type == 'application/json'):
            json = request.json
            url=json['url']
            front_color=back_color=logo_url=border_thickness=border_color=logo_url=None
            if 'front_color' not in json:
                front_color="rgb(0,0,0)"
            else:
                front_color=json['front_color']
            
            if 'back_color' not in json:
                back_color="rgb(255,255,255)"
            else:
                back_color=json['back_color']
            if 'border_thickness' not in json:
                border_thickness= 2
            else:
                border_thickness=json['border_thickness']
            if 'border_color' not in json:
                border_color="rgb(0,0,0)"
            else:    
                border_color=json['border_color']
            if 'logo_url' not in json:
                logo_url=None
            else:         
                logo_url=json['logo_url']
            qr= QR(url)
            qr_img= QR_color(qr,front_color,back_color)
            img_with_border=QR_frame(qr_img,border_thickness,border_color)
            image=img_with_border
            if logo_url:
                image=QR_logo(img_with_border,logo_url)
              
            presentDate = datetime.datetime.now()
            unix_timestamp = datetime.datetime.timestamp(presentDate)*1000  
            link=upload_to_aws(image,'qrcode/' + str(int(unix_timestamp)) + '.png')
            return{
                'url':link
                }
            #return send_file(img, mimetype='image/png')
        else:
            return 'Content-Type not supported!'
    except Exception as e:
        print
        return {"message":"something went wrong"}    
if __name__ == "__main__":
    app.run(debug=True)
