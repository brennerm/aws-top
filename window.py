#!/usr/bin/env python3
import botocore.exceptions
import time

import boto3
import curses

import aws
import globals

WHITE_ON_BLACK = 0
WHITE_ON_BLUE = 1
BLUE_ON_BLACK = 2
RED_ON_BLACK = 3
GREEN_ON_BLACK = 4
YELLOW_ON_BLACK = 5
CYAN_ON_BLACK = 6
MAGENTA_ON_BLACK = 7
WHITE_ON_CYAN = 8
MAGENTA_ON_CYAN = 9


class WindowManager:
    __instance = None

    ONE_EIGHT = '&#9601;'
    ONE_QUARTER = '&#9602;'
    THREE_EIGHTS = '&#9603;'
    HALF = '&#9604;'
    FIVE_EIGHTS = '&#9605;'
    THREE_QUARTERS = '&#9606;'
    SEVEN_EIGHTS = '&#9607;'
    FULL = '&#9608;'

    FULL_HEIGHT = -1
    FULL_WIDTH = -2
    BOTTOM = -3
    TOP = -4
    LEFT = -5
    RIGHT = -6

    @staticmethod
    def get_instance():
        if WindowManager.__instance is None:
            WindowManager()
        return WindowManager.__instance

    def __init__(self):
        if WindowManager.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            WindowManager.__instance = self

            self.__main_win = curses.initscr()
            self.__initialize_curses()

            curses.init_pair(WHITE_ON_BLUE, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(BLUE_ON_BLACK, curses.COLOR_BLUE, curses.COLOR_BLACK)
            curses.init_pair(RED_ON_BLACK, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(GREEN_ON_BLACK, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(YELLOW_ON_BLACK, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(CYAN_ON_BLACK, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(MAGENTA_ON_BLACK, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
            curses.init_pair(WHITE_ON_CYAN, curses.COLOR_WHITE, curses.COLOR_CYAN)
            curses.init_pair(MAGENTA_ON_CYAN, curses.COLOR_MAGENTA, curses.COLOR_CYAN)

            self.__windows = []

            self.register_window(
                self.__main_win.getmaxyx()[0] - 1,
                self.__main_win.getmaxyx()[1],
                0,
                0,
                StatusWindow
            )

            self.register_window(
                self.__main_win.getmaxyx()[0] - 2,
                self.__main_win.getmaxyx()[1] - 1,
                1,
                0,
                Ec2Window
            )

            self.register_window(
                1,
                self.__main_win.getmaxyx()[1],
                self.__main_win.getmaxyx()[0] - 1,
                0,
                OptionWindow,
                0,
                [
                    Option(''),
                    Option('Region'),
                    Option('Service'),
                    Option(''),
                    Option(''),
                    Option(''),
                    Option(''),
                    Option(''),
                    Option(''),
                    Option('Exit'),
                    Option(''),
                    Option('')
                ]
            )

            self.resize()

    def __del__(self):
        self.__deinitialize_curses()

    def __initialize_curses(self):
        curses.start_color()
        if curses.can_change_color():
            curses.init_color(0, 0, 0, 0)
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        curses.mousemask(1)
        self.__main_win.nodelay(1)
        self.__main_win.keypad(1)
        self.__main_win.refresh()

    def __deinitialize_curses(self):
        curses.nocbreak()
        self.__main_win.keypad(0)
        curses.echo()
        curses.endwin()

    def register_window(self, height, width, pos_y, pos_x, window_class, z_index=0, *args, **kwargs):
        window = window_class(height, width, pos_y, pos_x, z_index, *args, **kwargs)

        self.__windows.append(window)

    def remove_window(self, window_instance):
        if window_instance in self.__windows:
            self.__windows.remove(window_instance)

        del window_instance

    def resize(self):
        max_height, max_width = self.__main_win.getmaxyx()
        pass

    def get_pressed_key(self):
        return self.__main_win.getch()

    def handle_key(self, key):
        for window in sorted(self.__windows, key=lambda w: w.z_index):
            if window.handle_key(key):
                return

    def update(self):
        for window in sorted(self.__windows, key=lambda w: w.z_index):
            window.update()

        curses.doupdate()


class Window:
    def __init__(self, height, width, pos_y, pos_x, z_index=0):
        self._curses_window = curses.newwin(height, width, pos_y, pos_x)
        self.z_index = z_index

    @staticmethod
    def _shorten_string(string, width):
        return (string[:width - 4] + '...') if len(string) > width else string

    def _center_string(self, string):
        blank_space = self.width
        return string.center(blank_space)

    @property
    def height(self):
        return self._curses_window.getmaxyx()[0]

    @property
    def width(self):
        return self._curses_window.getmaxyx()[1]

    def resize(self, height, width, y, x):
        self._curses_window.resize(height, width)
        self._curses_window.mvwin(y, x)

    def update(self):
        self._curses_window.clear()
        self._update()
        self._render()
        self._curses_window.noutrefresh()

    def handle_key(self, key):
        return False

    def _update(self):
        return

    def _render(self):
        raise NotImplementedError


class StatusWindow(Window):
    def __init__(self, height, width, pos_y, pos_x, z_index):
        super(StatusWindow, self).__init__(height, width, pos_y, pos_x, z_index)

        self.__time = None
        self.__user = boto3.client('sts').get_caller_identity()["Arn"]
        self.__region = None

        self._update()

    def _update(self):
        self.__time = time.strftime(
            '%b %d %Y %H:%M:%S'
        )
        self.__region = boto3._get_default_session().region_name

    def _render(self):
        status_format = 'Logged in as: {user} | Region: {region} | Time: {time}'

        self._curses_window.addstr(0, 0,
                                   status_format.format(
                                       user=self.__user,
                                       region=self.__region,
                                       time=self.__time
                                   ),
                                   curses.A_BOLD)


class RegionSelector(Window):
    def __init__(self, height, width, pos_y, pos_x, z_index=0):
        super(RegionSelector, self).__init__(height, width, pos_y, pos_x, z_index)

        self.__regions = [
            "us-east-1",
            "us-east-2",
            "us-west-1",
            "us-west-2",
            "ca-central-1",
            "eu-west-1",
            "eu-central-1",
            "eu-west-2",
            "eu-west-3",
            "ap-northeast-1",
            "ap-northeast-2",
            "ap-southeast-1",
            "ap-southeast-2",
            "ap-south-1",
            "sa-east-1",
            "us-gov-west-1",
        ]

        self.__select_index = self.__regions.index(
            boto3._get_default_session().region_name
        )

    def handle_key(self, key):
        if key == curses.KEY_UP:
            self.__select_index = max(0, self.__select_index - 1)
        elif key == curses.KEY_DOWN:
            self.__select_index = min(len(self.__regions) - 1, self.__select_index + 1)
        elif key == 10:
            boto3.setup_default_session(region_name=self.__regions[self.__select_index])
            WindowManager.get_instance().remove_window(self)
        else:
            return False
        return True

    def _render(self):
        for i, region in enumerate(self.__regions):
            opts = curses.A_NORMAL

            if self.__select_index == i:
                opts |= curses.A_BOLD

            self._curses_window.addstr(i, 0, region, opts)


class ServiceSelector(Window):
    def __init__(self, height, width, pos_y, pos_x, z_index=0):
        super(ServiceSelector, self).__init__(height, width, pos_y, pos_x, z_index)

        self.__services = [
            "EC2",
            "S3",
        ]

        self.__select_index = 0

    def handle_key(self, key):
        if key == curses.KEY_UP:
            self.__select_index = max(0, self.__select_index - 1)
        elif key == curses.KEY_DOWN:
            self.__select_index = min(len(self.__services) - 1, self.__select_index + 1)
        elif key == 10:
            WindowManager.get_instance().remove_window(self)
        else:
            return False
        return True

    def _render(self):
        for i, region in enumerate(self.__services):
            opts = curses.A_NORMAL

            if self.__select_index == i:
                opts |= curses.A_BOLD

            self._curses_window.addstr(i, 0, region, opts)


class Ec2Window(Window):
    def __init__(self, height, width, pos_y, pos_x, z_index):
        super(Ec2Window, self).__init__(height, width, pos_y, pos_x, z_index)

        self.__instances = []
        self.__error = None

    def _update(self):
        if self.__instances is []:
            try:
                self.__instances = aws.Ec2().get_all_instances()
                self.__error = None
            except botocore.exceptions.ClientError as ex:
                self.__error = ex.response

    def _render(self):
        if self.__error:
            self._curses_window.addstr(
                0,
                0,
                self._center_string(self.__error),
                curses.color_pair(3)
            )
            return

        headers = ['ID', 'Name', 'State', 'Type', 'AZ']

        col_width = int(
            (self.width - max([len(header) for header in headers])) / len(headers)) + 1

        row_format = ("{:<" + str(col_width) + "}") * (len(headers))
        self._curses_window.addstr(0, 0, row_format.format(*headers), curses.A_BOLD)

        if len(self.__instances) == 0:
            self._curses_window.addstr(
                1,
                0,
                self._center_string('No available EC2 instances in this region.'),
                curses.color_pair(5)
            )
            return

        for i, instance in enumerate(self.__instances, 1):
            row = row_format.format(
                instance.id,
                Window._shorten_string(instance.name or 'N/A', 40),
                instance.state,
                instance.instance_type,
                instance.az
            )

            self._curses_window.addstr(i, 0, row)


class S3Window(Window):
    def __init__(self, height, width, pos_y, pos_x, z_index):
        super(S3Window, self).__init__(height, width, pos_y, pos_x, z_index)

        self.__buckets = []
        self.__error = None

    def _update(self):
        if self.__buckets is []:
            self.__buckets = aws.S3().get_all_buckets()

    def _render(self):
        if self.__error:
            self._curses_window.addstr(
                0,
                0,
                self._center_string(self.__error),
                curses.color_pair(3)
            )
            return

        headers = ['ID', 'Name', 'State', 'Type', 'AZ']

        col_width = int(
            (self._curses_window.getmaxyx()[1] - max([len(header) for header in headers])) / len(headers)) + 1

        row_format = ("{:<" + str(col_width) + "}") * (len(headers))
        self._curses_window.addstr(0, 0, row_format.format(*headers), curses.A_BOLD)

        if len(self.__buckets) == 0:
            self._curses_window.addstr(
                1,
                0,
                self._center_string('No available S3 buckets in this region.'),
                curses.color_pair(5)
            )
            return

        for i, bucket in enumerate(self.__buckets, 1):
            row = row_format.format()
            self._curses_window.addstr(i, 0, row)


class OptionWindow(Window):
    def __init__(self, height, width, pos_y, pos_x, z_index=0, options=None):
        super(OptionWindow, self).__init__(height, width, pos_y, pos_x, z_index)

        self.__options = options or []

    def handle_key(self, key):
        if key == curses.KEY_F2:
            WindowManager.get_instance().register_window(20, 40, 10, 20, RegionSelector, 50)
        if key == curses.KEY_F3:
            WindowManager.get_instance().register_window(0, 0, 10, 10, ServiceSelector, 50)
        if key == curses.KEY_F10:
            globals.keep_running = False
            return True
        return False

    def _render(self):
        remaining_width = self._curses_window.getmaxyx()[1] - 1
        remaining_width -= sum(len(option) for option in self.__options)

        remaining_width -= len(self.__options) * 3

        if len(self.__options) > 9:
            remaining_width -= len(self.__options) - 9

        free_space = int(remaining_width / len(self.__options))
        option_texts = [option.text.center(free_space) for option in self.__options]

        offset = 0
        for i, option_text in enumerate(option_texts, start=1):
            try:
                self._curses_window.addstr(0, offset, "F" + str(i), curses.A_BOLD)
                offset += 1 + len(str(i))

                self._curses_window.addstr(0, offset, option_text, curses.color_pair(1))
                offset += 1 + len(option_text) + 1
            except curses.error:
                raise Exception("given width is not sufficient for displaying all options")

    def set_options(self, options):
        if len(options) > 12:
            raise ValueError('Number of options exceeds 12')

        self.__options = options


class Option:
    def __init__(self, text):
        self.__text = text

    def __len__(self):
        return len(self.text)

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value):
        self.__text = value


class ToggableOption(Option):
    def __init__(self, text1, text2):
        super(ToggableOption, self).__init__(text1)
        self.__text1 = text1
        self.__text2 = text2
        self.__flag = True

    @property
    def text(self):
        return self.__text1 if self.__flag else self.__text2

    @text.setter
    def text(self, value):
        return

    def toggle(self):
        self.__flag = not self.__flag
