#!/usr/bin/env python3

import urwid

import aws_top.aws
import aws_top.signals


class RegionSelectorDialog(urwid.WidgetWrap):
    signals = [aws_top.signals.CLOSE]

    def __init__(self):
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

        current_region = aws_top.aws.get_region()

        body = []

        for region in self.__regions:
            button = urwid.Button(region)
            button._label.align = urwid.CENTER
            urwid.connect_signal(button, aws_top.signals.CLICK, self.__set_region, region)

            body.append(urwid.AttrMap(button, None, focus_map='reversed'))

        body = urwid.Pile(body)

        body.focus_position = self.__regions.index(current_region)

        body = urwid.Filler(body, valign=urwid.TOP)
        body = urwid.LineBox(body, title='Select Region')

        super(RegionSelectorDialog, self).__init__(urwid.AttrWrap(body, 'popbg'))

    @property
    def width(self):
        return 6 + max([len(region) for region in self.__regions])

    @property
    def height(self):
        return 2 + len(self.__regions)

    def __set_region(self, button, region):
        aws_top.aws.set_region(region)
        self._emit(aws_top.signals.CLOSE)


class ServiceSelectorDialog(urwid.WidgetWrap):
    signals = [aws_top.signals.CLOSE, aws_top.signals.SERVICE_CHANGE]

    def __init__(self, services):
        self.__services = services

        body = []

        for service in self.__services:
            button = urwid.Button(service)
            button._label.align = urwid.CENTER
            urwid.connect_signal(button, aws_top.signals.CLICK, self.__set_service, service)
            body.append(urwid.AttrMap(button, None, focus_map='reversed'))

        body = urwid.Pile(body)
        body = urwid.Filler(body, valign=urwid.TOP)
        body = urwid.LineBox(body, title='Select Service')

        super(ServiceSelectorDialog, self).__init__(urwid.AttrWrap(body, 'popbg'))

    @property
    def width(self):
        return 6 + max([
            max([len(service) for service in self.__services]),
            len('Select Service')
        ])

    @property
    def height(self):
        return 2 + len(self.__services)

    def __set_service(self, button, service):
        self._emit(aws_top.signals.SERVICE_CHANGE, service)
        self._emit(aws_top.signals.CLOSE)


class GenerousPopUpLauncher(urwid.PopUpLauncher):
    def __init__(self, w, popup):
        super(GenerousPopUpLauncher, self).__init__(w)
        self.__popup = popup

    def create_pop_up(self):
        urwid.connect_signal(
            self.__popup,
            aws_top.signals.CLOSE,
            lambda button: self.close_pop_up()
        )

        return self.__popup

    def get_pop_up_parameters(self):
        size = urwid.raw_display.Screen().get_cols_rows()

        width = self._pop_up_widget.width
        height = self._pop_up_widget.height
        left = size[0] / 2 - width / 2
        top = size[1] / 2 - height / 2

        return {
            'left': left,
            'top': top,
            'overlay_width': width,
            'overlay_height': height
        }
