import operator
from functools import reduce
import asyncio
from binascii import hexlify
from src.api.shtrih.commands import COMMANDS
from src.api.shtrih import logger 

class ShtrihProto:


    ENQ = bytearray((0x05,))
    STX = bytearray((0x02,))
    ACK = bytearray((0x06,))
    NAK = bytearray((0x15,))
    PING = bytearray((0x00,))

    def __init__(self):
        self.buffer = asyncio.Queue()
        self.connection = None 

    async def _write(self, *args):
        raise NotImplementedError

    async def _read(self, *args):
        raise NotImplementedError

    async def reconnect(self):
        pass

   
    def crc_calc(self, payload:bytearray) -> bytearray:
        """crc_calc [summary]

        [extended_summary]

        Args:
            payload (bytearray): [description]

        Returns:
            bytearray: [description]
        """
        return bytearray((reduce(operator.xor, payload),))


    def resp_pack(self, arr:bytearray) -> bytearray:
        output = bytearray()
        output.extend(ShtrihProto.STX)
        output.extend(arr)
        return output
        
    async def write(self, data:bytearray) ->None:
        task_buffer = self.buffer.put(data)
        task_log = logger.info(f'OUTPUT:{hexlify(bytes(data), sep=":")}')
        await asyncio.gather(task_log, task_buffer)
        while True:
            try:
                await self._write(data)
                break
            except Exception as e:
                    task_log = logger.error(e)
                    tasks_reconnect = self.reconnect()
                    await asyncio.gather(task_log, tasks_reconnect)
                    continue

    async def read(self, size:int):
        while True:
            try:
                data = await self._read(size)
                await logger.info(f'INPUT:{data}')
                return data
            except Exception as e:
                task_log = logger.error(e)
                tasks_reconnect = self.reconnect()
                await asyncio.gather(task_log, tasks_reconnect)
                continue

    async def consume(self):
        payload = await self.read(1)
        print(payload)
        if payload == ShtrihProto.ENQ:
            if not self.buffer.empty(): 
                queued = await self.buffer.get() #
                await self.write(queued) 
            else:
                output = ShtrihProto.NAK
                await self.write.write(output) 
        elif payload == ShtrihProto.ACK:
            while not self.buffer.empty(): 
                await self.buffer.get() 
        elif payload == ShtrihProto.STX:
            # read 1 byte for length
            length = await self.read(1) 
            # read bytes: total bytes size = length
            data = await self.read(length[0]) 
            # check if data presented
            if not data:
                # if data not presented in payload 
                await self.write(ShtrihProto.NAK) 
            # if data presented in payload
            else:
                crc = await self.read(1) 
                # check crc
                crc_arr = bytearray()
                crc_arr.extend(length) #type:ignore
                crc_arr.extend(data)
                logger.debug(crc_arr)
                # if crc positive
                if self.crc_calc(crc_arr) == crc[0]:
                    await logger.info('CRC:ACCEPTED')
                    await self._handle(data)
                # if crc negative
                else:
                    await self.write(ShtrihProto.NAK)  #type: ignore
        elif payload == ShtrihProto.NAK:
            await logger.info('INPUT:NAK')
            while not self.buffer.empty(): #type: ignore
                await self.buffer.get() #type: ignore
        else:
            await self.write(ShtrihProto.NAK) 
            await logger.error(f'INPUT:{payload}.Unknown byte controls ')

    async def _handle(self, payload): 
        cmd = payload[0:1]
        if cmd == bytearray((0xFF,)):
            cmd = payload[0:2]
        data = payload[len(cmd):]
        await logger.debug(f'CMD:{cmd} DATA:{data}')
        hdlr = next((c for c in COMMANDS if cmd == c._command_code),None)
        await logger.debug(f'HANDLER:{hdlr}')
        if hdlr:
            response = await hdlr.handle(data)
            response.extend(self.crc_calc(response))
            task_write = self.write(self.resp_pack(response))
            task_dispatch = hdlr.dispatch(data)
            await asyncio.gather(task_write, task_dispatch)
        else:
            await self.write(ShtrihProto.NAK)
            await logger.error(f"{cmd} not implemented in current build version ")
   
           
        


           

   


 


   