import time

from window import WindowManager

import globals

RENDER_INTERVAL = 1
UPDATE_INTERVAL = 1


class AwsEc2Top:
    keep_running = True

    def __init__(self, region='eu-central-1'):
        self.__region = region
        self.__wm = WindowManager()

    def run(self):
        last_render_ts = time.time()
        force_render = True

        while True:
            key = self.__wm.get_pressed_key()
            if key != -1:
                self.__wm.handle_key(key)
                force_render = True  # force rendering after key stroke

            if not globals.keep_running:
                break

            if force_render or (time.time() - last_render_ts) > RENDER_INTERVAL:
                self.__wm.update()

                last_render_ts = time.time()
                force_render = False


def main():
    AwsEc2Top().run()


if __name__ == '__main__':
    main()
