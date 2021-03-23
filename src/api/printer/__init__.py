from src.utils.logger import SynchronousLogger, AsynchronousLogger



sync_logger = SynchronousLogger("printer.log", name='synced_printer_logger')
async_logger = AsynchronousLogger("printer.log", name='async_printer_logger')
