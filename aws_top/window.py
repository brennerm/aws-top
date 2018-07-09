#!/usr/bin/env python3
import botocore.exceptions
import time

import urwid

import aws_top.aws


class WindowManager:
    ONE_EIGHT = '&#9601;'
    ONE_QUARTER = '&#9602;'
    THREE_EIGHTS = '&#9603;'
    HALF = '&#9604;'
    FIVE_EIGHTS = '&#9605;'
    THREE_QUARTERS = '&#9606;'
    SEVEN_EIGHTS = '&#9607;'
    FULL = '&#9608;'


class StatusWindow(urwid.Widget):
    _sizing = frozenset([urwid.BOX])

    def __init__(self):
        super(StatusWindow, self).__init__()
        self.__time = None
        self.__user = aws_top.aws.get_user()
        self.__region = None

        self.update()

    def update(self):
        self.__time = time.strftime(
            '%b %d %Y %H:%M:%S'
        )
        self.__region = aws_top.aws.get_region()
        self._invalidate()

    def render(self, size, focus=False):
        body = [
            urwid.Text('Logged in as: {}'.format(self.__user)),
            urwid.Text('Region: {}'.format(self.__region), align=urwid.CENTER),
            urwid.Text('Time: {}'.format(self.__time), align=urwid.RIGHT)
        ]

        return urwid.Columns(body).render((size[0],))


class Ec2Window(urwid.Widget):
    _sizing = frozenset([urwid.FLOW])

    def __init__(self):
        self.__instances = []
        self.__error = None
        self.update()

    def update(self):
        try:
            self.__instances = aws_top.aws.Ec2().get_all_instances()
            self.__error = None
        except botocore.exceptions.ClientError as ex:
            self.__error = ex.response
        self._invalidate()

    def rows(self, size, focus=False):
        return 1 + max(len(self.__instances), 1)

    def render(self, size, focus=False):
        if self.__error:
            return urwid.Text(('error', self.__error), align=urwid.CENTER).render(size)

        body = []
        header = [
            urwid.Text('ID'),
            urwid.Text('Name', align=urwid.LEFT),
            urwid.Text('State', align=urwid.LEFT),
            urwid.Text('Type', align=urwid.LEFT),
            urwid.Text('AZ', align=urwid.LEFT)
        ]

        body.append(
            urwid.AttrMap(urwid.Columns(header), 'bold')
        )

        if len(self.__instances) == 0:
            body.append(urwid.Text(('warn', 'No available EC2 instances in this region.'), align=urwid.CENTER))

        for i, instance in enumerate(self.__instances, 1):
            body.append(
                urwid.Columns(
                    [
                        urwid.Text(instance.id),
                        urwid.Text(instance.name or 'N/A'),
                        urwid.Text(instance.state),
                        urwid.Text(instance.instance_type),
                        urwid.Text(instance.az)
                    ]
                )
            )

        return urwid.Pile(body).render(size)


class S3Window(urwid.Widget):
    _sizing = frozenset([urwid.FLOW])

    def __init__(self):
        self.__buckets = []
        self.__error = None
        self.update()

    def update(self):
        try:
            self.__buckets = aws_top.aws.S3().get_all_buckets()
            self.__error = None
        except botocore.exceptions.ClientError as ex:
            self.__error = ex.response
        self._invalidate()

    def rows(self, size, focus=False):
        return 1 + max(len(self.__buckets), 1)

    def render(self, size, focus=False):
        if self.__error:
            return urwid.Text(('error', self.__error), align=urwid.CENTER).render(size)

        body = []

        header = [
            urwid.Text('Name'),
            urwid.Text('Creation Date', align=urwid.LEFT),
        ]

        body.append(
            urwid.AttrMap(urwid.Columns(header), 'bold')
        )

        if len(self.__buckets) == 0:
            body.append(urwid.Text(('warn', 'No available S3 buckets.'), align=urwid.CENTER))

        for i, bucket in enumerate(self.__buckets, 1):
            body.append(
                urwid.Columns(
                    [
                        urwid.Text(bucket.name),
                        urwid.Text(bucket.creation_date.strftime("%Y-%m-%d %H:%M:%S"))
                    ]
                )
            )

        return urwid.Pile(body).render(size)


class LambdaWindow(urwid.Widget):
    _sizing = frozenset([urwid.FLOW])

    def __init__(self):
        self.__functions = []
        self.__error = None
        self.update()

    def update(self):
        try:
            self.__functions = aws_top.aws.Lambda().get_all_functions()
            self.__error = None
        except botocore.exceptions.ClientError as ex:
            self.__error = ex.response
        self._invalidate()

    def rows(self, size, focus=False):
        return 1 + max(len(self.__functions), 1)

    def render(self, size, focus=False):
        if self.__error:
            return urwid.Text(('error', self.__error), align=urwid.CENTER).render(size)

        body = []

        header = [
            urwid.Text('Name'),
            urwid.Text('Runtime', align=urwid.LEFT),
            urwid.Text('Size', align=urwid.LEFT),
            urwid.Text('Memory', align=urwid.LEFT),
            urwid.Text('Timeout', align=urwid.LEFT),
            urwid.Text('Last Modified', align=urwid.LEFT),
        ]

        body.append(
            urwid.AttrMap(urwid.Columns(header), 'bold')
        )

        if len(self.__functions) == 0:
            body.append(urwid.Text(('warn', 'No available Lambda functions in this region.'), align=urwid.CENTER))

        for i, func in enumerate(self.__functions, 1):
            body.append(
                urwid.Columns(
                    [
                        urwid.Text(func.name),
                        urwid.Text(func.runtime),
                        urwid.Text(func.code_size),
                        urwid.Text(func.memory_size),
                        urwid.Text(func.timeout),
                        urwid.Text(func.last_modified)
                    ]
                )
            )

        return urwid.Pile(body).render(size)


class OptionWindow(urwid.Widget):
    _sizing = frozenset([urwid.BOX])
    _selectable = True

    def __init__(self, options=None):
        self.__options = options or []

    def keypress(self, size, key):
        for i in range(len(self.__options)):
            if key == 'f' + str(i + 1):
                self.__options[i].trigger()
                return

        return key

    def render(self, size, focus=False):
        body = []

        for i, option in enumerate(self.__options, start=1):
            body.append(
                urwid.Text(
                    [
                        ('f_key', "F" + str(i)),
                        ('options_bg', option.text)
                    ]
                )
            )

        return urwid.AttrMap(
            urwid.Columns(
                body
            ),
            'options_bg'
        ).render((size[0],))

    def set_options(self, options):
        if len(options) > 12:
            raise ValueError('Number of options exceeds 12')

        self.__options = options
        self._invalidate()


class Option:
    def __init__(self, text, action):
        self.__text = text
        self._action = action

    def __len__(self):
        return len(self.text)

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value):
        self.__text = value

    def trigger(self):
        self._action()


class ToggableOption(Option):
    def __init__(self, texts, action):
        self.__text1 = texts[0]
        self.__text2 = texts[1]
        self.__flag = True

        super(ToggableOption, self).__init__(self.__text1, action)

    @property
    def text(self):
        return self.__text1 if self.__flag else self.__text2

    @text.setter
    def text(self, value):
        return

    def __toggle(self):
        self.__flag = not self.__flag

    def trigger(self):
        self._action()
        self.__toggle()
