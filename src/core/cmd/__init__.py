"""
Always import this module as `cr`, this will help to bring a certain
consistency in how this module is referenced across all files and reduce
the possible confusion generated from the otherwise overriding of the 
python built-in `cmd` module.

Example:
```py
>>>  from . import cmd as cr    # correct
>>>  from . import cmd          # not correct
>>>  from . import cmd as cm    # not correct

```
"""

__all__ = ['observer', 'cr', 'set', 'joke']

from . import cr
from . import observer
from . import set
from . import joke

