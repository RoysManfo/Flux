import subprocess
from ...helpers.commands import *
from ...helpers.arguments import Parser



p: subprocess.Popen = None
class Command(CommandInterface):
    
    def init(self):
        self.parser = Parser("ext", description="Allows to use commands from outside flux")
        self.parser.add_argument("command", action="append", help="the command to run")

    def setup(self):
        if "-h" in self.command and self.command.index("-h") == 1:
            super().setup()
        
        elif "--help" in self.command and self.command.index("--help") == 1:
            super().setup()
        
        elif len(self.command) < 2:
            # print an help message
            self.command.append("-h")
            super().setup()

        elif len(self.command[1:]) == 0 :
            self.error(self.errors.parameter_not_specified("command"))
            self.parser.exit_execution = True
            return

        self.command = self.command[1:]

    def run(self):
        global p

        try:
            p = subprocess.Popen(self.command, stdin=self.stdin, stdout=self.stdout, stderr=self.stderr, text=True)
            p.wait()
        except FileNotFoundError:
            self.error("unable to spawn the specified process (not found)")
            self.status = STATUS_ERR

    def close(self):
        if not self.status:
            self.status = p.returncode if p else STATUS_ERR

