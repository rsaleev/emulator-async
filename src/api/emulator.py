from src.api.printer.device import *
from src.api.shtrih.device import *
from src.api.webkassa.gateway import *


class Emulator:

    shtrih = ShtrihSerialDevice()
    printer  = PrinterUsbDevice()
    webkassa = WebkassaClient()
    
    @classmethod
    async def serve(cls):
        while True:
            if cls.shtrih.device.in_waiting >0:
                payload = await cls.shtrih.read(cls.shtrih.device.in_waiting) #type: ignore
                if payload == ShtrihProto.ENQ:
                    if cls.shtrih.buffer.empty():
                        await cls.shtrih.write(ShtrihProto.NAK)
                    else:
                        await cls.shtrih.write(ShtrihProto.ACK)
                        queued = await cls.shtrih.buffer.get()
                        response = cls.shtrih.handle(queued)
                        if not response:
                            await cls.shtrih.write(ShtrihProto.NAK)
                        else:
                            await cls.shtrih.write(response)
                elif payload == ShtrihProto.ACK:
                    if not cls.shtrih.buffer.empty():
                        await cls.shtrih.buffer.get()
                elif payload[0:1] == ShtrihProto.STX:
                    length = payload[1:2]
                    cmd = payload[2:3]
                    if cmd == bytearray(0xFF):
                        cmd = payload[2:4]
                    data = payload[len(length)+len(cmd):-1]
                    if cmd == ''
   
