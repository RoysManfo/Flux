"""
# `flux observer`

### Copyright notice

This files contains work from Kalle Hallden
https://github.com/KalleHallden/desktop_cleaner

MIT License

Copyright (c) 2019 kalle hallden

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import shutil
from pathlib import Path
import time
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, DirModifiedEvent
from .helpers.extensions import extension_paths
from .helpers.arguments import Parser
from .helpers.commands import CommandInterface


class Command(CommandInterface):

    def init(self) -> None:

        self.parser = Parser(prog="observer",
                             description="Scans the bucket folder and sorts files in a `Files` folder")
        self.parser.add_argument("--path", action="store_true",
                                 help="Reveal the observer path")
        self.parser.add_argument("-bg", dest="background", action="store_true",
                                 help="Execute the observer in background just for this session ")

        self.parser.add_help_message("""Scans the bucket folder and sorts files in a `Files` folder
               
usage: observer [-h] [--path] [-bg]
                                    
options:
-h, --help  show this help message and exit
--path      Reveal the observer path
-bg         Execute the observer in background just for this session
        """)

    def run(self, command: list[str], info: object, from_command_line: bool = True) -> None:
        args = self.parser.parse_args(command[1:])

        if self.parser.parsing_error:
            return

        if args.help:
            self.parser.help()
            return

        if args.background:
            self.background_task(info)

        if args.path:
            self.show_path(info)
            return

        if from_command_line:
            self.sort_files(info)

        else:
            self.sort_files(info, forever=True)

    def show_path(self, info: object) -> bool:
        print(info.user.paths.bucket, "\n")
        return False

    def background_task(self, info: object):
        info.bg_tasks.append(
            Thread(target=self.run, args=([], info, False), name="Observer"))
        info.bg_tasks[-1].start()
        print("Started as background task\n")

    def sort_files(self, info: object, forever: bool = False) -> None:
        watch_path = Path(info.user.paths.bucket)
        destination_root = Path(info.user.paths.bucket_destination)

        try:
            os.makedirs(watch_path)
        except FileExistsError:
            pass

        try:
            os.makedirs(destination_root)
        except FileExistsError:
            pass

        try:
            event_handler = self.EventHandler(
                watch_path=watch_path, destination_root=destination_root)

            observer = Observer()
            observer.schedule(event_handler, f'{watch_path}', recursive=True)

            observer.start()
            event_handler.on_modified(DirModifiedEvent)

            # Check if we decided to run the process as a background task
            if forever:

                try:
                    while True:
                        time.sleep(.1)
                        continue
                except KeyboardInterrupt:
                    observer.stop()
            else:
                time.sleep(1)
                observer.stop()

            # End the process
            observer.join()
            return

        except FileNotFoundError:
            # We deleted one or both directories
            self.sort_files(info, forever)

    class EventHandler(FileSystemEventHandler):
        """    
        When a file is moved in the bucket, the event handler detects it and
        moves it in the appropiate folder
        """

        def __init__(self, watch_path: Path, destination_root: Path) -> None:
            self.watch_path = watch_path.resolve()
            self.destination_root = destination_root.resolve()

        def create_destination_path(path: Path) -> Path:
            """
            Helper function that adds current year/month to destination path. If the path
            doesn't already exist, it is created.
            :param Path path: destination root to append subdirectories based on date
            """
            path.mkdir(parents=True, exist_ok=True)
            return path

        def rename_file(source: Path, destination_path: Path) -> Path:
            """
            Helper function that renames file to reflect new path. If a file of the same
            name already exists in the destination folder, the file name is numbered and
            incremented until the filename is unique (prevents overwriting files).
            :param Path source: source of file to be moved
            :param Path destination_path: path to destination directory
            """
            if Path(destination_path / source.name).exists():
                increment = 0

                while True:
                    increment += 1
                    new_name = destination_path / \
                        f'{source.stem}_{increment}{source.suffix}'

                    if not new_name.exists():
                        return new_name
            else:
                return destination_path / source.name

        def restore_dirs(self) -> None:
            """    
            Will restore the bucket if it has been deleted after opening the app
            """
            try:
                os.makedirs(self.watch_path)
            except:
                pass

            try:
                os.makedirs(self.destination_root)
            except:
                pass

        def on_modified(self, event) -> None:
            self.restore_dirs()

            for child in self.watch_path.iterdir():

                # skips directories and non-specified extensions
                if child.is_file() and child.suffix.lower() in extension_paths:
                    destination_path = self.destination_root / \
                        extension_paths[child.suffix.lower()]
                    destination_path = self.create_destination_path(
                        path=destination_path)
                    destination_path = self.rename_file(
                        source=child, destination_path=destination_path)
                    shutil.move(src=child, dst=destination_path)

                elif child.is_file() and child.suffix.lower() not in extension_paths:
                    destination_path = self.destination_root / \
                        extension_paths["noname"]
                    destination_path = self.create_destination_path(
                        path=destination_path)
                    destination_path = self.rename_file(
                        source=child, destination_path=destination_path)
                    shutil.move(src=child, dst=destination_path)
