from collections import deque
import queue
from escpos.printer import Dummy


class PrinterBuffer(Dummy):
    
    def __init__(self):
        super().__init__()
        self.queue = deque(self._output_list)

    def clear(self):
        while self.queue:
            self.queue.pop()