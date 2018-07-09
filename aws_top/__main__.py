import argparse
import collections

import urwid

import aws_top.signals
from aws_top import aws
from aws_top.popup import GenerousPopUpLauncher, RegionSelectorDialog, ServiceSelectorDialog
from aws_top.window import StatusWindow, OptionWindow, Option, Ec2Window, S3Window, LambdaWindow


class AwsTop:
    def __init__(self, access_key=None, secret_key=None, session_token=None, region=None):
        if access_key and secret_key or session_token:
            aws.set_credentials(access_key, secret_key, session_token)

        if region:
            aws.set_region(region)

        services = collections.OrderedDict({
            'EC2': Ec2Window,
            'S3': S3Window,
            'Lambda': LambdaWindow,
            'DynamoDB': None
        })

        def exit_main_loop():
            raise urwid.ExitMainLoop()

        def change_service(w, service):
            self.service_window.original_widget = services[service]()

        popup_anchor = urwid.BoxAdapter(urwid.SolidFill(), 0)
        region_selector = RegionSelectorDialog()
        service_selector = ServiceSelectorDialog(list(services.keys()))
        region_popup_launcher = GenerousPopUpLauncher(popup_anchor, region_selector)
        service_popup_launcher = GenerousPopUpLauncher(popup_anchor, service_selector)

        self.status_window = StatusWindow()
        self.service_window = urwid.Filler(list(services.values())[0](), valign=urwid.TOP)
        self.option_window = OptionWindow(
            [
                Option('Help', lambda: None),
                Option('Region', lambda: region_popup_launcher.open_pop_up()),
                Option('Service', lambda: service_popup_launcher.open_pop_up()),
                Option('Exit', exit_main_loop)
            ]
        )

        urwid.connect_signal(service_selector, aws_top.signals.SERVICE_CHANGE, change_service)

        # Layout:
        # - invisible PopUp launchers
        # - Status
        # - Main
        # - Options
        self.main_win = urwid.Pile(
            [
                ('pack', urwid.Pile([region_popup_launcher, service_popup_launcher])),
                ('pack', urwid.BoxAdapter(self.status_window, 1)),
                self.service_window,
                ('pack', urwid.BoxAdapter(self.option_window, 1))
            ],
            focus_item=3
        )

        palette = [
            ('error', 'dark red', ''),
            ('warn', 'yellow', ''),
            ('f_key', 'bold,white', 'default'),
            ('options_bg', 'bold', 'dark blue'),
            ('bold', 'bold', ''),
            ('popbg', 'white', 'dark blue')
        ]

        self.__loop = urwid.MainLoop(
            self.main_win,
            palette=palette,
            pop_ups=True
        )
        self.__loop.screen.set_terminal_properties(colors=256)

    def update_ui(self, loop, user_data=None):
        self.status_window.update()
        self.service_window.original_widget.update()

        self.__loop.draw_screen()
        self.__loop.set_alarm_in(1, self.update_ui)

    def run(self):
        self.__loop.set_alarm_in(1, self.update_ui)
        self.__loop.run()


def main():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('-a', '--access-key')
    argparser.add_argument('-s', '--secret-key')
    argparser.add_argument('-S', '--session-token')
    argparser.add_argument('-r', '--region')

    args = argparser.parse_args()

    AwsTop(
        args.access_key,
        args.secret_key,
        args.session_token,
        args.region
    ).run()


if __name__ == '__main__':
    main()
