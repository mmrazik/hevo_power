#!/usr/bin/env python3
import http.server
import logging
import socketserver
import signal
import sys
import RPi.GPIO as GPIO

httpd = None
logger = logging.getLogger('hevopower')

PORT = 8001

BUTTON_PIN = 27
SSR_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SSR_PIN, GPIO.OUT)
GPIO.output(SSR_PIN, 0)


def sigint_handler(signal, frame):
    logger.info("Shuting down httpd (CTRL+C)")
    if httpd is not None:
        httpd.server_close()
        GPIO.cleanup()
        sys.exit(0)


def button_callback(channel):
    logger.debug("Button callback")
    state = GPIO.input(SSR_PIN)
    GPIO.output(SSR_PIN, 1 - state)


def init_logging():
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('/var/log/hevopower.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)


class HevoCommandsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/hevo/off':
            logger.info("/hevo/off received; Shutting down")
            GPIO.output(SSR_PIN, 0)
        elif self.path == '/hevo/on':
            logger.info("/hevo/on received; Powering up")
            GPIO.output(SSR_PIN, 1)
        else:
            self.send_response(404)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("OK".encode("utf8"))


if __name__ == '__main__':
    init_logging()
    signal.signal(signal.SIGINT, sigint_handler)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING,
                          callback=button_callback, bouncetime=500)

    httpd = socketserver.TCPServer(('0.0.0.0', PORT), HevoCommandsHandler)
    logger.info("httpd setup complete")
    httpd.serve_forever()
