import logging
import os
from time import sleep
from datetime import datetime, timedelta
import pytz
from astral import Astral
import picamera

def wait(ts_compare):
    '''
    Calculate the delay to the start of the specifict timestamp
    '''
    #ts = ts.replace(tzinfo=None)
    if ts_compare <= datetime.now(ACT_TZ):
        return

    delay = (ts_compare - datetime.now(ACT_TZ)).seconds
    sleep(delay)

try:
    ACT_TZ = pytz.timezone('Europe/Prague')
    TARGET_PATH = "/mnt/remotenfs"
    OUT_PATH = os.path.join(TARGET_PATH, datetime.now(ACT_TZ).strftime('%Y_%m_%d'))

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%d.%m.%y %H:%M:%S',
                        filename=TARGET_PATH + '/' + datetime.now().strftime("%Y%m%d") + '.log')

    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logging.info('Target folder: %s', OUT_PATH)

    if not os.path.isdir(OUT_PATH):
        os.makedirs(OUT_PATH)

    CITY_NAME = 'Prague'

    ASTRAL = Astral()
    ASTRAL.solar_depression = 'civil'

    CITY = ASTRAL[CITY_NAME]

    logging.info('Information for %s/%s', CITY_NAME, CITY.region)
    logging.info('Timezone: %s', CITY.timezone)
    logging.info('Latitude: %.02f; Longitude: %.02f', CITY.latitude, CITY.longitude)

    SUN = CITY.sun(date=datetime.now(), local=True)
    logging.info('Dawn:     %s', str(SUN['dawn']))
    logging.info('Sunrise:  %s', str(SUN['sunrise']))
    logging.info('Noon:     %s', str(SUN['noon']))
    logging.info('Sunset:   %s', str(SUN['sunset']))
    logging.info('Dusk:     %s', str(SUN['dusk']))

    SUN_RISE = SUN['sunrise'].replace(microsecond=0, second=0, minute=0)+timedelta(hours=1)
    SUN_SET = SUN['sunset'].replace(microsecond=0, second=0, minute=0)

    logging.info('waiting to Sunrise ...')
    wait(SUN_RISE)
    logging.info('The sun is shining.')
    logging.info('Camera set up')

except Exception:
    logging.exception("Init")

try:
    with picamera.PiCamera(resolution=(1920, 1080), framerate=30) as camera:
        # Set ISO to the desired value
        camera.iso = 100
        sleep(2)
        camera.shutter_speed = camera.exposure_speed
        camera.exposure_mode = 'off'
        g = camera.awb_gains
        camera.awb_mode = 'off'
        camera.awb_gains = g
        camera.start_preview()
        sleep(2)
        logging.info("Let's go to make picture ...")
        for filename in camera.capture_continuous(os.path.join(OUT_PATH, 'img{counter:04d}.jpg')):
            logging.info('Captured: %s', filename)
            sleep(300) # wait 5 minutes
            if SUN_SET <= datetime.now(ACT_TZ):
                break
except Exception:
    logging.exception("Take a picture")

try:
    logging.info('The dusk is coming ...')
    os.system("ffmpeg -r 10 -i " + OUT_PATH + "/img%04d.jpg -r 10 -vcodec libx264 -crf 20 -g 15 " + OUT_PATH + "/timelapse.mp4")
    logging.info('Finish. Video was created.')
except Exception:
    logging.exception("Make video")
