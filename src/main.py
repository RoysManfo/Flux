# Flux modules
from core import setup, manager
from settings.info import Info
import utils

# External Dependencies
import sys
import os
from colorama import init, Fore

init(autoreset=True)


# Setup process
INFO: Info = setup.setup()


def listen() -> list[str]:
    """
    This function is used to get the command typed by the user preceded by
    a string of text containing the username, the name of the program,
    the version and the location where Flux is oparating on the disk.
    """
    try:
        print(
            f"{Fore.GREEN}{INFO.user.username}{Fore.CYAN} Flux [{INFO.version}] {Fore.YELLOW}" + str(INFO.user.paths.terminal).lower() + f"{Fore.WHITE}{Fore.MAGENTA} $ ", end="")
        command = input()
        print(f"{Fore.WHITE}", end="")

        return utils.transform.string_to_list(command)

    except KeyboardInterrupt:
        print(f"{Fore.RED}^C{Fore.RESET}")
        return utils.transform.string_to_list("")

    except EOFError:
        print(f"{Fore.RED}^C{Fore.RESET}")
        return utils.transform.string_to_list("")


def run():
    while True:
        os.chdir(INFO.user.paths.terminal)
        try:
            cmd = listen()

        except KeyboardInterrupt:
            print()
            continue

        # Check if we just want to leave, there's no need to check in
        # all of SYSTEM_CMDS if we just want to leave and do it quickly
        if cmd[0] == "exit":
            INFO.exit = True
            sys.exit(0)

        # Check if it's a command the default terminal can handle
        if cmd[0] == "clear":
            os.system("cls || clear")

        elif cmd[0] == "cd":
            if len(cmd) > 1:
                try:
                    new_dir = "" + cmd[1].strip("\"").strip("'")
                    if new_dir.startswith("$"):
                        new_dir = INFO.variables.get(new_dir).value or new_dir
                    os.chdir(f"{new_dir}")
                    INFO.variables.set("$PWD", new_dir)
                
                except FileNotFoundError:
                    # Disply an error message if path specified is iniexistent
                    print("-flux: cd: No such file or directory\n")
                    pass

                except NotADirectoryError:
                    # Disply an error message if path specified is iniexistent
                    print(f"-flux: cd: {new_dir}: Not a directory\n")
                    pass
                
                except OSError:
                    # Disply an error message if path specified is iniexistent
                    print(f"-flux: cd: {new_dir}: cannot read file or directory\n")
                    pass
                INFO.user.paths.terminal = os.getcwd()
                INFO.user.paths.terminal.replace("\\", "/")

            else:
                os.chdir(INFO.variables.get("$HOME").value)
                INFO.user.paths.terminal = INFO.variables.get("$HOME").value
                INFO.variables.set("$PWD", INFO.user.paths.terminal)

        # Pass the command to the manager
        else:
            manager.manage(cmd, INFO)


if __name__ == "__main__":

    try:
        INFO.processes._add_main_process(INFO, ['flux'], run)
    except Exception as e:
        # Catch all the exceptions related to the whole program.
        # Exeptions in single commands will get handled by the command itself.

        # Something REALLY weird is going on if execution reaches here

        sys.stderr.write("Failed do start\n")
        sys.stderr.write("We belive the problem might be on your system\n")
        sys.stderr.write(f"\nError message \n{'-' * 13}\n{type(e).__name__}: {e.__str__()}\n\n")

        log_path = utils.crash_handler.write_error_log()[1]
        sys.stderr.write("The full traceback of this error can be found here: \n" + log_path + "\n")

        sys.exit(1)

    sys.exit(0)
